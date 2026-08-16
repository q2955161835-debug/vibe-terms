(() => {
  'use strict';

  const core = globalThis.VibeCore;
  if (!core) {
    console.error('Vibe Terms core helpers are unavailable.');
    return;
  }

  const root = document.documentElement;
  const locale = (root.lang || 'en').toLowerCase();
  const basePath = String(root.dataset.basePath || '').replace(/\/$/, '');
  const messagesNode = document.querySelector('#ui-messages');
  let messages = {};

  try {
    messages = messagesNode ? JSON.parse(messagesNode.textContent || '{}') : {};
  } catch (error) {
    console.error('Localized interface messages could not be parsed.', error);
  }

  const message = (key) => (typeof messages[key] === 'string' ? messages[key] : '');

  try {
    localStorage.setItem('vibe-locale', locale);
  } catch {
    // Public browsing never depends on storage permission.
  }

  document.querySelectorAll('[data-locale-picker]').forEach((picker) => {
    picker.addEventListener('change', () => {
      const nextLocale = picker.value;
      const path = picker.dataset.path || '/';
      try {
        localStorage.setItem('vibe-locale', nextLocale);
      } catch {
        // Navigation still works when locale persistence is blocked.
      }
      window.location.href = `${basePath}/${nextLocale}${path}`;
    });
  });

  const themeButton = document.querySelector('.theme-toggle');
  const themeOrder = ['system', 'light', 'dark'];
  const themeIcons = { system: '◐', light: '☀', dark: '☾' };

  function setTheme(theme) {
    const normalized = themeOrder.includes(theme) ? theme : 'system';
    root.dataset.theme = normalized;

    if (themeButton) {
      themeButton.textContent = themeIcons[normalized];
      const label = message(`theme_${normalized}`);
      themeButton.setAttribute('aria-label', label);
      themeButton.title = label;
    }

    try {
      localStorage.setItem('vibe-theme', normalized);
    } catch {
      // The selected theme still applies to the current document.
    }
  }

  setTheme(root.dataset.theme || 'system');
  themeButton?.addEventListener('click', () => {
    const current = root.dataset.theme || 'system';
    const next = themeOrder[(themeOrder.indexOf(current) + 1) % themeOrder.length];
    setTheme(next);
  });

  let termsPromise;
  function loadTerms() {
    if (!termsPromise) {
      termsPromise = fetch(`${basePath}/assets/terms.${locale}.json`, {
        credentials: 'same-origin',
      }).then((response) => {
        if (!response.ok) {
          throw new Error(`Term index request failed with status ${response.status}.`);
        }
        return response.json();
      });
    }
    return termsPromise;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;',
    })[character]);
  }

  const homeSearchForm = document.querySelector('#home-search-form');
  if (homeSearchForm && !homeSearchForm.hasAttribute('data-global-search')) {
    const input = homeSearchForm.querySelector('#home-search');
    const panel = homeSearchForm.querySelector('#search-results');
    let activeIndex = -1;
    let searchTimer;

    function closeResults() {
      panel.hidden = true;
      input.setAttribute('aria-expanded', 'false');
      input.removeAttribute('aria-activedescendant');
      activeIndex = -1;
    }

    function setActiveResult(index) {
      const options = Array.from(panel.querySelectorAll('[role="option"]'));
      options.forEach((option) => {
        option.classList.remove('is-active');
        option.setAttribute('aria-selected', 'false');
      });
      if (!options.length) return;

      activeIndex = (index + options.length) % options.length;
      const option = options[activeIndex];
      option.classList.add('is-active');
      option.setAttribute('aria-selected', 'true');
      input.setAttribute('aria-activedescendant', option.id);
      option.scrollIntoView({ block: 'nearest' });
    }

    function rankTerms(terms, query) {
      return terms
        .map((term) => ({ term, score: core.scoreTerm(term, query) }))
        .filter(({ score }) => score > 0)
        .sort(
          (left, right) =>
            right.score - left.score ||
            (left.term.learning_order ?? Number.MAX_SAFE_INTEGER) -
              (right.term.learning_order ?? Number.MAX_SAFE_INTEGER) ||
            left.term.title.localeCompare(right.term.title, locale),
        )
        .slice(0, 8)
        .map(({ term }) => term);
    }

    function renderSearchRows(terms) {
      if (!terms.length) {
        panel.innerHTML = `<div class="search-result search-empty" role="status"><small>${escapeHtml(message('no_results'))}</small></div>`;
        return;
      }

      panel.innerHTML = terms
        .map(
          (term, index) => `
            <a
              id="search-option-${index}"
              class="search-result"
              role="option"
              aria-selected="false"
              href="/${locale}/terms/${term.slug}/"
            >
              <strong>${escapeHtml(term.title)}</strong>
              <small>${escapeHtml(term.short_definition)}</small>
              <span>${escapeHtml(term.domain_title)}</span>
            </a>
          `,
        )
        .join('');
    }

    async function renderResults() {
      const query = core.normalizeSearchText(input.value);
      if (!query) {
        closeResults();
        return [];
      }

      panel.hidden = false;
      panel.setAttribute('aria-busy', 'true');
      input.setAttribute('aria-expanded', 'true');

      try {
        const results = rankTerms(await loadTerms(), query);
        renderSearchRows(results);
        return results;
      } catch (error) {
        console.error(error);
        panel.innerHTML = `<div class="search-result search-empty" role="status"><small>${escapeHtml(message('load_error'))}</small></div>`;
        return [];
      } finally {
        panel.setAttribute('aria-busy', 'false');
        activeIndex = -1;
        input.removeAttribute('aria-activedescendant');
      }
    }

    input.addEventListener('input', () => {
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(renderResults, 90);
    });

    input.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setActiveResult(activeIndex + 1);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setActiveResult(activeIndex - 1);
      } else if (event.key === 'Escape') {
        closeResults();
      } else if (event.key === 'Enter' && activeIndex >= 0) {
        event.preventDefault();
        panel.querySelectorAll('[role="option"]')[activeIndex]?.click();
      }
    });

    homeSearchForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const results = await renderResults();
      if (results[0]) {
        window.location.href = `${basePath}/${locale}/terms/${results[0].slug}/`;
      } else {
        input.focus();
      }
    });

    document.addEventListener('pointerdown', (event) => {
      if (!homeSearchForm.contains(event.target)) closeResults();
    });
  }

  async function copyText(text) {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }

    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.append(textarea);
    textarea.select();
    const success = document.execCommand('copy');
    textarea.remove();
    if (!success) throw new Error('Clipboard fallback failed.');
  }

  document.querySelectorAll('.copy-prompt').forEach((button) => {
    button.addEventListener('click', async () => {
      const original = button.textContent;
      try {
        await copyText(button.dataset.copy || '');
        button.textContent = message('copied') || original;
      } catch (error) {
        console.error(error);
        button.textContent = message('copy_failed') || original;
      }
      window.setTimeout(() => {
        button.textContent = original;
      }, 1400);
    });
  });

  const DB_NAME = 'vibe-terms-guest-v1';
  const STORE_NAME = 'progress';
  const DB_VERSION = 1;
  const FALLBACK_KEY = 'vibe-terms-progress-v1';
  let databasePromise;

  function openDatabase() {
    if (!('indexedDB' in globalThis)) {
      return Promise.reject(new Error('IndexedDB is unavailable.'));
    }
    if (databasePromise) return databasePromise;

    databasePromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const database = request.result;
        if (!database.objectStoreNames.contains(STORE_NAME)) {
          database.createObjectStore(STORE_NAME, { keyPath: 'slug' });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('IndexedDB open failed.'));
      request.onblocked = () => reject(new Error('IndexedDB upgrade was blocked.'));
    });

    return databasePromise;
  }

  async function withStore(mode, operation) {
    const database = await openDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(STORE_NAME, mode);
      const request = operation(transaction.objectStore(STORE_NAME));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('IndexedDB request failed.'));
      transaction.onabort = () => reject(transaction.error || new Error('IndexedDB transaction failed.'));
    });
  }

  function readFallbackProgress() {
    try {
      const value = JSON.parse(localStorage.getItem(FALLBACK_KEY) || '[]');
      return Array.isArray(value) ? value : [];
    } catch {
      return [];
    }
  }

  function writeFallbackProgress(row) {
    const rows = readFallbackProgress().filter((item) => item.slug !== row.slug);
    rows.push(row);
    localStorage.setItem(FALLBACK_KEY, JSON.stringify(rows));
  }

  async function getAllProgress() {
    try {
      return await withStore('readonly', (store) => store.getAll());
    } catch {
      return readFallbackProgress();
    }
  }

  async function putProgress(row) {
    try {
      await withStore('readwrite', (store) => store.put(row));
    } catch {
      writeFallbackProgress(row);
    }
  }

  function toStoredProgress(previous, rating, now) {
    const scheduled = core.scheduleReview(previous, rating, now);
    return scheduled;
  }

  document.querySelectorAll('.learn-one').forEach((button) => {
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        const rows = await getAllProgress();
        const existing = rows.find((row) => row.slug === button.dataset.term);
        const now = Date.now();
        await putProgress({
          ...(existing || {}),
          slug: button.dataset.term,
          rating: 'queued',
          queued: true,
          nextReviewAt: 0,
          reviews: existing?.reviews || 0,
          updatedAt: now,
          dailySessionDate: existing?.dailySessionDate || null,
        });
        button.textContent = message('queued') || '✓';
        button.setAttribute('aria-pressed', 'true');
      } catch (error) {
        console.error(error);
        button.disabled = false;
        button.textContent = message('storage_error') || button.textContent;
      }
    });
  });

  const learningCard = document.querySelector('#learning-card');
  if (learningCard) {
    const dailyInput = document.querySelector('#daily-count');
    const startButton = document.querySelector('#start-learning');
    const template = document.querySelector('#learning-template');
    const progressLabel = document.querySelector('#learn-progress');
    const statusLabel = document.querySelector('#learning-status');
    let queue = [];
    let currentIndex = 0;
    let progressBySlug = new Map();

    try {
      dailyInput.value = String(
        core.clampDailyCount(localStorage.getItem('vibe-daily-count') || 3),
      );
    } catch {
      dailyInput.value = '3';
    }

    function saveDailyCount() {
      const value = core.clampDailyCount(dailyInput.value);
      dailyInput.value = String(value);
      try {
        localStorage.setItem('vibe-daily-count', String(value));
      } catch {
        // The current choice still applies to this learning session.
      }
    }

    dailyInput.addEventListener('change', saveDailyCount);
    dailyInput.addEventListener('blur', saveDailyCount);

    function showStorageError() {
      if (!statusLabel) return;
      statusLabel.textContent = message('storage_error');
      statusLabel.hidden = false;
    }

    function renderLearningCard() {
      progressLabel.textContent = `${Math.min(currentIndex, queue.length)} / ${queue.length}`;

      if (currentIndex >= queue.length) {
        learningCard.innerHTML = `<div class="learning-empty"><strong aria-hidden="true">✓</strong><p>${escapeHtml(message('done'))}</p></div>`;
        return;
      }

      const term = queue[currentIndex];
      const node = template.content.cloneNode(true);
      const title = node.querySelector('.learn-title');
      const answer = node.querySelector('.learn-answer');
      const reveal = node.querySelector('.reveal');

      node.querySelector('.learn-position').textContent = `${currentIndex + 1} / ${queue.length}`;
      node.querySelector('.learn-domain').textContent = term.domain_title;
      title.textContent = term.title;
      node.querySelector('.learn-canonical').textContent =
        term.title === term.canonical_name ? '' : term.canonical_name;
      node.querySelector('.learn-definition').textContent = term.short_definition;
      node.querySelector('.learn-analogy').textContent = term.analogy;

      reveal.addEventListener('click', () => {
        reveal.hidden = true;
        answer.hidden = false;
        answer.querySelector('[data-rating]')?.focus();
      });

      node.querySelectorAll('[data-rating]').forEach((button) => {
        button.addEventListener('click', async () => {
          answer.querySelectorAll('button').forEach((item) => {
            item.disabled = true;
          });

          try {
            const previous = progressBySlug.get(term.slug);
            const now = Date.now();
            const next = {
              ...toStoredProgress(previous, button.dataset.rating, now),
              slug: term.slug,
            };
            await putProgress(next);
            progressBySlug.set(term.slug, next);
            currentIndex += 1;
            renderLearningCard();
          } catch (error) {
            console.error(error);
            showStorageError();
            answer.querySelectorAll('button').forEach((item) => {
              item.disabled = false;
            });
          }
        });
      });

      learningCard.replaceChildren(node);
      title.focus({ preventScroll: true });
    }

    async function beginLearning() {
      startButton.disabled = true;
      statusLabel.hidden = true;
      saveDailyCount();

      try {
        const [terms, progressRows] = await Promise.all([loadTerms(), getAllProgress()]);
        progressBySlug = new Map(progressRows.map((row) => [row.slug, row]));
        queue = core.buildDailyQueue(
          terms,
          progressRows,
          dailyInput.value,
          Date.now(),
        );
        currentIndex = 0;
        const now = Date.now();
        const dailySessionDate = core.localDateKey(now);
        const newRows = [];
        for (const term of queue) {
          if (progressBySlug.has(term.slug)) continue;
          const row = {
            slug: term.slug,
            rating: 'queued',
            queued: true,
            reviews: 0,
            intervalDays: 0,
            nextReviewAt: now,
            introducedOn: dailySessionDate,
            dailySessionDate,
            updatedAt: now,
          };
          await putProgress(row);
          progressBySlug.set(term.slug, row);
          newRows.push(row);
        }
        try {
          localStorage.setItem('vibe-daily-session-date', dailySessionDate);
        } catch {
          // This marker is optional; the review schedule is stored with each term.
        }
        renderLearningCard();
      } catch (error) {
        console.error(error);
        showStorageError();
        startButton.disabled = false;
      }
    }

    startButton?.addEventListener('click', beginLearning);
  }
})();

(() => {
  'use strict';

  const core = globalThis.VibeCore;
  if (!core) return;

  const root = document.documentElement;
  const locale = (root.dataset.locale || root.lang || 'en').toLowerCase();
  const basePath = String(root.dataset.basePath || '').replace(/\/$/, '');
  const assetUrl = (name) => `${basePath}/assets/${name}`;
  const localStateKey = 'vibe-terms-local-v2-fallback';
  const databaseName = 'vibe-terms-local-v2';
  const stores = ['termProgress', 'exerciseAttempts', 'pathProgress', 'bookmarks', 'recentViews'];

  function escapeText(value) {
    return String(value ?? '').replace(/[&<>"']/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    })[character]);
  }

  function readFallback() {
    try {
      const parsed = JSON.parse(localStorage.getItem(localStateKey) || 'null');
      return core.migrateLocalStateV1(parsed || [], Date.now());
    } catch {
      return core.migrateLocalStateV1([], Date.now());
    }
  }

  function writeFallback(state) {
    try {
      localStorage.setItem(localStateKey, JSON.stringify(state));
      return true;
    } catch {
      return false;
    }
  }

  function openDatabase() {
    if (!('indexedDB' in globalThis)) return Promise.resolve(null);
    return new Promise((resolve) => {
      const request = indexedDB.open(databaseName, 1);
      request.onupgradeneeded = () => {
        for (const store of stores) {
          if (!request.result.objectStoreNames.contains(store)) {
            const keyPath = store === 'termProgress' ? 'slug' : store === 'exerciseAttempts' ? 'exerciseId' : store === 'pathProgress' ? 'pathId' : 'id';
            request.result.createObjectStore(store, { keyPath });
          }
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
      request.onblocked = () => resolve(null);
    });
  }

  async function getAll(storeName) {
    const database = await openDatabase();
    if (!database) {
      const fallback = readFallback();
      const key = storeName === 'termProgress' ? 'termProgress' : storeName;
      return Array.isArray(fallback[key]) ? fallback[key] : [];
    }
    return new Promise((resolve) => {
      const request = database.transaction(storeName, 'readonly').objectStore(storeName).getAll();
      request.onsuccess = () => { database.close(); resolve(request.result || []); };
      request.onerror = () => { database.close(); resolve([]); };
    });
  }

  async function put(storeName, row) {
    const database = await openDatabase();
    if (!database) {
      const state = readFallback();
      const key = storeName === 'termProgress' ? 'termProgress' : storeName;
      const rows = Array.isArray(state[key]) ? state[key] : [];
      const idKey = storeName === 'termProgress' ? 'slug' : storeName === 'exerciseAttempts' ? 'exerciseId' : storeName === 'pathProgress' ? 'pathId' : 'id';
      const next = rows.filter((item) => item[idKey] !== row[idKey]);
      next.push(row);
      state[key] = next;
      writeFallback(state);
      return;
    }
    await new Promise((resolve) => {
      const transaction = database.transaction(storeName, 'readwrite');
      transaction.objectStore(storeName).put(row);
      transaction.oncomplete = resolve;
      transaction.onerror = resolve;
    });
    database.close();
  }

  async function migrateV1() {
    const marker = 'vibe-terms-v2-migration-complete';
    try {
      if (localStorage.getItem(marker) === '1') return;
      const rows = JSON.parse(localStorage.getItem('vibe-terms-progress-v1') || '[]');
      if (typeof indexedDB.databases === 'function') {
        const existing = await indexedDB.databases();
        if (existing.some((entry) => entry.name === 'vibe-terms-guest-v1')) {
          const legacyRows = await new Promise((resolve) => {
            const request = indexedDB.open('vibe-terms-guest-v1');
            request.onsuccess = () => {
              const database = request.result;
              if (!database.objectStoreNames.contains('progress')) { database.close(); resolve([]); return; }
              const read = database.transaction('progress', 'readonly').objectStore('progress').getAll();
              read.onsuccess = () => { database.close(); resolve(read.result || []); };
              read.onerror = () => { database.close(); resolve([]); };
            };
            request.onerror = () => resolve([]);
          });
          const bySlug = new Map(rows.map((row) => [row.slug, row]));
          for (const row of legacyRows) {
            const previous = bySlug.get(row.slug);
            if (!previous || Number(row.updatedAt || 0) > Number(previous.updatedAt || 0)) bySlug.set(row.slug, row);
          }
          rows.splice(0, rows.length, ...bySlug.values());
        }
      }
      const migrated = core.migrateLocalStateV1(rows, Date.now());
      for (const row of migrated.termProgress) await put('termProgress', row);
      localStorage.setItem(marker, '1');
    } catch {
      // A failed migration remains retryable and never blocks browsing.
    }
  }

  migrateV1();

  let searchDocumentsPromise;
  function loadSearchDocuments() {
    if (!searchDocumentsPromise) {
      const configured = root.dataset.searchIndex || assetUrl(`search-index.${locale}.json`);
      searchDocumentsPromise = fetch(configured, { credentials: 'same-origin' }).then((response) => {
        if (!response.ok) throw new Error(`Search index request failed (${response.status}).`);
        return response.json();
      }).then((payload) => Array.isArray(payload) ? payload : payload.documents || []);
    }
    return searchDocumentsPromise;
  }

  function searchGroupLabel(type) {
    const labels = {
      term: { en: 'Terms', 'zh-cn': '词条', 'zh-tw': '詞條' },
      topic: { en: 'Topics', 'zh-cn': '主题', 'zh-tw': '主題' },
      path: { en: 'Project paths', 'zh-cn': '项目路径', 'zh-tw': '專案路徑' },
    };
    return labels[type]?.[locale] || labels[type]?.en || type;
  }

  function renderGroupedResults(panel, groups) {
    const rows = ['term', 'topic', 'path'].flatMap((type) => {
      const documents = groups[type] || [];
      if (!documents.length) return [];
      return [
        `<div class="search-group-label" role="presentation">${escapeText(searchGroupLabel(type))}</div>`,
        ...documents.map((document, index) => `
          <a class="search-result" role="option" aria-selected="false"
             id="global-search-${type}-${index}" href="${escapeText(document.url)}">
            <strong>${escapeText(document.title)}</strong>
            <small>${escapeText(document.summary || document.short_definition || document.canonical_name)}</small>
            <span>${escapeText(document.badge || searchGroupLabel(type))}</span>
          </a>`),
      ];
    });
    panel.innerHTML = rows.length
      ? rows.join('')
      : '<div class="search-empty" role="status">No matching term, topic, or path.</div>';
    panel.hidden = false;
  }

  function bindGlobalSearch(form) {
    if (form.dataset.searchBound === 'true') return;
    form.dataset.searchBound = 'true';
    const input = form.querySelector('[data-search-input], input[type="search"], input[role="combobox"]');
    const panel = form.querySelector('[data-search-results], [role="listbox"]');
    if (!input || !panel) return;
    let active = -1;
    let timer;

    const options = () => Array.from(panel.querySelectorAll('[role="option"]'));
    const activate = (index) => {
      const rows = options();
      if (!rows.length) return;
      rows.forEach((row) => { row.classList.remove('is-active'); row.setAttribute('aria-selected', 'false'); });
      active = (index + rows.length) % rows.length;
      rows[active].classList.add('is-active');
      rows[active].setAttribute('aria-selected', 'true');
      input.setAttribute('aria-activedescendant', rows[active].id);
      rows[active].scrollIntoView({ block: 'nearest' });
    };

    const render = async () => {
      const query = core.normalizeSearchText(input.value);
      if (!query) { panel.hidden = true; input.setAttribute('aria-expanded', 'false'); return; }
      input.setAttribute('aria-expanded', 'true');
      panel.hidden = false;
      panel.setAttribute('aria-busy', 'true');
      try {
        renderGroupedResults(panel, core.groupSearchResults(await loadSearchDocuments(), query, 10));
      } catch (error) {
        console.error(error);
        panel.innerHTML = '<div class="search-empty" role="status">Search is unavailable. Ordinary navigation still works.</div>';
      } finally {
        panel.setAttribute('aria-busy', 'false');
        active = -1;
      }
    };

    input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(render, 80); });
    input.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown') { event.preventDefault(); activate(active + 1); }
      else if (event.key === 'ArrowUp') { event.preventDefault(); activate(active - 1); }
      else if (event.key === 'Enter' && active >= 0) { event.preventDefault(); options()[active]?.click(); }
      else if (event.key === 'Escape') { panel.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); }
    });
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (active >= 0) { options()[active]?.click(); return; }
      await render();
      options()[0]?.click();
    });
  }

  const searchForms = Array.from(document.querySelectorAll('[data-global-search]'));
  searchForms.forEach(bindGlobalSearch);

  const mobileDialog = document.querySelector('#mobile-search-dialog');
  let mobileTrigger = null;
  document.querySelectorAll('[data-search-open]').forEach((button) => {
    button.addEventListener('click', () => {
      mobileTrigger = button;
      if (mobileDialog?.showModal) mobileDialog.showModal();
      else mobileDialog?.setAttribute('open', '');
      mobileDialog?.querySelector('[data-search-input]')?.focus();
    });
  });
  mobileDialog?.querySelector('[data-search-close]')?.addEventListener('click', () => mobileDialog.close());
  mobileDialog?.addEventListener('close', () => mobileTrigger?.focus());
  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      const desktop = document.querySelector('.desktop-search [data-search-input]');
      if (desktop && getComputedStyle(desktop).display !== 'none') desktop.focus();
      else document.querySelector('[data-search-open]')?.click();
    }
  });

  document.querySelectorAll('[data-example-root]').forEach((element) => {
    globalThis.VibeExamples?.mount(element, { id: element.dataset.exampleId });
  });

  document.querySelectorAll('[data-exercise]').forEach((container) => {
    const payloadNode = container.querySelector('[data-exercise-payload]');
    const form = container.matches('form') ? container : container.querySelector('form');
    const feedback = container.querySelector('[data-exercise-feedback]');
    if (!payloadNode || !form || !feedback) return;
    let exercise;
    try { exercise = JSON.parse(payloadNode.textContent || '{}'); } catch { return; }
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const selected = Array.from(form.querySelectorAll('input:checked')).map((input) => input.value);
      const result = core.gradeExercise(exercise, selected);
      feedback.hidden = false;
      feedback.dataset.correct = String(result.correct);
      feedback.textContent = result.correct
        ? (exercise.correct_feedback || 'Correct — the concept is connected.')
        : (exercise.incorrect_feedback || 'Not quite. Review the explanation and try again.');
      await put('exerciseAttempts', {
        exerciseId: exercise.id,
        slug: exercise.slug,
        correct: result.correct,
        selected,
        nextReviewAt: Date.now() + (result.correct ? 3 * core.DAY_MS : 10 * 60_000),
        updatedAt: Date.now(),
      });
    });
  });

  document.querySelectorAll('[data-bookmark]').forEach((button) => {
    const slug = button.dataset.termSlug;
    if (!slug) return;
    button.addEventListener('click', async () => {
      const selected = button.getAttribute('aria-pressed') !== 'true';
      button.setAttribute('aria-pressed', String(selected));
      await put('bookmarks', { id: slug, slug, selected, updatedAt: Date.now() });
    });
  });

  const currentTerm = document.querySelector('[data-term-page]')?.dataset.termSlug;
  if (currentTerm) put('recentViews', { id: currentTerm, slug: currentTerm, updatedAt: Date.now() });

  document.querySelectorAll('[data-copy]').forEach((button) => {
    if (button.dataset.copyBound === 'true') return;
    button.dataset.copyBound = 'true';
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(button.dataset.copy || ''); button.dataset.copied = 'true'; }
      catch { button.dataset.copied = 'false'; }
    });
  });

  const practiceRoot = document.querySelector('[data-practice-root]');
  if (practiceRoot) {
    const status = practiceRoot.querySelector('[data-practice-status]');
    const card = practiceRoot.querySelector('[data-practice-card]');
    const scopeSelect = practiceRoot.querySelector('[data-practice-scope]');
    let queue = [];
    let position = 0;
    const renderPractice = () => {
      const item = queue[position];
      if (!item) { card.innerHTML = ''; status.textContent = 'Practice complete.'; return; }
      status.textContent = `${position + 1} / ${queue.length}`;
      card.innerHTML = `<h2>${escapeText(item.title)}</h2><p>${escapeText(item.question)}</p><a class="button-secondary" href="${escapeText(item.url)}">Open exercise</a><button type="button" data-practice-next>Next</button>`;
      card.querySelector('[data-practice-next]').addEventListener('click', () => { position += 1; renderPractice(); });
    };
    const loadPractice = async () => {
      const response = await fetch(root.dataset.exerciseIndex || assetUrl(`exercises.${locale}.json`));
      const exercises = await response.json();
      const attempts = await getAll('exerciseAttempts');
      const scopeValue = scopeSelect?.value || 'all';
      const scope = scopeValue.startsWith('domain:') ? { domain: scopeValue.slice(7) } : {};
      queue = core.buildPracticeQueue(exercises, attempts, scope, Date.now());
      position = 0;
      renderPractice();
    };
    scopeSelect?.addEventListener('change', loadPractice);
    loadPractice().catch((error) => { console.error(error); status.textContent = 'Practice data is unavailable.'; });
  }

  const exportButton = document.querySelector('[data-export-local]');
  exportButton?.addEventListener('click', async () => {
    const payload = { schemaVersion: 2 };
    for (const store of stores) payload[store] = await getAll(store);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'vibe-terms-local-data.json';
    link.click();
    URL.revokeObjectURL(link.href);
  });

  document.querySelector('[data-import-local]')?.addEventListener('change', async (event) => {
    const file = event.currentTarget.files?.[0];
    if (!file) return;
    let payload;
    try { payload = JSON.parse(await file.text()); }
    catch { event.currentTarget.setCustomValidity('Invalid JSON file.'); event.currentTarget.reportValidity(); return; }
    const valid = payload?.schemaVersion === 2 && stores.every((store) => Array.isArray(payload[store]));
    if (!valid) { event.currentTarget.setCustomValidity('This is not a Vibe Terms schema v2 export.'); event.currentTarget.reportValidity(); return; }
    event.currentTarget.setCustomValidity('');
    for (const store of stores) {
      const current = await getAll(store);
      const idKey = store === 'termProgress' ? 'slug' : store === 'exerciseAttempts' ? 'exerciseId' : store === 'pathProgress' ? 'pathId' : 'id';
      const byId = new Map(current.map((row) => [row[idKey], row]));
      for (const row of payload[store]) {
        if (!row || typeof row !== 'object' || !row[idKey]) continue;
        const previous = byId.get(row[idKey]);
        if (!previous || Number(row.updatedAt || 0) >= Number(previous.updatedAt || 0)) await put(store, row);
      }
    }
    location.reload();
  });

  document.querySelector('[data-clear-local]')?.addEventListener('click', async (event) => {
    const button = event.currentTarget;
    if (button.dataset.confirm !== 'true') { button.dataset.confirm = 'true'; button.textContent = button.dataset.confirmLabel || 'Confirm clear'; return; }
    await new Promise((resolve) => {
      const request = indexedDB.deleteDatabase(databaseName);
      request.onsuccess = request.onerror = request.onblocked = resolve;
    });
    try { localStorage.removeItem(localStateKey); localStorage.removeItem('vibe-terms-progress-v1'); } catch { /* ignored */ }
    location.reload();
  });
})();
