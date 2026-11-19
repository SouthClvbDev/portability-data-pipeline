import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { parse } from 'csv-parse/sync';
import { buildScenarios } from '../lib/scenarios.mjs';
import { buildHistory } from '../lib/history.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const web = path.join(root, 'web');
const files = ['portability_cases.csv', 'portability_cases_incremental.csv', 'portability_cases_daily.csv'];
const rows = [];
let dailyRows = [];
for (const file of files) {
  const csv = await readFile(path.join(root, 'data/sample', file), 'utf8');
  const parsed = parse(csv.replace(/^\uFEFF/, ''), { columns: true, skip_empty_lines: true });
  if (file === 'portability_cases_daily.csv') dailyRows = parsed;
  rows.push(...parsed);
}
const daily = JSON.parse(await readFile(path.join(root, 'data/sample/portability_cases_daily.meta.json'), 'utf8'));
if (daily.records !== dailyRows.length || dailyRows.some(row => row.received_at.replace(' ', 'T') > daily.asOf || (row.closed_at && row.closed_at.replace(' ', 'T') > daily.asOf))) throw new Error('El lote diario no coincide con su fecha de corte');

const countBy = (field) => Object.fromEntries(
  [...new Set(rows.map((row) => row[field]))].sort().map((value) => [value, rows.filter((row) => row[field] === value).length])
);
const closed = new Set(['Aprobado', 'Rechazado', 'Anulado']);
const resolved = rows.filter((row) => closed.has(row.status));
const byMonth = {};
for (const row of rows) {
  const month = row.received_at.slice(0, 7);
  byMonth[month] = (byMonth[month] || 0) + 1;
}
const summary = {
  source: 'Datos sintéticos versionados en data/sample',
  generatedAt: new Date().toISOString(),
  dailyAsOf: daily.asOf,
  total: rows.length,
  open: rows.length - resolved.length,
  closed: resolved.length,
  withinSla: resolved.filter((row) => Number(row.resolution_hours) <= 48).length,
  outsideSla: resolved.filter((row) => Number(row.resolution_hours) > 48).length,
  period: { start: rows.map((row) => row.received_at).sort()[0].slice(0, 10), end: rows.map((row) => row.received_at).sort().at(-1).slice(0, 10) },
  byStatus: countBy('status'),
  byChannel: countBy('channel'),
  byTeam: countBy('team'),
  byMonth
};
summary.slaRate = Number((summary.withinSla / summary.closed * 100).toFixed(1));
await mkdir(path.join(web, 'public/data'), { recursive: true });
await writeFile(path.join(web, 'public/data/summary.json'), JSON.stringify(summary, null, 2) + '\n');
const history = buildHistory(rows);
if (history.series.at(-1).open !== summary.open) throw new Error('El backlog final no coincide con la instantánea');
await writeFile(path.join(web, 'public/data/history.json'), JSON.stringify(history) + '\n');
const records = rows.map((row) => ({
  status: row.status,
  channel: row.channel,
  team: row.team,
  month: row.received_at.slice(0, 7),
  resolutionHours: row.resolution_hours === '' ? null : Number(row.resolution_hours),
  receivedAt: row.received_at,
  closedAt: row.closed_at || null
}));
await mkdir(path.join(web, 'data'), { recursive: true });
await writeFile(path.join(web, 'data/records.json'), JSON.stringify(records) + '\n');
await writeFile(path.join(web, 'public/data/scenarios.json'), JSON.stringify(buildScenarios(records), null, 2) + '\n');
console.log(`Resumen generado: ${summary.total} casos (${summary.period.start} a ${summary.period.end})`);
