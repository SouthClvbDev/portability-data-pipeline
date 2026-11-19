import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { readFile } from 'node:fs/promises';
import { answerQuery } from '../lib/query.mjs';

test('cada escenario publicado corresponde a un cálculo del mismo dataset', async () => {
  const records = JSON.parse(await readFile(new URL('../data/records.json', import.meta.url), 'utf8'));
  const scenarios = JSON.parse(await readFile(new URL('../public/data/scenarios.json', import.meta.url), 'utf8'));
  assert.equal(scenarios.length, 4);
  for (const scenario of scenarios) {
    const expected = answerQuery(scenario.question, records);
    assert.deepEqual(scenario.spec, expected.spec);
    assert.equal(scenario.total, expected.result.cases);
    assert.deepEqual(scenario.groups, expected.result.groups);
  }
  const rejections = scenarios.find((item) => item.id === 'rejections');
  assert.equal(rejections.spec.filters.status, 'Rechazado');
  assert.equal(rejections.spec.filters.month, '2023-05');
});
