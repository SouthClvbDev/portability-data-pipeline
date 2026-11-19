import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import handler from '../api/chat.mjs';

const invoke = async (question, mode = 'dataset') => {
  let result;
  const response = { status(code) { this.code = code; return this; }, json(body) { result = { code: this.code, ...body }; return this; } };
  await handler({ method: 'POST', body: { question, mode }, headers: { 'x-forwarded-for': '192.0.2.25' } }, response);
  return result;
};

test('la función responde un cruce calculado del dataset', async () => {
  const result = await invoke('¿Qué equipo tuvo más rechazos en mayo?');
  assert.equal(result.code, 200);
  assert.equal(result.result.cases, 92);
  assert.match(result.answer, /Backoffice Norte: 31/);
});

test('la IA solo interpreta filtros; el servidor calcula el resultado', async () => {
  const originalFetch = globalThis.fetch;
  const originalKey = process.env.GEMINI_API_KEY;
  process.env.GEMINI_API_KEY = 'test-only';
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ candidates: [{ content: { parts: [{ text: JSON.stringify({ metric: 'count', groupBy: 'team', filters: { status: 'Rechazado', month: '2023-05' } }) }] } }] }) });
  try {
    const result = await invoke('¿Qué equipo tuvo más rechazos en mayo?', 'llm');
    assert.equal(result.source, 'interpreted:gemini');
    assert.equal(result.result.cases, 92);
    assert.match(result.answer, /Backoffice Norte: 31/);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalKey === undefined) delete process.env.GEMINI_API_KEY;
    else process.env.GEMINI_API_KEY = originalKey;
  }
});

test('la cuota compartida bloquea llamadas al modelo y conserva la respuesta determinista', async () => {
  const previous = {
    fetch: globalThis.fetch,
    gemini: process.env.GEMINI_API_KEY,
    url: process.env.UPSTASH_REDIS_REST_URL,
    token: process.env.UPSTASH_REDIS_REST_TOKEN
  };
  const requests = [];
  process.env.GEMINI_API_KEY = 'test-only';
  process.env.UPSTASH_REDIS_REST_URL = 'https://quota.example.test';
  process.env.UPSTASH_REDIS_REST_TOKEN = 'test-only';
  globalThis.fetch = async (url, options) => {
    requests.push({ url, options });
    return { ok: true, json: async () => ({ result: 0 }) };
  };
  try {
    const result = await invoke('¿Cuántos casos hay?', 'llm');
    assert.equal(result.source, 'dataset');
    assert.match(result.note, /Cuota compartida/);
    assert.equal(requests.length, 1);
    const command = JSON.parse(requests[0].options.body);
    assert.equal(command[0], 'EVAL');
    assert.equal(command[2], '2');
    assert.match(command[3], /global/);
    assert.match(command[4], /visitor/);
    requests.length = 0;
    globalThis.fetch = async (url, options) => {
      requests.push({ url, options });
      if (url === 'https://quota.example.test') return { ok: true, json: async () => ({ result: 1 }) };
      return { ok: true, json: async () => ({ candidates: [{ content: { parts: [{ text: JSON.stringify({ metric: 'count', groupBy: null, filters: {} }) }] } }] }) };
    };
    const allowed = await invoke('¿Cuántos casos hay?', 'llm');
    assert.equal(allowed.source, 'interpreted:gemini');
    assert.equal(allowed.result.cases, 7500);
    assert.equal(requests.length, 2);
  } finally {
    globalThis.fetch = previous.fetch;
    for (const [key, name] of [['gemini', 'GEMINI_API_KEY'], ['url', 'UPSTASH_REDIS_REST_URL'], ['token', 'UPSTASH_REDIS_REST_TOKEN']]) {
      if (previous[key] === undefined) delete process.env[name]; else process.env[name] = previous[key];
    }
  }
});
