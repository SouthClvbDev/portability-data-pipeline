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
    $('#period').textContent = `Fuente: CSV sintéticos del repositorio · Recepciones del ${data.period.start} al ${data.period.end} · SLA sintético de 48 horas corridas.`;
    const months = Object.entries(data.byMonth);
    const maxMonth = Math.max(...months.map(([, value]) => value));
    for (const [month, value] of months) {
      const item = document.createElement('div'); item.className = 'bar-item';
      item.style.setProperty('--bar-height', `${Math.max(value / maxMonth * 145, 2)}px`);
      const count = document.createElement('strong'); count.textContent = number(value);
      const bar = document.createElement('i');
      const name = document.createElement('span'); name.textContent = month.slice(5);
      item.append(count, bar, name); $('#monthly').append(item);
    }
    $('#monthly').setAttribute('aria-label', `Casos recibidos por mes: ${months.map(([month, value]) => `${month}: ${value}`).join(', ')}`);
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
  visual.append(bars, element('small', 'scenario-source', 'Fuente: CSV sintéticos · Cálculo generado al desplegar'));
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

async function ask(question) {
  message(question, 'user'); const pending = message('Consultando el resumen…', 'bot');
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, mode: $('#llm').checked ? 'llm' : 'dataset' }) });
    const data = await response.json();
    pending.textContent = data.answer || data.error || 'No pude responder esta vez.';
    if (data.note) pending.textContent += ` ${data.note}`;
    if (data.llmAvailable === false) $('#llm-state').textContent = '(sin configurar)';
  } catch { pending.textContent = 'No se pudo conectar con el asistente. Revisá el despliegue de la función.'; }
}

$('#chat-form').addEventListener('submit', (event) => { event.preventDefault(); const input = $('#question'); const question = input.value.trim(); if (question) { input.value = ''; ask(question); } });
document.querySelectorAll('[data-question]').forEach((button) => button.addEventListener('click', () => { $('#question').value = button.dataset.question; $('#question').focus(); }));
loadData();
loadScenarios();
