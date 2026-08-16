(function attachVibeExplainers(globalScope, factory) {
  const api = factory(globalScope);
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (globalScope) globalScope.VibeExplainers = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function createVibeExplainers(globalScope) {
  'use strict';

  const CONTROL_SELECTOR = '[data-explainer-state-control]';
  const STATE_SELECTOR = '[data-explainer-state]';
  const CONCLUSION_SELECTOR = '[data-explainer-conclusion]';
  const NODE_SELECTOR = '[data-explainer-node]';
  const FOCUS_SELECTOR = '[data-explainer-state-focus]';
  const VALUE_SELECTOR = '[data-explainer-state-value-for]';
  const NAVIGATION_KEYS = new Set(['ArrowLeft', 'ArrowRight', 'Home', 'End']);
  const mountedRoots = new WeakSet();

  function stateId(element, attribute) {
    return element?.dataset?.[attribute] || '';
  }

  function stateFocus(state) {
    return new Set(
      Array.from(state.querySelectorAll(FOCUS_SELECTOR)).map((item) =>
        stateId(item, 'explainerStateFocus'),
      ),
    );
  }

  function stateValues(state) {
    return new Map(
      Array.from(state.querySelectorAll(VALUE_SELECTOR)).map((item) => [
        stateId(item, 'explainerStateValueFor'),
        item.textContent,
      ]),
    );
  }

  function mount(root) {
    if (!root || typeof root.querySelectorAll !== 'function') return false;
    if (mountedRoots.has(root)) return true;

    const controls = Array.from(root.querySelectorAll(CONTROL_SELECTOR));
    const states = Array.from(root.querySelectorAll(STATE_SELECTOR));
    if (!controls.length && !states.length) return false;

    const stateIds = new Set(states.map((state) => stateId(state, 'explainerState')));
    const availableControls = controls.filter((control) =>
      stateIds.has(stateId(control, 'explainerStateControl')),
    );
    const nodes = Array.from(root.querySelectorAll(NODE_SELECTOR));
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
        state.hidden = true;
        state.classList.toggle('is-active', active);
        if (active) state.setAttribute('aria-current', 'step');
        else state.removeAttribute('aria-current');
      });

      const activeState = states.find((state) => stateId(state, 'explainerState') === nextStateId);
      const focus = stateFocus(activeState);
      const values = stateValues(activeState);
      nodes.forEach((node) => {
        const nodeId = stateId(node, 'explainerNode');
        node.classList.toggle('is-active', focus.has(nodeId));
        const value = values.get(nodeId);
        const code = node.querySelector('code');
        if (value !== undefined && code) code.textContent = value;
      });

      if (conclusion && activeState?.dataset?.explainerConclusion) {
        conclusion.textContent = activeState.dataset.explainerConclusion;
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
    const mounted = activate(initial);
    if (mounted) mountedRoots.add(root);
    return mounted;
  }

  function mountAll(root) {
    if (!root || typeof root.querySelectorAll !== 'function') return 0;
    const roots = Array.from(root.querySelectorAll('[data-visual-explainer]'));
    if (root.getAttribute?.('data-visual-explainer') != null) roots.unshift(root);
    return roots.reduce((mounted, explainer) => mounted + Number(mount(explainer)), 0);
  }

  const documentRef = globalScope && globalScope.document;
  if (documentRef?.addEventListener) {
    documentRef.addEventListener('DOMContentLoaded', () => mountAll(documentRef));
  }

  return { mount, mountAll };
});
