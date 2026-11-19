const months = { enero: '01', febrero: '02', marzo: '03', abril: '04', mayo: '05', junio: '06', julio: '07', agosto: '08', septiembre: '09', setiembre: '09', octubre: '10', noviembre: '11', diciembre: '12' };
const final = new Set(['Aprobado', 'Rechazado', 'Anulado']);
const format = (n) => new Intl.NumberFormat('es-AR').format(n);
const normalized = (s) => String(s).toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
import { backlogAtDate, validDate } from './history.mjs';

export function interpret(question, records) {
  const q = normalized(question);
  const spec = { metric: 'count', groupBy: null, filters: {} };
  if (/backlog|abiert|pendient/.test(q) && /\b20\d{2}-\d{2}-\d{2}\b/.test(q)) {
    spec.metric = 'backlog';
    spec.asOf = q.match(/\b20\d{2}-\d{2}-\d{2}\b/)[0];
  } else if (/sla|cumplimiento/.test(q)) spec.metric = 'sla';
  else if (/promedio|media|tiempo medio/.test(q) && /resolucion|horas|demora/.test(q)) spec.metric = 'average_resolution';
  const month = Object.entries(months).find(([name]) => new RegExp(`\\b${name}\\b`).test(q));
  const numericMonth = q.match(/\b(20\d{2})[-/](0?[1-9]|1[0-2])\b/);
  if (spec.metric !== 'backlog' && numericMonth) spec.filters.month = `${numericMonth[1]}-${numericMonth[2].padStart(2, '0')}`;
  else if (spec.metric !== 'backlog' && month) {
    const matches = [...new Set(records.map((row) => row.month).filter((value) => value.endsWith(`-${month[1]}`)))];
    if (matches.length === 1) spec.filters.month = matches[0];
    if (matches.length > 1) spec.ambiguousMonth = true;
  }
  const statuses = [...new Set(records.map((row) => row.status))];
  const synonyms = { Aprobado: /aprobado|aprobaciones/, Rechazado: /rechazado|rechazos/, Anulado: /anulado|anulaciones/ };
  const status = statuses.find((value) => (synonyms[value]?.test(q) || q.includes(normalized(value))));
  if (status) spec.filters.status = status;
  else if (spec.metric !== 'backlog' && /abierto|abiertos|pendiente|pendientes/.test(q) && !/historico|historia|fecha pasada/.test(q)) spec.filters.state = 'open';
  else if (spec.metric !== 'backlog' && /cerrado|cerrados|resuelto|resueltos/.test(q)) spec.filters.state = 'closed';
  const teams = [...new Set(records.map((row) => row.team))];
  const channels = [...new Set(records.map((row) => row.channel))];
  const team = teams.find((value) => q.includes(normalized(value)) || (/(equipo|backoffice)/.test(q) && q.includes(normalized(value).replace('backoffice ', ''))));
  const channel = channels.find((value) => q.includes(normalized(value)));
  if (team) spec.filters.team = team;
  if (channel) spec.filters.channel = channel;
  if (/(por|cada|cual|que)\s+(equipo|backoffice)|equipos/.test(q) && !team) spec.groupBy = 'team';
  else if (/(por|cada|cual|que)\s+canal|canales/.test(q) && !channel) spec.groupBy = 'channel';
  else if (/por\s+(mes|estado)|evolucion|tendencia|estados/.test(q)) spec.groupBy = /estado/.test(q) ? 'status' : 'month';
  return spec;
}

export function validateSpec(candidate, records) {
  if (!candidate || typeof candidate !== 'object') throw new Error('Consulta inválida');
  if (!['count', 'sla', 'average_resolution', 'backlog'].includes(candidate.metric)) throw new Error('Métrica inválida');
  if (candidate.groupBy !== null && !['status', 'team', 'channel', 'month'].includes(candidate.groupBy)) throw new Error('Agrupación inválida');
  const { metric, groupBy } = candidate;
  if (metric === 'backlog') {
    if (groupBy && !['team', 'channel'].includes(groupBy)) throw new Error('El backlog solo admite agrupación por equipo o canal');
    const dates = records.flatMap(row => [row.receivedAt, row.closedAt].filter(Boolean).map(value => value.slice(0, 10))).sort();
    if (!dates.length || !validDate(candidate.asOf) || candidate.asOf < dates[0] || candidate.asOf > dates.at(-1)) throw new Error('Fecha fuera del período observado');
  }
  const filters = {};
  for (const key of ['status', 'team', 'channel', 'month']) {
    const values = new Set(records.map((row) => row[key]));
    if (candidate.filters?.[key]) {
      if (!values.has(candidate.filters[key]) && !(key === 'month' && /^20\d{2}-(0[1-9]|1[0-2])$/.test(candidate.filters[key]))) throw new Error('Filtro inválido');
      filters[key] = candidate.filters[key];
    }
  }
  if (candidate.filters?.state) {
    if (!['open', 'closed'].includes(candidate.filters.state)) throw new Error('Estado inválido');
    filters.state = candidate.filters.state;
  }
  if (metric === 'backlog' && (filters.month || filters.status || filters.state)) throw new Error('El backlog solo admite filtros por equipo o canal');
  return { metric, groupBy, filters, ...(metric === 'backlog' ? { asOf: candidate.asOf } : {}) };
}

export function calculate(spec, records) {
  const rows = records.filter((row) => Object.entries(spec.filters).every(([key, value]) => key === 'state' ? (value === 'closed' ? final.has(row.status) : !final.has(row.status)) : row[key] === value));
  const metric = (part) => {
    if (spec.metric === 'backlog') return { cases: backlogAtDate(spec.asOf, part) };
    if (spec.metric === 'sla') {
      const resolved = part.filter((row) => final.has(row.status));
      const within = resolved.filter((row) => row.resolutionHours !== null && row.resolutionHours <= 48).length;
      return { cases: part.length, resolved: resolved.length, within, outside: resolved.length - within, rate: resolved.length ? Number((within / resolved.length * 100).toFixed(1)) : null };
    }
    if (spec.metric === 'average_resolution') {
      const hours = part.map((row) => row.resolutionHours).filter((n) => n !== null && Number.isFinite(n));
      return { cases: part.length, resolved: hours.length, hours: hours.length ? Number((hours.reduce((a, b) => a + b, 0) / hours.length).toFixed(1)) : null };
    }
    return { cases: part.length };
  };
  const partitions = new Map();
  if (spec.groupBy) for (const row of rows) partitions.set(row[spec.groupBy], [...(partitions.get(row[spec.groupBy]) || []), row]);
  const groups = spec.groupBy ? [...partitions].map(([name, part]) => ({ name, ...metric(part) })).sort((a, b) => spec.groupBy === 'month' ? a.name.localeCompare(b.name) : spec.metric === 'sla' ? (b.rate ?? -1) - (a.rate ?? -1) : b.cases - a.cases) : null;
  return { ...metric(rows), groups };
}

export function explain(spec, result) {
  const scope = Object.entries(spec.filters).map(([key, value]) => key === 'month' ? `en ${value}` : key === 'state' ? (value === 'open' ? 'abiertos' : 'cerrados') : `con ${key === 'status' ? 'estado' : key === 'team' ? 'equipo' : 'canal'} ${value}`).join(', ');
  const prefix = scope ? `Para casos ${scope}: ` : 'En la muestra sintética: ';
  if (spec.metric === 'backlog') {
    const detail = spec.groupBy ? ` Desglose por ${spec.groupBy === 'team' ? 'equipo' : 'canal'}: ${result.groups.map(group => `${group.name}: ${format(group.cases)}`).join('; ')}.` : '';
    return `${prefix}${format(result.cases)} casos abiertos al cierre del ${spec.asOf}.${detail} Se calcula con fechas de recepción y cierre; no describe los estados intermedios ni reaperturas.`;
  }
  if (spec.groupBy) {
    if (!result.groups?.length) return `${prefix}no hay casos para ese cruce.`;
    const label = result.groups.map((g) => spec.metric === 'sla' ? `${g.name}: ${g.rate === null ? 'sin casos resueltos' : `${g.rate.toLocaleString('es-AR')} % (${format(g.within)}/${format(g.resolved)})`}` : spec.metric === 'average_resolution' ? `${g.name}: ${g.hours === null ? 'sin casos resueltos' : `${g.hours.toLocaleString('es-AR')} h`}` : `${g.name}: ${format(g.cases)}`).join('; ');
    const dimension = { team: 'equipo', channel: 'canal', status: 'estado', month: 'mes' }[spec.groupBy];
    return `${prefix}${spec.metric === 'sla' ? 'cumplimiento de SLA' : spec.metric === 'average_resolution' ? 'resolución promedio' : 'casos'} por ${dimension}: ${label}.`;
  }
  if (spec.metric === 'sla') return `${prefix}${result.resolved ? `${format(result.within)} de ${format(result.resolved)} casos resueltos dentro del SLA sintético de 48 horas (${result.rate.toLocaleString('es-AR')} %).` : 'no hay casos resueltos para calcular SLA.'} Los casos abiertos no entran en el denominador.`;
  if (spec.metric === 'average_resolution') return `${prefix}${result.hours === null ? 'no hay casos resueltos con horas de resolución.' : `tiempo promedio de resolución de ${result.hours.toLocaleString('es-AR')} horas entre ${format(result.resolved)} casos resueltos.`}`;
  return `${prefix}${format(result.cases)} ${result.cases === 1 ? 'caso' : 'casos'}.`;
}

export function answerQuery(question, records, override = null) {
  if (/backlog|abiertos? al cierre/.test(normalized(question)) && !/\b20\d{2}-\d{2}-\d{2}\b/.test(question)) return { answer: 'Indicá una fecha de corte completa, por ejemplo: backlog al 2023-05-31. Puedo calcular casos abiertos al cierre del día con recepciones y cierres; no conozco los estados intermedios.', spec: null, result: null, reason: 'missing_date' };
  if (/por que|causa|motivo|mediana|cliente|numero de linea/.test(normalized(question))) return { answer: 'Esta versión no contiene datos suficientes para responder esa pregunta. Puedo calcular conteos, SLA y promedio de resolución con filtros por mes, estado, canal y equipo.', spec: null, result: null, reason: 'unsupported' };
  if (!override && !/total|cuant|cantidad|volumen|casos|tramites|estado|abiert|pendient|cerrad|resuelt|rechaz|aprob|anulad|sla|cumplimiento|equipo|backoffice|canal|mes|mensual|evolucion|tendencia|promedio|resolucion|horas|backlog/.test(normalized(question))) return { answer: 'No identifiqué una métrica. Preguntame por casos, SLA, resolución promedio o backlog a una fecha.', spec: null, result: null, reason: 'unrecognized' };
  const local = interpret(question, records);
  if (!override && local.ambiguousMonth) return { answer: 'Ese mes aparece en más de un año. Indicá el año, por ejemplo 2023-05.', spec: null, result: null, reason: 'ambiguous' };
  if (!override && local.metric === 'backlog') {
    if (local.groupBy && !['team', 'channel'].includes(local.groupBy)) return { answer: 'Puedo desglosar el backlog por equipo o canal, pero no reconstruir estados intermedios.', spec: null, result: null, reason: 'unsupported' };
    const dates = records.flatMap(row => [row.receivedAt, row.closedAt].filter(Boolean).map(value => value.slice(0, 10))).sort();
    if (!dates.length || !validDate(local.asOf) || local.asOf < dates[0] || local.asOf > dates.at(-1)) return { answer: `La fecha está fuera del período observado${dates.length ? ` (${dates[0]} a ${dates.at(-1)})` : ''}.`, spec: null, result: null, reason: 'out_of_range' };
  }
  const spec = validateSpec(override || local, records);
  const result = calculate(spec, records);
  return { answer: explain(spec, result), spec, result };
}
