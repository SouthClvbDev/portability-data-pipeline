const number = (value) => new Intl.NumberFormat('es-AR').format(value);
const $ = (selector) => document.querySelector(selector);

async function loadData() {
  try {
    const response = await fetch('/data/summary.json');
    if (!response.ok) throw new Error('No se pudo cargar el resumen');
    const data = await response.json();
    $('#total').textContent = number(data.total);
    $('#open').textContent = number(data.open);
    $('#closed').textContent = number(data.closed);
    $('#sla').textContent = `${data.slaRate.toLocaleString('es-AR')} %`;
    $('#period').textContent = `Fuente: muestra liviana sintética · Recepciones del ${data.period.start} al ${data.period.end} · Mes del corte parcial · Lote diario actualizado hasta ${data.dailyAsOf.replace('T', ' ')} (Argentina) · SLA sintético de 48 horas corridas.`;
    const months = Object.entries(data.byMonth).sort(([a], [b]) => a.localeCompare(b)).slice(-12);
    const maxMonth = Math.max(...months.map(([, value]) => value));
    for (const [month, value] of months) {
      const item = document.createElement('div'); item.className = 'bar-item';
      item.style.setProperty('--bar-height', `${Math.max(value / maxMonth * 145, 2)}px`);
      const count = document.createElement('strong'); count.textContent = number(value);
      const bar = document.createElement('i');
      const name = document.createElement('span'); name.textContent = month.slice(2) + (month === data.period.end.slice(0, 7) ? '*' : '');
      item.append(count, bar, name); $('#monthly').append(item);
    }
    $('#monthly').setAttribute('aria-label', `Casos recibidos en los últimos 12 meses; el último mes es parcial: ${months.map(([month, value]) => `${month}: ${value}`).join(', ')}`);
    const statuses = Object.entries(data.byStatus).sort((a, b) => b[1] - a[1]);
    for (const [status, value] of statuses) {
      const row = document.createElement('div'); row.className = 'status-row';
      const label = document.createElement('span'); label.textContent = status;
      const track = document.createElement('span'); track.className = 'track';
      const fill = document.createElement('span'); fill.className = 'fill'; fill.style.width = `${value / data.total * 100}%`;
      const count = document.createElement('strong'); count.textContent = number(value);
      track.append(fill); row.append(label, track, count); $('#statuses').append(row);
    }
  } catch { $('#period').textContent = 'No fue posible cargar los indicadores. Revisá la construcción del sitio.'; }
}

function message(text, role) {
  const node = document.createElement('div'); node.className = `message ${role}`; node.textContent = text;
  $('#messages').append(node); $('#messages').scrollTop = $('#messages').scrollHeight;
  return node;
}

function element(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function showScenario(scenario, button) {
  document.querySelectorAll('.scenario-tabs button').forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
  const card = $('#scenario-card'); card.replaceChildren();
  const copy = element('div', 'scenario-copy');
  copy.append(element('p', 'eyebrow', `ESCENARIO · ${scenario.id.toUpperCase()}`), element('h3', '', scenario.title), element('p', 'scenario-context', scenario.context));
  const stages = element('ol', 'scenario-stages');
  const filterText = Object.entries(scenario.spec.filters).map(([key, value]) => `${key}: ${value}`).join(' · ') || 'Muestra completa';
  for (const [title, detail] of [
    ['01 · Datos', `${number(scenario.total)} casos en el alcance`],
    ['02 · Filtros', filterText],
    ['03 · Métrica', scenario.spec.metric === 'sla' ? 'Dentro de SLA / casos resueltos' : 'Cantidad de casos'],
    ['04 · Resultado', `${scenario.groups.length} grupos comparables`]
  ]) {
    const item = element('li'); item.append(element('strong', '', title), element('span', '', detail)); stages.append(item);
  }
  copy.append(stages, element('p', 'scenario-caveat', scenario.interpretation));
  const askButton = element('button', 'scenario-ask', 'Preguntar al asistente ↗');
  askButton.type = 'button'; askButton.addEventListener('click', () => { $('#question').value = scenario.question; $('#asistente').scrollIntoView({ behavior: 'smooth' }); $('#question').focus({ preventScroll: true }); });
  copy.append(askButton);
  const visual = element('div', 'scenario-visual');
  visual.append(element('p', 'eyebrow', `PREGUNTA · ${scenario.question}`));
  const bars = element('div', 'scenario-bars');
  const peak = Math.max(...scenario.groups.map((item) => scenario.spec.metric === 'sla' ? item.rate || 0 : item.cases), 1);
  for (const group of scenario.groups) {
    const row = element('div', 'scenario-bar');
    const name = element('span', 'scenario-bar-name', group.name);
    const track = element('div', 'scenario-bar-track');
    const fill = element('div', 'scenario-bar-fill');
    fill.style.width = `${Math.max(2, (scenario.spec.metric === 'sla' ? group.rate || 0 : group.cases) / peak * 100)}%`;
    track.append(fill);
    const amount = scenario.spec.metric === 'sla' ? (group.rate === null ? 'Sin resueltos' : `${group.rate.toLocaleString('es-AR')} % (${number(group.within)}/${number(group.resolved)})`) : number(group.cases);
    row.append(name, track, element('strong', 'scenario-bar-value', amount)); bars.append(row);
  }
  visual.append(bars, element('small', 'scenario-source', 'Fuente: muestra liviana sintética · Cálculo generado al desplegar'));
  card.append(copy, visual);
}

async function loadScenarios() {
  try {
    const response = await fetch('/data/scenarios.json');
    if (!response.ok) throw new Error('No se pudieron cargar escenarios');
    const scenarios = await response.json();
    for (const scenario of scenarios) {
      const button = element('button', '', scenario.title); button.type = 'button'; button.setAttribute('aria-pressed', 'false');
      button.addEventListener('click', () => showScenario(scenario, button)); $('#scenario-tabs').append(button);
    }
    if (scenarios.length) showScenario(scenarios[0], $('#scenario-tabs button'));
  } catch { $('#scenario-card').textContent = 'No se pudieron cargar los escenarios. Revisá la construcción del sitio.'; }
}

async function loadReport() {
  const grid = $('#report-grid');
  try {
    const response = await fetch('/data/report.json');
    if (!response.ok) throw new Error('No se pudo cargar el informe');
    const pages = await response.json();
    grid.replaceChildren();
    for (const [index, page] of pages.entries()) {
      const card = element('article', 'report-card');
      const visual = element('div', 'report-visual');
      if (page.image) {
        const link = element('a'); link.href = page.image; link.target = '_blank'; link.rel = 'noopener noreferrer';
        const image = element('img'); image.src = page.image; image.alt = `Captura real del informe Power BI: ${page.title}`; image.loading = 'lazy';
        link.append(image); visual.append(link);
      } else visual.append(element('span', 'report-pending', 'Captura pendiente'));
      card.append(visual, element('span', 'report-page', `PÁGINA ${String(index + 1).padStart(2, '0')}`), element('h3', '', page.title), element('p', '', page.purpose));
      grid.append(card);
    }
  } catch { grid.textContent = 'No se pudo cargar la galería del informe. Revisá la construcción del sitio.'; }
}

async function loadHistory() {
  try {
    const response = await fetch('/data/history.json');
    if (!response.ok) throw new Error('No se pudo cargar el historial');
    const { series } = await response.json();
    if (!series.length) throw new Error('Historial vacío');
    const chart = $('#history-chart');
    const svg = (tag, attributes) => {
      const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
      for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
      return node;
    };
    const slider = $('#history-day');
    const range = $('#history-range');
    const ask = $('#history-ask');
    let visible = [];
    const draw = () => {
      visible = series.slice(-Math.min(series.length, range.value === 'all' ? series.length : Number(range.value)));
      const values = visible.map(day => day.open);
      const minimum = Math.min(...values);
      const maximum = Math.max(...values);
      const lower = Math.max(0, Math.floor(minimum * 0.9));
      const upper = Math.max(lower + 1, Math.ceil(maximum * 1.08));
      const point = (index) => ({ x: 42 + index / Math.max(visible.length - 1, 1) * 743, y: 155 - (visible[index].open - lower) / (upper - lower) * 125 });
      chart.replaceChildren();
      for (const [value, y] of [[upper, 30], [lower, 155]]) {
        chart.append(svg('line', { x1: 42, y1: y, x2: 785, y2: y, stroke: '#dbe7e5' }));
        const label = svg('text', { x: 36, y: y + 4, 'text-anchor': 'end', fill: '#61737b', 'font-size': 10 });
        label.textContent = number(value); chart.append(label);
      }
      chart.append(svg('polyline', { points: visible.map((_, index) => { const { x, y } = point(index); return `${x},${y}`; }).join(' '), fill: 'none', stroke: '#0c9b87', 'stroke-width': 2.5, 'stroke-linejoin': 'round' }));
      const marker = svg('circle', { r: 6, fill: '#102a36', stroke: '#fff', 'stroke-width': 2 }); chart.append(marker);
      slider.max = String(visible.length - 1); slider.value = slider.max; slider.disabled = false; ask.disabled = false;
      const select = () => {
        const entry = visible[Number(slider.value)];
        const { x, y } = point(Number(slider.value)); marker.setAttribute('cx', x); marker.setAttribute('cy', y);
        $('#history-open').textContent = number(entry.open);
        $('#history-date').textContent = `al cierre del ${entry.date}`;
        $('#history-detail').textContent = `Ese día ingresaron ${number(entry.received)} casos y cerraron ${number(entry.closed)}. Escala visible: ${number(lower)} a ${number(upper)} abiertos.`;
        chart.setAttribute('aria-label', `Casos abiertos diarios del ${visible[0].date} al ${visible.at(-1).date}, escala ${lower} a ${upper}; fecha seleccionada ${entry.date}: ${entry.open} abiertos.`);
      };
      slider.oninput = select; select();
    };
    range.addEventListener('change', draw); draw();
    ask.addEventListener('click', () => { $('#question').value = `¿Cuál era el backlog al ${visible[Number(slider.value)].date}?`; $('#asistente').scrollIntoView({ behavior: 'smooth' }); $('#question').focus({ preventScroll: true }); });
  } catch { $('#history-detail').textContent = 'No se pudo cargar la evolución diaria. Revisá la construcción del sitio.'; }
}

async function loadTimeline() {
  const card = $('#timeline-card');
  try {
    const response = await fetch('/data/timeline.json');
    if (!response.ok) throw new Error('No se pudo cargar el recorrido');
    const stages = await response.json();
    const tabs = $('#timeline-tabs'); const play = $('#timeline-play');
    let current = 0; let timer = null;
    const buttons = stages.map((stage, index) => {
      const button = element('button', '', String(index + 1).padStart(2, '0'));
      button.type = 'button'; button.title = stage.title; button.setAttribute('aria-label', `Etapa ${index + 1}: ${stage.title}`);
      button.addEventListener('click', () => { stop(); show(index); }); tabs.append(button); return button;
    });
    const show = (index) => {
      current = index; buttons.forEach((button, position) => button.setAttribute('aria-pressed', String(position === index)));
      const stage = stages[index]; card.replaceChildren();
      const copy = element('div');
      copy.append(element('p', 'eyebrow', `ETAPA ${String(index + 1).padStart(2, '0')} / ${String(stages.length).padStart(2, '0')}`), element('h3', '', stage.title), element('p', 'timeline-question', stage.question), element('p', 'timeline-result', stage.result));
      const link = element('a', 'text-link', `Ver evidencia: ${stage.evidence} ↗`);
      link.href = `https://github.com/SouthClvbDev/portability-data-pipeline/blob/main/${stage.evidence}`;
      link.target = '_blank'; link.rel = 'noopener noreferrer'; copy.append(link);
      card.append(copy, element('span', 'timeline-count', String(index + 1).padStart(2, '0')));
    };
    const stop = () => { if (timer) clearInterval(timer); timer = null; play.textContent = 'Reproducir recorrido ▶'; };
    play.addEventListener('click', () => {
      if (timer) { stop(); return; }
      show(0); play.textContent = 'Pausar recorrido Ⅱ';
      timer = setInterval(() => { if (current === stages.length - 1) stop(); else show(current + 1); }, 4000);
    });
    if (stages.length) show(0);
  } catch { card.textContent = 'No se pudo cargar el recorrido del proyecto.'; }
}

async function ask(question) {
  message(question, 'user'); const pending = message('Consultando el resumen…', 'bot');
  try {
    const requestedLlm = $('#llm').checked;
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, mode: $('#llm').checked ? 'llm' : 'dataset' }) });
    const data = await response.json();
    pending.textContent = data.answer || data.error || 'No pude responder esta vez.';
    if (data.note) pending.textContent += ` ${data.note}`;
    const state = $('#llm-state');
    state.className = '';
    if (data.source?.startsWith('interpreted:')) {
      state.textContent = data.source === 'interpreted:gemini' ? 'Gemini activo' : 'IA activa';
      state.classList.add('llm-active');
    } else if (data.llmAvailable === false) {
      state.textContent = 'IA sin configurar';
      state.classList.add('llm-unavailable');
    } else if (requestedLlm && data.llmAvailable) {
      state.textContent = 'IA configurada · respuesta con reglas';
      state.classList.add('llm-fallback');
    } else if (data.llmAvailable) state.textContent = 'IA configurada';
  } catch {
    pending.textContent = 'No se pudo conectar con el asistente. Revisá el despliegue de la función.';
    $('#llm-state').textContent = 'No se pudo verificar la IA';
  }
}

$('#chat-form').addEventListener('submit', (event) => { event.preventDefault(); const input = $('#question'); const question = input.value.trim(); if (question) { input.value = ''; ask(question); } });
document.querySelectorAll('[data-question]').forEach((button) => button.addEventListener('click', () => { $('#question').value = button.dataset.question; $('#question').focus(); }));
document.querySelectorAll('.mobile-menu a').forEach(link => link.addEventListener('click', () => { link.closest('details').open = false; }));
loadData();
fetch('/data/full-scale-analysis.json').then(response => response.json()).then(data => {
  $('#python-cutoff').textContent = `${number(data.total)} trámites del 2023-01-01 al ${data.asOf.replace('T', ' ')} (Argentina)`;
  const peak = data.insights.highestVolume;
  const slowest = data.insights.lowestSla;
  $('#decision-volume').textContent = number(peak.cases);
  $('#decision-volume-month').textContent = peak.month;
  $('#decision-volume-sla').textContent = `${peak.slaRate.toLocaleString('es-AR')} %`;
  $('#decision-low-sla').textContent = `${slowest.slaRate.toLocaleString('es-AR')} %`;
  $('#decision-low-month').textContent = slowest.month;
  $('#decision-low-volume').textContent = number(slowest.cases);
  $('#decision-cutoff').textContent = `Datos sintéticos de escala completa · ${number(data.total)} trámites · Corte ${data.asOf.replace('T', ' ')} (Argentina)`;
  if (peak.month === slowest.month) {
    $('#decision-symbol').textContent = '=';
    $('#decision-reading-title').textContent = 'El pico de demanda coincide con el peor SLA.';
    $('#decision-reading-text').textContent = 'La coincidencia no demuestra una causa. En una operación real, revisaría capacidad, tiempos por equipo y canal, y la evolución de pendientes antes de asignar recursos.';
  }
  const cards = [
    ['Mayor demora', data.insights.lowestSla, `${data.insights.lowestSla.slaRate.toLocaleString('es-AR')} % dentro de SLA`, data.insights.lowestSla.episode],
    ['Mejor cumplimiento', data.insights.highestSla, `${data.insights.highestSla.slaRate.toLocaleString('es-AR')} % dentro de SLA`, data.insights.highestSla.episode],
    ['Mayor volumen', data.insights.highestVolume, `${number(data.insights.highestVolume.cases)} trámites`, data.insights.highestVolume.category.replace('_', ' ')]
  ];
  for (const [title, month, value, detail] of cards) {
    const card = element('article');
    card.append(element('span', '', title), element('strong', '', value), element('small', '', `${month.month} · ${detail}`));
    $('#python-insights').append(card);
  }
}).catch(() => { $('#python-cutoff').textContent = 'Fecha de corte no disponible'; $('#decision-cutoff').textContent = 'No se pudo cargar el caso de decisión'; });
loadScenarios();
loadReport();
loadHistory();
loadTimeline();
