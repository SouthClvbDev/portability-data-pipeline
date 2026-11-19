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

async function ask(question) {
  message(question, 'user'); const pending = message('Consultando el resumen…', 'bot');
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, mode: $('#llm').checked ? 'llm' : 'dataset' }) });
    const data = await response.json();
    pending.textContent = data.answer || data.error || 'No pude responder esta vez.';
    if (data.llmAvailable === false) $('#llm-state').textContent = '(sin configurar)';
  } catch { pending.textContent = 'No se pudo conectar con el asistente. Revisá el despliegue de la función.'; }
}

$('#chat-form').addEventListener('submit', (event) => { event.preventDefault(); const input = $('#question'); const question = input.value.trim(); if (question) { input.value = ''; ask(question); } });
document.querySelectorAll('[data-question]').forEach((button) => button.addEventListener('click', () => { $('#question').value = button.dataset.question; $('#question').focus(); }));
loadData();
