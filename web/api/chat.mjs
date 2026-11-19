import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { answerQuery } from '../lib/query.mjs';

const dataPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../data/records.json');
let recordsPromise;
const hourlyUse = new Map();
const limit = 10; // Por instancia; no sustituye un límite distribuido en producción.

function provider() {
  if (process.env.GEMINI_API_KEY) return 'gemini';
  if (process.env.OPENAI_API_KEY) return 'openai';
  return null;
}

function clientId(req) {
  return (req.headers?.['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown').split(',')[0].trim();
}

function allowLocalLlm(req) {
  const id = clientId(req);
  const now = Date.now();
  const entry = hourlyUse.get(id);
  const current = entry && now - entry.since < 3_600_000 ? entry : { since: now, count: 0 };
  if (current.count >= limit) return false;
  current.count += 1;
  hourlyUse.set(id, current);
  return true;
}

async function allowLlm(req) {
  const endpoint = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!endpoint && !token) return { allowed: allowLocalLlm(req), note: 'Límite de IA de esta instancia; se usaron reglas.' };
  if (!endpoint || !token) return { allowed: false, note: 'Cuota compartida incompleta; se usaron reglas.' };
  const hour = Math.floor(Date.now() / 3_600_000);
  const visitor = createHash('sha256').update(clientId(req)).digest('hex').slice(0, 24);
  const script = `local total=tonumber(redis.call('GET',KEYS[1]) or '0')
local own=tonumber(redis.call('GET',KEYS[2]) or '0')
if total>=tonumber(ARGV[1]) or own>=tonumber(ARGV[2]) then return 0 end
total=redis.call('INCR',KEYS[1])
own=redis.call('INCR',KEYS[2])
if total==1 then redis.call('EXPIRE',KEYS[1],7200) end
if own==1 then redis.call('EXPIRE',KEYS[2],7200) end
return 1`;
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(['EVAL', script, '2', `portability:llm:global:${hour}`, `portability:llm:visitor:${hour}:${visitor}`, '30', '10']),
      signal: AbortSignal.timeout(3000)
    });
    if (!response.ok) throw new Error(`Redis HTTP ${response.status}`);
    const data = await response.json();
    if (data.error) throw new Error('Redis rechazó la cuota');
    return { allowed: Number(data.result) === 1, note: 'Cuota compartida de IA agotada; se usaron reglas.' };
  } catch {
    return { allowed: false, note: 'Cuota compartida no disponible; se usaron reglas.' };
  }
}

async function interpretWithLlm(question, records, selected) {
  const values = Object.fromEntries(['status', 'team', 'channel', 'month'].map((key) => [key, [...new Set(records.map((row) => row[key]))]]));
  const instruction = `Convertí la pregunta en un JSON puro con esta forma exacta: {"metric":"count|sla|average_resolution","groupBy":null|"status"|"team"|"channel"|"month","filters":{"status":...,"team":...,"channel":...,"month":...,"state":"open|closed"}}. Omití filtros no solicitados. Para "qué equipo/canal tiene más" agrupá por esa dimensión; para un equipo/canal específico filtrá. Usá solo valores literales de este catálogo: ${JSON.stringify(values)}. No inventes filtros ni años. Respondé solo JSON.`;
  if (selected === 'gemini') {
    const model = process.env.GEMINI_MODEL || 'gemini-2.5-flash-lite';
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-goog-api-key': process.env.GEMINI_API_KEY },
      body: JSON.stringify({ contents: [{ parts: [{ text: `${instruction}\nPregunta: ${question}` }] }], generationConfig: { responseMimeType: 'application/json', maxOutputTokens: 350 } }),
      signal: AbortSignal.timeout(8000)
    });
    if (!response.ok) throw new Error(`Gemini HTTP ${response.status}`);
    const body = await response.json();
    return JSON.parse(body.candidates?.[0]?.content?.parts?.map((part) => part.text || '').join('') || '');
  }
  const response = await fetch('https://api.openai.com/v1/responses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
    body: JSON.stringify({ model: process.env.OPENAI_MODEL || 'gpt-4.1-mini', max_output_tokens: 350, input: [
      { role: 'system', content: instruction },
      { role: 'user', content: question }
    ] }),
    signal: AbortSignal.timeout(8000)
  });
  if (!response.ok) throw new Error(`OpenAI HTTP ${response.status}`);
  const body = await response.json();
  const text = body.output?.flatMap((item) => item.content || []).filter((item) => item.type === 'output_text').map((item) => item.text).join('');
  return JSON.parse(text || '');
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Usá POST.' });
  const question = typeof req.body?.question === 'string' ? req.body.question.trim() : '';
  if (!question || question.length > 300) return res.status(400).json({ error: 'La pregunta debe tener entre 1 y 300 caracteres.' });
  const records = await (recordsPromise ||= readFile(dataPath, 'utf8').then(JSON.parse).catch(error => { recordsPromise = null; throw error; }));
  const deterministic = answerQuery(question, records);
  const selected = provider();
  if (req.body?.mode !== 'llm' || !selected || deterministic.spec?.metric === 'backlog' || ['unsupported', 'ambiguous', 'missing_date', 'out_of_range'].includes(deterministic.reason)) return res.status(200).json({ ...deterministic, source: 'dataset', llmAvailable: Boolean(selected) });
  const quota = await allowLlm(req);
  if (!quota.allowed) return res.status(200).json({ ...deterministic, source: 'dataset', llmAvailable: true, note: quota.note });
  try {
    const spec = await interpretWithLlm(question, records, selected);
    const verified = answerQuery(question, records, spec);
    return res.status(200).json({ ...verified, source: `interpreted:${selected}`, llmAvailable: true });
  } catch {
    return res.status(200).json({ ...deterministic, source: 'dataset', llmAvailable: true, note: 'No fue posible interpretar con el modelo; se usaron reglas.' });
  }
}
