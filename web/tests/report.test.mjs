import assert from 'node:assert/strict';
import { access, readFile } from 'node:fs/promises';
import test from 'node:test';

test('la galería declara las tres páginas y solo enlaza capturas publicadas', async () => {
  const manifest = new URL('../public/data/report.json', import.meta.url);
  const pages = JSON.parse(await readFile(manifest, 'utf8'));
  assert.deepEqual(pages.map(page => page.id), ['resumen-operativo', 'analisis-demoras', 'evolucion-mensual']);
  for (const page of pages) {
    assert.ok(page.title && page.purpose);
    if (page.image) {
      assert.equal(page.image, `/report/${page.id}.png`);
      await access(new URL(`../public${page.image}`, import.meta.url));
    } else assert.equal(page.image, null);
  }
});
