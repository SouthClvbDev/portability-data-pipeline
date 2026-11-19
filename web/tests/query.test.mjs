import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { answerQuery, interpret } from '../lib/query.mjs';

const records = [
  { status: 'Rechazado', team: 'Backoffice Norte', channel: 'Web', month: '2023-05', resolutionHours: 72 },
  { status: 'Rechazado', team: 'Backoffice Norte', channel: 'App', month: '2023-05', resolutionHours: 24 },
  { status: 'Aprobado', team: 'Backoffice Sur', channel: 'Web', month: '2023-05', resolutionHours: 30 },
  { status: 'Rechazado', team: 'Backoffice Sur', channel: 'App', month: '2023-04', resolutionHours: 10 },
  { status: 'Recibido', team: 'Backoffice Sur', channel: 'Web', month: '2023-05', resolutionHours: null }
];

test('cruza estado, mes y equipo sin mezclar otros casos', () => {
  const response = answerQuery('¿Qué equipo tuvo más rechazos en mayo?', records);
  assert.equal(response.spec.filters.status, 'Rechazado');
  assert.equal(response.spec.filters.month, '2023-05');
  assert.deepEqual(response.result.groups.map((item) => [item.name, item.cases]), [['Backoffice Norte', 2]]);
});

test('SLA por canal excluye los abiertos', () => {
  const response = answerQuery('SLA por canal en mayo', records);
  assert.equal(response.result.cases, 4);
  assert.equal(response.result.resolved, 3);
  assert.equal(response.result.groups.find((item) => item.name === 'Web').rate, 50);
});

test('calcula promedio del equipo filtrado', () => {
  const response = answerQuery('Tiempo promedio de resolución del equipo Norte', records);
  assert.equal(response.spec.filters.team, 'Backoffice Norte');
  assert.equal(response.result.hours, 48);
});

test('rechaza filtro inventado del modelo', () => {
  assert.throws(() => answerQuery('casos', records, { metric: 'count', groupBy: null, filters: { team: 'Inventado' } }), /Filtro inválido/);
});

test('no explica causas ausentes y solicita fecha para backlog', () => {
  assert.equal(interpret('casos de mayo', records).filters.month, '2023-05');
  assert.equal(answerQuery('¿Por qué se rechazan?', records).spec, null);
  assert.equal(answerQuery('backlog histórico', records).spec, null);
  assert.equal(answerQuery('¿Qué clima hace?', records).reason, 'unrecognized');
});
