const datePart = (value) => value?.slice(0, 10);
const day = 86_400_000;
export const validDate = date => /^\d{4}-\d{2}-\d{2}$/.test(date) && !Number.isNaN(Date.parse(`${date}T00:00:00Z`)) && new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) === date;

export function buildHistory(rows) {
  if (!rows.length) throw new Error('No hay casos para construir el historial');
  const changes = new Map();
  const add = (date, field) => {
    const entry = changes.get(date) || { received: 0, closed: 0 };
    entry[field]++;
    changes.set(date, entry);
  };
  let first = '9999-12-31';
  let last = '0000-01-01';
  for (const row of rows) {
    const received = datePart(row.received_at);
    const closed = datePart(row.closed_at);
    if (!validDate(received) || (closed && (!validDate(closed) || closed < received))) throw new Error(`Fechas inválidas en ${row.case_id}`);
    if (['Aprobado', 'Rechazado', 'Anulado'].includes(row.status) !== Boolean(closed)) throw new Error(`Cierre inconsistente en ${row.case_id}`);
    add(received, 'received');
    if (closed) add(closed, 'closed');
    if (received < first) first = received;
    if ((closed || received) > last) last = closed || received;
  }
  const series = [];
  let open = 0;
  for (let time = Date.parse(`${first}T00:00:00Z`), end = Date.parse(`${last}T00:00:00Z`); time <= end; time += day) {
    const date = new Date(time).toISOString().slice(0, 10);
    const { received = 0, closed = 0 } = changes.get(date) || {};
    open += received - closed;
    if (open < 0) throw new Error(`Backlog negativo en ${date}`);
    series.push({ date, received, closed, open });
  }
  return { definition: 'Casos recibidos hasta el cierre del día menos casos cerrados hasta ese mismo día; sin reaperturas.', series };
}

export function backlogAtDate(date, records) {
  if (!validDate(date)) throw new Error('Fecha de corte inválida');
  return records.filter(row => row.receivedAt?.slice(0, 10) <= date && (!row.closedAt || row.closedAt.slice(0, 10) > date)).length;
}
