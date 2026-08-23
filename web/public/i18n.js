'use strict';

const I18n = (() => {
  let _strings = {};
  let _lang = 'en';
  let _manifest = [];

  function t(key, ...args) {
    let s = _strings[key];
    if (s === undefined) return key;
    args.forEach((v, i) => { s = s.replaceAll(`{${i}}`, v); });
    return s;
  }

  async function _fetchManifest() {
    try {
      const r = await fetch('/locales/manifest.json');
      const d = await r.json();
      _manifest = d.languages || [];
    } catch {
      _manifest = [{ code: 'en', name: 'English' }];
    }
  }

  async function load(code) {
    try {
      const r = await fetch(`/locales/${code}.xml`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const raw = await r.text();
      const doc = new DOMParser().parseFromString(raw, 'application/xml');
      const err = doc.querySelector('parsererror');
      if (err) throw new Error('XML parse error');
      _strings = {};
      doc.querySelectorAll('t[id]').forEach(node => {
        _strings[node.getAttribute('id')] = node.textContent;
      });
      _lang = code;
      localStorage.setItem('mhdlang', code);
      _applyDOM();
      document.dispatchEvent(new CustomEvent('langchange', { detail: { lang: code } }));
    } catch (e) {
      if (code !== 'en') {
        console.warn(`[i18n] Failed to load "${code}", falling back to English.`, e);
        await load('en');
      }
    }
  }

  function _applyDOM() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = t(el.getAttribute('data-i18n'));
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      el.placeholder = t(el.getAttribute('data-i18n-ph'));
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      el.title = t(el.getAttribute('data-i18n-title'));
    });
    document.querySelectorAll('[data-i18n-aria]').forEach(el => {
      el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria')));
    });
    _buildLangSelect();
  }

  function _buildLangSelect() {
    const sel = document.getElementById('langSel');
    if (!sel) return;
    sel.innerHTML = '';
    _manifest.forEach(m => {
      const o = document.createElement('option');
      o.value = m.code;
      o.textContent = m.name;
      o.selected = m.code === _lang;
      sel.appendChild(o);
    });
  }

  async function init() {
    await _fetchManifest();
    const saved = localStorage.getItem('mhdlang') || 'en';
    await load(saved);
  }

  function getLang() { return _lang; }
  function getManifest() { return _manifest; }

  return { t, load, init, getLang, getManifest };
})();
