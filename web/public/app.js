'use strict';

const API = '';
let autoScroll = true;
let jwtToken = localStorage.getItem('jwt_token') || '';

async function ensureJwtToken() {
  if (jwtToken) return jwtToken;
  try {
    const res = await fetch(API + '/api/auth/token', { method: 'POST' }).then(r => r.json());
    if (res.success && res.token) {
      jwtToken = res.token;
      localStorage.setItem('jwt_token', jwtToken);
    }
  } catch {}
  return jwtToken;
}

async function apiFetch(url, options = {}) {
  options.headers = options.headers || {};
  await ensureJwtToken();
  if (jwtToken) {
    options.headers['Authorization'] = 'Bearer ' + jwtToken;
    options.headers['X-API-Key'] = jwtToken;
  }
  let r = await fetch(API + url, options);
  if (r.status === 401 && !url.includes('/api/auth/')) {
    jwtToken = '';
    localStorage.removeItem('jwt_token');
    await ensureJwtToken();
    if (jwtToken) {
      options.headers['Authorization'] = 'Bearer ' + jwtToken;
      options.headers['X-API-Key'] = jwtToken;
      r = await fetch(API + url, options);
    }
  }
  return r;
}

function fmt(n, unit) {
  if (n >= 1e9) return (n / 1e9).toFixed(1) + ' G' + unit;
  if (n >= 1e6) return (n / 1e6).toFixed(1) + ' M' + unit;
  if (n >= 1e3) return (n / 1e3).toFixed(1) + ' K' + unit;
  return n + ' ' + unit;
}

function clamp(v) { return Math.max(0, Math.min(100, v)); }
function $(id) { return document.getElementById(id); }
function escHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

const { t } = I18n;

const Toast = (() => {
  const ICONS = {
    success: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.4"/><polyline points="5,8.5 7,10.5 11,5.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    error:   `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.4"/><line x1="5.5" y1="5.5" x2="10.5" y2="10.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><line x1="10.5" y1="5.5" x2="5.5" y2="10.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`,
    warning: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2.5L13.8 12.5H2.2L8 2.5Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><line x1="8" y1="7" x2="8" y2="9.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="8" cy="11.2" r="0.7" fill="currentColor"/></svg>`,
    info:    `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.4"/><line x1="8" y1="7.5" x2="8" y2="11" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="8" cy="5.5" r="0.7" fill="currentColor"/></svg>`,
  };
  let container = null;

  function init() {
    if (container) return;
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  function show(msg, type = 'info', ms = 3800) {
    init();
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `<span class="toast-ico">${ICONS[type] || ICONS.info}</span><span class="toast-msg">${escHtml(msg)}</span><button class="toast-close" aria-label="Close">×</button>`;
    container.appendChild(el);
    requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add('visible')));
    const dismiss = () => { el.classList.remove('visible'); setTimeout(() => el.remove(), 300); };
    el.querySelector('.toast-close').addEventListener('click', dismiss);
    setTimeout(dismiss, ms);
  }

  return { show };
})();

const Dialog = (() => {
  function _render(html) {
    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = html;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => requestAnimationFrame(() => overlay.classList.add('visible')));
    return overlay;
  }

  function _close(overlay) {
    overlay.classList.remove('visible');
    setTimeout(() => overlay.remove(), 200);
  }

  function confirm(message, title, danger = false) {
    const hdTitle = title || t('dlg.stop_task.title');
    return new Promise(resolve => {
      const overlay = _render(`
        <div class="dialog" role="dialog" aria-modal="true">
          <div class="dialog-hd">${escHtml(hdTitle)}</div>
          <div class="dialog-body">${message}</div>
          <div class="dialog-foot">
            <button class="dialog-cancel">${t('dlg.cancel')}</button>
            <button class="dialog-ok${danger ? ' danger' : ''}">${t('dlg.confirm')}</button>
          </div>
        </div>`);

      const done = v => { _close(overlay); resolve(v); };
      overlay.querySelector('.dialog-ok').addEventListener('click', () => done(true));
      overlay.querySelector('.dialog-cancel').addEventListener('click', () => done(false));
      overlay.addEventListener('click', e => { if (e.target === overlay) done(false); });
      document.addEventListener('keydown', function esc(e) {
        if (e.key === 'Escape') { done(false); document.removeEventListener('keydown', esc); }
      });
    });
  }

  function alert(message, title) {
    const hdTitle = title || t('dlg.warn.title');
    return new Promise(resolve => {
      const overlay = _render(`
        <div class="dialog" role="dialog" aria-modal="true">
          <div class="dialog-hd">${escHtml(hdTitle)}</div>
          <div class="dialog-body">${message}</div>
          <div class="dialog-foot">
            <button class="dialog-ok">${t('dlg.ok')}</button>
          </div>
        </div>`);
      const done = () => { _close(overlay); resolve(); };
      overlay.querySelector('.dialog-ok').addEventListener('click', done);
      overlay.addEventListener('click', e => { if (e.target === overlay) done(); });
    });
  }

  return { confirm, alert };
})();

class CustomSelect {
  constructor(sel) {
    this._sel = sel;
    this._open = false;
    this._outside = null;
    this._build();
  }

  _build() {
    const wrap = document.createElement('div');
    wrap.className = 'csel';

    const trigger = document.createElement('div');
    trigger.className = 'csel-trigger';
    trigger.tabIndex = 0;
    trigger.setAttribute('role', 'combobox');

    const label = document.createElement('span');
    label.className = 'csel-label';

    const arrow = document.createElement('span');
    arrow.className = 'csel-arrow';
    arrow.innerHTML = `<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

    trigger.append(label, arrow);

    const dropdown = document.createElement('div');
    dropdown.className = 'csel-dropdown';

    wrap.append(trigger, dropdown);

    this._sel.style.display = 'none';
    this._sel.parentNode.insertBefore(wrap, this._sel);
    wrap.appendChild(this._sel);

    this._wrap = wrap;
    this._trigger = trigger;
    this._label = label;
    this._dropdown = dropdown;

    this._sync();
    this._listen();
  }

  _sync() {
    const opt = this._sel.options[this._sel.selectedIndex];
    this._label.textContent = opt ? opt.text : '—';
    this._dropdown.innerHTML = '';
    Array.from(this._sel.options).forEach((o, i) => {
      const item = document.createElement('div');
      item.className = 'csel-option' + (i === this._sel.selectedIndex ? ' selected' : '');
      item.innerHTML = `<span class="csel-opt-txt">${escHtml(o.text)}</span><span class="csel-check"><svg width="13" height="13" viewBox="0 0 13 13" fill="none"><polyline points="2,6.5 5,10 11,3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>`;
      item.addEventListener('mousedown', e => {
        e.preventDefault();
        this._sel.selectedIndex = i;
        this._sel.dispatchEvent(new Event('change', { bubbles: true }));
        this._sync();
        this._closeDropdown();
      });
      this._dropdown.appendChild(item);
    });
  }

  _openDropdown() {
    if (this._open) return;
    document.querySelectorAll('.csel.open').forEach(el => { if (el !== this._wrap) el.classList.remove('open'); });

    const rect = this._trigger.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;
    if (spaceBelow < 200 && spaceAbove > spaceBelow) {
      this._wrap.classList.add('open-up');
    } else {
      this._wrap.classList.remove('open-up');
    }

    this._open = true;
    this._wrap.classList.add('open');
    this._outside = e => { if (!this._wrap.contains(e.target)) this._closeDropdown(); };
    setTimeout(() => document.addEventListener('click', this._outside), 0);
  }

  _closeDropdown() {
    if (!this._open) return;
    this._open = false;
    this._wrap.classList.remove('open');
    if (this._outside) { document.removeEventListener('click', this._outside); this._outside = null; }
  }

  _listen() {
    this._trigger.addEventListener('click', e => {
      e.stopPropagation();
      this._open ? this._closeDropdown() : this._openDropdown();
    });
    this._trigger.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this._open ? this._closeDropdown() : this._openDropdown(); }
      if (e.key === 'Escape') this._closeDropdown();
    });
  }

  refresh() {
    if (this._open) this._closeDropdown();
    this._sync();
  }
}

let methods = { layer7: [], layer4: [], amplification: [], sockTypes: [] };
let methodCS = null;
let socksCS = null;
let layerCS = null;
let toolCS = null;
let langCS = null;

function getViewTitles() {
  return {
    dashboard: [t('nav.dashboard'),  t('sub.dashboard')],
    launch:    [t('nav.launch'),     t('sub.launch')],
    tasks:     [t('nav.tasks'),      t('sub.tasks')],
    tools:     [t('nav.tools'),      t('sub.tools')],
    terminal:  [t('nav.terminal'),   t('sub.terminal')],
  };
}

let currentView = 'dashboard';

function switchView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const view = $('view-' + name);
  if (view) view.classList.add('active');
  const btn = document.querySelector(`[data-view="${name}"]`);
  if (btn) btn.classList.add('active');
  currentView = name;
  const vt = getViewTitles();
  const [title, sub] = vt[name] || ['—', ''];
  $('viewTitle').textContent = title;
  $('viewSub').textContent = sub;
  if (name === 'tasks') loadTasks();
}

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => switchView(btn.dataset.view));
});

$('viewTermBtn').addEventListener('click', () => switchView('terminal'));

async function pollStats() {
  try {
    const d = await apiFetch('/api/system/stats').then(r => r.json());
    $('cpuVal').textContent = d.cpu_percent + '%';
    $('cpuBar').style.width = clamp(d.cpu_percent) + '%';
    $('ramVal').textContent = d.ram_percent + '%';
    $('ramBar').style.width = clamp(d.ram_percent) + '%';
    $('ramDetail').textContent = d.ram_used_gb + ' / ' + d.ram_total_gb + ' GB';
    $('netSentVal').textContent = fmt(d.bytes_sent, 'B');
    $('activeVal').textContent = d.active_attacks;
    $('activeVal').style.color = d.active_attacks > 0 ? 'var(--accent)' : 'var(--text2)';
  } catch { }
}

async function pollResources() {
  try {
    const d = await apiFetch('/api/files/info').then(r => r.json());
    $('uaCount').textContent = d.useragents_count.toLocaleString();
    $('refCount').textContent = d.referers_count.toLocaleString();
    $('proxyCount').textContent = d.proxy_files.length;
  } catch { }
}

function updateLayerOptions() {
  const sel = $('layerSel');
  Array.from(sel.options).forEach(o => {
    const key = o.getAttribute('data-i18n-opt');
    if (key) o.textContent = t(key);
  });
  if (layerCS) layerCS.refresh();
}

function updateToolOptions() {
  const sel = $('toolSel');
  Array.from(sel.options).forEach(o => {
    const key = o.getAttribute('data-i18n-opt');
    if (key) o.textContent = t(key);
  });
  if (toolCS) toolCS.refresh();
}

async function loadMethods() {
  try {
    methods = await apiFetch('/api/methods').then(r => r.json());
    populateMethodSel();
    populateSocksSel();
    if (!methodCS) methodCS = new CustomSelect($('methodSel'));
    else methodCS.refresh();
    if (!socksCS) socksCS = new CustomSelect($('socksSel'));
    else socksCS.refresh();
  } catch { }
}

function populateMethodSel() {
  const layer = $('layerSel').value;
  const sel = $('methodSel');
  sel.innerHTML = '';
  const list = layer === 'L7' ? methods.layer7 : layer === 'L4' ? methods.layer4 : methods.amplification;
  list.forEach(m => { const o = document.createElement('option'); o.value = m; o.textContent = m; sel.appendChild(o); });
  toggleL7Fields(layer);
  if (methodCS) methodCS.refresh();
}

function populateSocksSel() {
  const sel = $('socksSel');
  sel.innerHTML = '';
  methods.sockTypes.forEach(s => { const o = document.createElement('option'); o.value = s.id; o.textContent = s.name; sel.appendChild(o); });
  if (socksCS) socksCS.refresh();
}

function toggleL7Fields(layer) {
  const isL7 = layer === 'L7';
  const isAmp = methods.amplification.includes($('methodSel').value);
  $('socksField').style.display = isL7 ? '' : 'none';
  $('proxyField').style.display = (isL7 || (layer === 'L4' && !isAmp)) ? '' : 'none';
  $('rpcField').style.display = isL7 ? '' : 'none';
  $('reflField').style.display = (!isL7 && isAmp) ? '' : 'none';
  $('targetLabel').textContent = t(isL7 ? 'form.target.l7' : 'form.target.l4');
  $('targetInp').placeholder = t(isL7 ? 'form.target.ph.l7' : 'form.target.ph.l4');
}

$('layerSel').addEventListener('change', populateMethodSel);
$('methodSel').addEventListener('change', () => toggleL7Fields($('layerSel').value));

$('launchForm').addEventListener('submit', async e => {
  e.preventDefault();
  const btn = $('launchBtn');
  btn.disabled = true;
  btn.querySelector('span').textContent = t('form.starting');
  try {
    const r = await apiFetch('/api/attacks/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        layer: $('layerSel').value,
        method: $('methodSel').value,
        target: $('targetInp').value.trim(),
        threads: parseInt($('threadsInp').value),
        duration: parseInt($('durationInp').value),
        socks_type: parseInt($('socksSel').value || '0'),
        proxylist: $('proxyInp').value.trim(),
        rpc: parseInt($('rpcInp').value),
        reflector: $('reflInp').value.trim(),
      }),
    });
    const d = await r.json();
    if (d.success) {
      Toast.show(t('toast.task_started', d.task_id, d.pid), 'success');
      switchView('tasks');
    } else {
      await Dialog.alert(escHtml(d.error), t('dlg.error.title'));
    }
  } catch (err) {
    await Dialog.alert(escHtml(err.message), t('dlg.error.title'));
  } finally {
    btn.disabled = false;
    btn.querySelector('span').textContent = t('form.start');
  }
});

async function loadTasks() {
  try {
    const tasks = await apiFetch('/api/attacks/active').then(r => r.json());
    const tbody = $('tasksTbody');
    if (!tasks.length) {
      tbody.innerHTML = `<tr class="empty-row"><td colspan="10">${t('task.empty')}</td></tr>`;
      return;
    }
    const badges = { RUNNING: 'badge-run', STOPPED: 'badge-stop', FINISHED: 'badge-done' };
    tbody.innerHTML = tasks.map(task => `<tr>
      <td class="mono">${escHtml(task.id)}</td>
      <td class="mono">${task.pid}</td>
      <td>${task.layer}</td>
      <td class="mono">${escHtml(task.method)}</td>
      <td>${escHtml(task.target)}</td>
      <td class="mono">${task.threads}</td>
      <td class="mono">${task.start_time}</td>
      <td class="mono">${task.elapsed}s / ${task.duration}s</td>
      <td><span class="badge ${badges[task.status] || 'badge-done'}">${task.status}</span></td>
      <td>${task.status === 'RUNNING' ? `<button class="btn-stop" data-id="${task.id}">${t('task.stop')}</button>` : ''}</td>
    </tr>`).join('');
  } catch { }
}

$('tasksTbody').addEventListener('click', async e => {
  const btn = e.target.closest('[data-id]');
  if (!btn) return;
  const id = btn.dataset.id;
  const ok = await Dialog.confirm(t('dlg.stop_task.msg', id), t('dlg.stop_task.title'), true);
  if (!ok) return;
  try {
    const d = await apiFetch('/api/attacks/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    }).then(r => r.json());
    Toast.show(
      d.stopped.length ? t('toast.task_stopped') : t('toast.none_stopped'),
      d.stopped.length ? 'success' : 'warning'
    );
    loadTasks();
  } catch (err) {
    Toast.show(t('toast.stop_error', err.message), 'error');
  }
});

$('killAllBtn').addEventListener('click', async () => {
  const ok = await Dialog.confirm(t('dlg.stop_all.msg'), t('dlg.stop_all.title'), true);
  if (!ok) return;
  try {
    const d = await apiFetch('/api/attacks/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: 'all' }),
    }).then(r => r.json());
    Toast.show(t('toast.all_stopped', d.stopped.length), d.stopped.length ? 'success' : 'warning');
    loadTasks();
  } catch (err) {
    Toast.show(t('toast.stop_error', err.message), 'error');
  }
});

$('refreshTasksBtn').addEventListener('click', loadTasks);

function addTermLine(time, text) {
  const term = $('terminal');
  const div = document.createElement('div');
  div.className = 't-line';
  div.innerHTML = `<span class="t-time">${time}</span><span class="t-text">${escHtml(text)}</span>`;
  term.appendChild(div);
  if (term.children.length > 600) term.removeChild(term.children[0]);
  if (autoScroll) term.scrollTop = term.scrollHeight;
  const dash = $('dashLog');
  if (dash) {
    const clone = div.cloneNode(true);
    dash.appendChild(clone);
    if (dash.children.length > 30) dash.removeChild(dash.children[0]);
    dash.scrollTop = dash.scrollHeight;
  }
}

function connectSSE() {
  const tokenParam = jwtToken ? '?token=' + encodeURIComponent(jwtToken) : '';
  const es = new EventSource(API + '/api/logs/stream' + tokenParam);
  es.onmessage = e => { try { const d = JSON.parse(e.data); addTermLine(d.time, d.text); } catch { } };
  es.onerror = () => {
    $('connDot').style.background = 'var(--danger)';
    $('connDot').style.boxShadow = 'none';
    setTimeout(connectSSE, 3000);
  };
  es.onopen = () => {
    $('connDot').style.background = 'var(--accent)';
    $('connDot').style.boxShadow = '0 0 8px var(--accent)';
  };
}

$('clearTermBtn').addEventListener('click', () => { $('terminal').innerHTML = ''; $('dashLog').innerHTML = ''; });

$('scrollBtn').addEventListener('click', () => {
  autoScroll = !autoScroll;
  $('scrollBtn').textContent = t(autoScroll ? 'term.autoscroll.on' : 'term.autoscroll.off');
});

$('runToolBtn').addEventListener('click', async () => {
  const tool = $('toolSel').value;
  const target = $('toolInp').value.trim();
  if (!target) { Toast.show(t('toast.target_required'), 'warning'); return; }
  const out = $('toolOutput');
  out.classList.add('active');
  out.textContent = '…';
  try {
    const d = await apiFetch('/api/tools/' + tool, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target }),
    }).then(r => r.json());
    out.textContent = JSON.stringify(d, null, 2);
    Toast.show(t('toast.tool_done'), 'success', 2000);
  } catch (err) {
    out.textContent = t('toast.net_error', err.message);
    Toast.show(t('toast.exec_failed'), 'error');
  }
});

$('themeBtn').addEventListener('click', () => {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  $('themeLbl').textContent = t(isDark ? 'theme.to_dark' : 'theme.to_light');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
});

$('langSel').addEventListener('change', async e => {
  await I18n.load(e.target.value);
  if (langCS) langCS.refresh();
});

document.addEventListener('langchange', () => {
  updateDynamicStrings();
});

function updateDynamicStrings() {
  updateLayerOptions();
  updateToolOptions();
  if (langCS) langCS.refresh();
  switchView(currentView);
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  $('themeLbl').textContent = t(isDark ? 'theme.to_light' : 'theme.to_dark');
  $('scrollBtn').textContent = t(autoScroll ? 'term.autoscroll.on' : 'term.autoscroll.off');
  toggleL7Fields($('layerSel').value);
  if ($('view-tasks').classList.contains('active')) loadTasks();
}

(async () => {
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);

  await I18n.init();

  $('themeLbl').textContent = t(savedTheme === 'dark' ? 'theme.to_light' : 'theme.to_dark');

  layerCS = new CustomSelect($('layerSel'));
  toolCS  = new CustomSelect($('toolSel'));
  langCS  = new CustomSelect($('langSel'));
  updateLayerOptions();
  updateToolOptions();
  switchView('dashboard');

  setInterval(pollStats, 2000);
  setInterval(() => { if ($('view-tasks').classList.contains('active')) loadTasks(); }, 3000);

  pollStats();
  pollResources();
  loadMethods();
  connectSSE();
})();
