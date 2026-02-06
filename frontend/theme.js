// theme.js — light/dark/system theme toggle with no-FOUC
// Storage key is intentionally stable.
(function () {
  const STORAGE_KEY = 'rab-theme'; // 'light' | 'dark' | 'system'

  function getSystemTheme() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }

  function getSavedTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY) || 'system';
    } catch {
      return 'system';
    }
  }

  function resolveTheme(theme) {
    return theme === 'system' ? getSystemTheme() : theme;
  }

  function applyTheme(theme) {
    const resolved = resolveTheme(theme);
    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.setAttribute('data-theme-pref', theme);

    // Update segmented control (if present)
    const buttons = document.querySelectorAll('[data-theme-set]');
    buttons.forEach((btn) => {
      const v = btn.getAttribute('data-theme-set');
      btn.setAttribute('aria-pressed', String(v === theme));
      btn.classList.toggle('active', v === theme);
    });
  }

  function setTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {}
    applyTheme(theme);
  }

  function initTheme() {
    const pref = getSavedTheme();
    applyTheme(pref);

    // If user preference is system, react to system changes.
    if (window.matchMedia) {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      const handler = () => {
        const cur = getSavedTheme();
        if (cur === 'system') applyTheme(cur);
      };
      try {
        mq.addEventListener('change', handler);
      } catch {
        // Safari < 14
        mq.addListener(handler);
      }
    }

    // Wire UI
    document.addEventListener('click', (e) => {
      const t = e.target && e.target.closest ? e.target.closest('[data-theme-set]') : null;
      if (!t) return;
      const theme = t.getAttribute('data-theme-set');
      if (!theme) return;
      setTheme(theme);
    });
  }

  // Expose a minimal API for app.js if needed.
  window.Theme = {
    init: initTheme,
    set: setTheme,
    get: getSavedTheme,
    resolve: resolveTheme,
  };
})();
