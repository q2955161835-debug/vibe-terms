(function attachVibeExamples(globalScope, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (globalScope) globalScope.VibeExamples = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function createVibeExamples() {
  'use strict';

  function renderStateExample(root) {
    const controls = Array.from(root.querySelectorAll('[data-example-control]'));
    const states = Array.from(root.querySelectorAll('[data-example-state]'));
    if (!states.length) return;

    const activate = (stateId) => {
      controls.forEach((control) => {
        const active = control.dataset.exampleControl === stateId;
        control.setAttribute('aria-pressed', String(active));
        control.classList.toggle('is-active', active);
      });
      states.forEach((state) => {
        const active = state.dataset.exampleState === stateId;
        state.hidden = false;
        state.classList.toggle('is-active', active);
        state.setAttribute('aria-pressed', String(active));
        if (active) state.setAttribute('aria-current', 'step');
        else state.removeAttribute('aria-current');
      });
    };

    controls.forEach((control) => {
      control.addEventListener('click', () => activate(control.dataset.exampleControl));
    });
    states.forEach((state) => {
      state.addEventListener('click', () => activate(state.dataset.exampleState));
    });
    activate(
      controls.find((control) => control.getAttribute('aria-pressed') === 'true')?.dataset.exampleControl ||
        states.find((state) => state.getAttribute('aria-pressed') === 'true')?.dataset.exampleState ||
        controls[0]?.dataset.exampleControl ||
        states[0].dataset.exampleState,
    );
  }

  const registry = new Map(
    [
      'prompt-constraint-builder',
      'context-window-budget',
      'agent-tool-loop',
      'tool-calling-boundary',
      'retrieval-pipeline',
      'hallucination-evidence',
      'html-structure',
      'css-cascade',
      'dom-update',
      'component-reuse',
      'form-save-state',
      'responsive-breakpoints',
      'accessible-control',
      'api-request-response',
      'request-lifecycle',
      'http-status-outcomes',
      'database-write-read',
      'authentication-authorization',
      'git-working-tree',
      'testing-evidence',
    ].map((id) => [id, Object.freeze({ id, render: renderStateExample })]),
  );

  function has(id) {
    return registry.has(String(id));
  }

  function get(id) {
    return registry.get(String(id));
  }

  function ids() {
    return [...registry.keys()];
  }

  function mount(root, definition) {
    if (!root) return false;
    const id = String(definition?.id || root.dataset.exampleId || '');
    const entry = get(id);
    const renderer = entry?.render || renderStateExample;
    if (!entry && !root.querySelector('[data-example-stage-trigger]')) return false;
    renderer(root, definition || {});
    return true;
  }

  return { get, has, ids, mount };
});
