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
