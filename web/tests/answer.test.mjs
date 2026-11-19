import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { answer } from '../lib/answer.mjs';

const data = { total: 7500, open: 3676, closed: 3824, withinSla: 2927, outsideSla: 897, slaRate: 76.5, byStatus: { Aprobado: 2464 }, byChannel: { Web: 3, App: 2 }, byTeam: { Norte: 4, Sur: 1 }, byMonth: { '2023-01': 100 }, period: { start: '2023-01-01', end: '2023-06-30' } };
test('SLA excluye abiertos del denominador', () => assert.match(answer('¿Cuál es el SLA?', data), /3\.824 casos cerrados/));
test('backlog histórico reconoce el límite', () => assert.match(answer('¿Backlog histórico?', data), /no se puede calcular backlog histórico/i));
test('canal usa los conteos reales', () => assert.match(answer('Canal principal', data), /Web \(3\)/));
