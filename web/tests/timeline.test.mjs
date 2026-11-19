import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { access, readFile } from 'node:fs/promises';

test('cada etapa del recorrido enlaza evidencia presente en el repositorio', async () => {
  const stages = JSON.parse(await readFile(new URL('../public/data/timeline.json', import.meta.url)));
  assert.ok(stages.length >= 5);
  for (const stage of stages) {
    assert.ok(stage.title && stage.question && stage.result);
    assert.match(stage.evidence, /^(src|sql|web)\//);
    await access(new URL(`../../${stage.evidence}`, import.meta.url));
  }
});
