(function attachVibeExplainers(globalScope, factory) {
  const api = factory(globalScope);
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (globalScope) globalScope.VibeExplainers = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function createVibeExplainers(globalScope) {
  'use strict';

  const CONTROL_SELECTOR = '[data-explainer-state-control]';
  const STATE_SELECTOR = '[data-explainer-state]';
  const CONCLUSION_SELECTOR = '[data-explainer-conclusion]';
  const NAVIGATION_KEYS = new Set(['ArrowLeft', 'ArrowRight', 'Home', 'End']);

  function stateId(element, attribute) {
    return element?.dataset?.[attribute] || '';
  }

  function stateConclusion(state) {
    const direct = state?.dataset?.explainerConclusion;
    if (direct) return direct;
    return state?.querySelector?.(CONCLUSION_SELECTOR)?.textContent || '';
  }

  function mount(root) {
    if (!root || typeof root.querySelectorAll !== 'function') return false;

    const controls = Array.from(root.querySelectorAll(CONTROL_SELECTOR));
    const states = Array.from(root.querySelectorAll(STATE_SELECTOR));
    if (!controls.length && !states.length) return false;

    const stateIds = new Set(states.map((state) => stateId(state, 'explainerState')));
    const availableControls = controls.filter((control) =>
      stateIds.has(stateId(control, 'explainerStateControl')),
    );
    const conclusions = Array.from(root.querySelectorAll(CONCLUSION_SELECTOR));
    const conclusion = conclusions.find((item) => !stateId(item, 'explainerState'));

    function activate(nextStateId) {
      if (!stateIds.has(nextStateId)) return false;

      availableControls.forEach((control) => {
        const active = stateId(control, 'explainerStateControl') === nextStateId;
        control.setAttribute('aria-pressed', String(active));
        control.classList.toggle('is-active', active);
      });
      states.forEach((state) => {
        const active = stateId(state, 'explainerState') === nextStateId;
        state.hidden = !active;
        state.classList.toggle('is-active', active);
        if (active) state.setAttribute('aria-current', 'step');
        else state.removeAttribute('aria-current');
      });

      if (conclusion) {
        const activeState = states.find((state) => stateId(state, 'explainerState') === nextStateId);
        const nextConclusion = stateConclusion(activeState);
        if (nextConclusion) conclusion.textContent = nextConclusion;
      }
      return true;
    }

    availableControls.forEach((control, index) => {
      control.addEventListener('click', () => activate(stateId(control, 'explainerStateControl')));
      control.addEventListener('keydown', (event) => {
        if (!NAVIGATION_KEYS.has(event.key)) return;
        event.preventDefault();
        let nextIndex = index;
        if (event.key === 'ArrowLeft') nextIndex = (index - 1 + availableControls.length) % availableControls.length;
        if (event.key === 'ArrowRight') nextIndex = (index + 1) % availableControls.length;
        if (event.key === 'Home') nextIndex = 0;
        if (event.key === 'End') nextIndex = availableControls.length - 1;
        const nextControl = availableControls[nextIndex];
        activate(stateId(nextControl, 'explainerStateControl'));
        nextControl.focus();
      });
    });

    const selected = availableControls.find((control) => control.getAttribute('aria-pressed') === 'true');
    const current = states.find((state) => state.getAttribute('aria-current') === 'step');
    const initial = stateId(selected, 'explainerStateControl') ||
      stateId(current, 'explainerState') || stateId(states[0], 'explainerState');
    return activate(initial);
  }

  function mountAll(root) {
    if (!root || typeof root.querySelectorAll !== 'function') return 0;
    const roots = Array.from(root.querySelectorAll('[data-visual-explainer]'));
    return roots.reduce((mounted, explainer) => mounted + Number(mount(explainer)), 0);
  }

  const documentRef = globalScope && globalScope.document;
  if (documentRef?.addEventListener) {
    documentRef.addEventListener('DOMContentLoaded', () => mountAll(documentRef));
  }

  return { mount, mountAll };
});
