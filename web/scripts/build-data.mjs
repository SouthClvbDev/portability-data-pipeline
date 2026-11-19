import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { parse } from 'csv-parse/sync';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const web = path.join(root, 'web');
const files = ['portability_cases.csv', 'portability_cases_incremental.csv'];
const rows = [];
for (const file of files) {
  const csv = await readFile(path.join(root, 'data/sample', file), 'utf8');
  rows.push(...parse(csv.replace(/^\uFEFF/, ''), { columns: true, skip_empty_lines: true }));
}

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
console.log(`Resumen generado: ${summary.total} casos (${summary.period.start} a ${summary.period.end})`);
