import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('el análisis publicado muestra episodios y totales calculados desde la serie', async () => {
  const data = JSON.parse(await readFile(new URL('../public/data/full-scale-analysis.json', import.meta.url), 'utf8'));
  const complete = data.monthly.filter(month => month.complete);
  assert.equal(data.total, data.monthly.reduce((sum, month) => sum + month.cases, 0));
  assert.equal(data.total, data.daily.reduce((sum, day) => sum + day.cases, 0));
  assert.deepEqual(data.insights.lowestSla, complete.reduce((lowest, month) => month.slaRate < lowest.slaRate ? month : lowest));
  assert.deepEqual(data.insights.highestSla, complete.reduce((highest, month) => month.slaRate > highest.slaRate ? month : highest));
  assert.ok(data.insights.highestSla.slaRate - data.insights.lowestSla.slaRate > 40);
});
