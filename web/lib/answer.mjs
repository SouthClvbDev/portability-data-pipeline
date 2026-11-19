const format = (value) => new Intl.NumberFormat('es-AR').format(value);
const best = (counts) => Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
const label = (entries) => entries.map(([name, count]) => `${name}: ${format(count)}`).join('; ');

export function answer(question, data) {
  const q = question.toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  if (/duplicad/.test(q)) return 'Los CSV de muestra contienen IDs únicos. La base también protege case_id con una clave primaria.';
  if (/sla|cumplimiento/.test(q)) return `De ${format(data.closed)} casos cerrados, ${format(data.withinSla)} están dentro del SLA sintético de 48 horas y ${format(data.outsideSla)} fuera. Cumplimiento: ${data.slaRate.toLocaleString('es-AR')} %. Los casos abiertos no entran en ese denominador.`;
  if (/abiert|pendient|backlog/.test(q)) return `Hay ${format(data.open)} casos abiertos en la instantánea sintética. No se puede calcular backlog histórico exacto porque el dataset no registra transiciones de estado.`;
  if (/cerrad|resuelt/.test(q)) return `Hay ${format(data.closed)} casos cerrados en la muestra; los estados finales son Aprobado, Rechazado y Anulado.`;
  if (/estado|rechaz|aprob|anulad/.test(q)) return `Distribución por estado: ${label(Object.entries(data.byStatus))}.`;
  if (/canal/.test(q)) { const [name, count] = best(data.byChannel); return `El canal con más casos es ${name} (${format(count)}). Desglose: ${label(Object.entries(data.byChannel))}.`; }
  if (/equipo|team/.test(q)) { const [name, count] = best(data.byTeam); return `El equipo con más casos es ${name} (${format(count)}). Desglose: ${label(Object.entries(data.byTeam))}.`; }
  if (/mes|mensual|evolucion|tendencia/.test(q)) return `Casos recibidos por mes: ${label(Object.entries(data.byMonth))}. Son volúmenes por fecha de recepción, no cierres ocurridos en cada mes.`;
  if (/periodo|fecha|cuando/.test(q)) return `La muestra sintética abarca recepciones del ${data.period.start} al ${data.period.end}.`;
  if (/total|cuantos|cantidad|volumen|casos/.test(q)) return `El dataset sintético contiene ${format(data.total)} trámites: ${format(data.open)} abiertos y ${format(data.closed)} cerrados.`;
  return 'Puedo responder sobre total, estados, abiertos, SLA, canal, equipo y evolución mensual de la muestra. Para otras preguntas hace falta definir la métrica y los datos necesarios.';
}
