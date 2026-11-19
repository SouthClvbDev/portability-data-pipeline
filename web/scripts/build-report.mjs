import { copyFile, mkdir, readFile, rm, writeFile } from 'node:fs/promises';

const pages = [
  { id: 'resumen-operativo', title: 'Resumen Operativo', purpose: 'Volumen, estado y cumplimiento de SLA para situar la operación.' },
  { id: 'analisis-demoras', title: 'Análisis de demoras', purpose: 'Tiempos de resolución y motivos de rechazo o anulación para detectar dónde investigar.' },
  { id: 'evolucion-mensual', title: 'Evolución Mensual', purpose: 'Recepciones y resultados por mes para comparar períodos con el contexto correcto.' }
];

const root = new URL('../', import.meta.url);
const output = new URL('public/report/', root);
await mkdir(output, { recursive: true });
await mkdir(new URL('public/data/', root), { recursive: true });

for (const page of pages) {
  const source = new URL(`evidence/${page.id}.png`, root);
  const destination = new URL(`${page.id}.png`, output);
  await rm(destination, { force: true });
  let bytes;
  try { bytes = await readFile(source); }
  catch (error) {
    if (error.code !== 'ENOENT') throw error;
    page.image = null;
    continue;
  }
  const signature = Buffer.from('89504e470d0a1a0a', 'hex');
  if (bytes.length < 24 || !bytes.subarray(0, 8).equals(signature)) throw new Error(`${source.pathname}: se requiere un PNG válido`);
  const width = bytes.readUInt32BE(16);
  const height = bytes.readUInt32BE(20);
  if (width < 1200 || height < 675) throw new Error(`${source.pathname}: resolución mínima 1200 × 675`);
  await copyFile(source, destination);
  page.image = `/report/${page.id}.png`;
}

await writeFile(new URL('public/data/report.json', root), `${JSON.stringify(pages, null, 2)}\n`);
console.log(`Galería Power BI: ${pages.filter(page => page.image).length}/${pages.length} capturas disponibles`);
