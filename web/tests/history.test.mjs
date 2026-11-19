import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { readFile } from 'node:fs/promises';
import { buildHistory, backlogAtDate } from '../lib/history.mjs';
import { answerQuery } from '../lib/query.mjs';

test('el historial diario conserva ingresos, cierres y backlog final', async () => {
  const history = JSON.parse(await readFile(new URL('../public/data/history.json', import.meta.url)));
  const summary = JSON.parse(await readFile(new URL('../public/data/summary.json', import.meta.url)));
  const daily = JSON.parse(await readFile(new URL('../../data/sample/portability_cases_daily.meta.json', import.meta.url)));
  assert.equal(summary.dailyAsOf, daily.asOf);
  assert.equal(summary.total, 7500 + daily.records);
  assert.equal(history.series.reduce((sum, entry) => sum + entry.received, 0), summary.total);
  assert.equal(history.series.reduce((sum, entry) => sum + entry.closed, 0), summary.closed);
  assert.equal(history.series.at(-1).open, summary.open);
  assert.ok(history.series.every(entry => entry.open >= 0));
  const recent = history.series.slice(-365).map(entry => entry.open);
  assert.ok(Math.max(...recent) - Math.min(...recent) >= 20, 'el último año debe mostrar variación de backlog');
  assert.ok(summary.open < 100, 'la cohorte de 2023 ya no debe inflar el backlog actual');
});

test('el asistente calcula la fecha de corte con las mismas fechas', async () => {
  const records = JSON.parse(await readFile(new URL('../data/records.json', import.meta.url)));
  const answer = answerQuery('¿Cuál era el backlog al 2023-05-31?', records);
  assert.equal(answer.spec.metric, 'backlog');
  assert.equal(backlogAtDate('2023-05-31', records), answer.result.cases);
  assert.equal(answerQuery('¿Cuántos casos estaban abiertos al 2023-05-31?', records).result.cases, answer.result.cases);
  const byTeam = answerQuery('backlog al 2023-05-31 por equipo', records);
  assert.equal(byTeam.result.groups.reduce((sum, group) => sum + group.cases, 0), answer.result.cases);
  assert.equal(answerQuery('backlog al 2030-01-01', records).reason, 'out_of_range');
  assert.equal(answerQuery('backlog histórico', records).reason, 'missing_date');
});

test('no inventa etapas intermedias y rechaza fechas de cierre incoherentes', () => {
  const rows = [
    { case_id: 'A', received_at: '2023-01-01 10:00:00', closed_at: '2023-01-02 08:00:00', status: 'Aprobado' },
    { case_id: 'B', received_at: '2023-01-02 09:00:00', closed_at: '', status: 'Pendiente contacto' }
  ];
  assert.deepEqual(buildHistory(rows).series.map(entry => entry.open), [1, 1]);
  assert.throws(() => buildHistory([{ ...rows[0], closed_at: '2022-12-31 09:00:00' }]), /Fechas inválidas/);
  assert.throws(() => backlogAtDate('2023-02-31', []), /Fecha de corte inválida/);
});
