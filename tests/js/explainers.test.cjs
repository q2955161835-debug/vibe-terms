const test = require('node:test');
const assert = require('node:assert/strict');

const { mount, mountAll } = require('../../web/explainers.js');

class FixtureElement {
  constructor({ attributes = {}, classes = [], textContent = '', tagName = 'div' } = {}) {
    this.attributes = new Map(Object.entries(attributes));
    this.dataset = Object.fromEntries(
      Object.entries(attributes)
        .filter(([name]) => name.startsWith('data-'))
        .map(([name, value]) => [
          name.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase()),
          value,
        ]),
    );
    this.children = [];
    this.hidden = false;
    this.tagName = tagName;
    this.focusCount = 0;
    this.textContent = textContent;
    this.listeners = new Map();
    this.classList = {
      values: new Set(classes),
      add: (...names) => names.forEach((name) => this.classList.values.add(name)),
      remove: (...names) => names.forEach((name) => this.classList.values.delete(name)),
      toggle: (name, force) => {
        const enabled = force === undefined ? !this.classList.values.has(name) : Boolean(force);
        if (enabled) this.classList.values.add(name);
        else this.classList.values.delete(name);
        return enabled;
      },
      contains: (name) => this.classList.values.has(name),
    };
  }

  append(...children) {
    this.children.push(...children);
    return this;
  }

  setAttribute(name, value) {
    const stringValue = String(value);
    this.attributes.set(name, stringValue);
    if (name.startsWith('data-')) {
      this.dataset[name.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = stringValue;
    }
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  removeAttribute(name) {
    this.attributes.delete(name);
    if (name.startsWith('data-')) {
      delete this.dataset[name.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())];
    }
  }

  addEventListener(type, listener) {
    this.listeners.set(type, [...(this.listeners.get(type) || []), listener]);
  }

  dispatchEvent(event) {
    const dispatched = event;
    dispatched.target = this;
    for (const listener of this.listeners.get(dispatched.type) || []) listener(dispatched);
    return !dispatched.defaultPrevented;
  }

  click() {
    this.dispatchEvent({ type: 'click', preventDefault() { this.defaultPrevented = true; } });
  }

  focus() {
    this.focusCount += 1;
    document.activeElement = this;
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  querySelectorAll(selector) {
    return this.descendants().filter((element) => matches(element, selector));
  }

  descendants() {
    return this.children.flatMap((child) => [child, ...child.descendants()]);
  }
}

function matches(element, selector) {
  if (selector.startsWith('.')) return element.classList.contains(selector.slice(1));
  if (/^[a-z]+$/.test(selector)) return element.tagName === selector;
  const attribute = /^\[([^=\]]+)(?:="([^"]*)")?\]$/.exec(selector);
  return Boolean(attribute) && element.getAttribute(attribute[1]) !== null &&
    (attribute[2] === undefined || element.getAttribute(attribute[1]) === attribute[2]);
}

function key(name) {
  return {
    type: 'keydown',
    key: name,
    preventDefault() { this.defaultPrevented = true; },
  };
}

function makeExplainerFixture(stateIds) {
  const root = new FixtureElement({ attributes: { 'data-visual-explainer': '' } });
  const controls = new FixtureElement({ classes: ['visual-state-controls'] });
  const conclusion = new FixtureElement({ attributes: { 'data-explainer-conclusion': '' } });
  const transcript = new FixtureElement({ classes: ['visual-transcript'] });
  const states = stateIds.map((id, index) => new FixtureElement({
    attributes: {
      'data-explainer-state': id,
      'data-explainer-conclusion': `${id} conclusion`,
      'aria-hidden': 'true',
    },
  }).append(
    ...['primary-rule', 'computed-value'].map((nodeId) => new FixtureElement({
      attributes: { 'data-explainer-state-focus': index === 0 ? nodeId : nodeId === 'primary-rule' ? 'override-rule' : nodeId },
    })),
    new FixtureElement({
      attributes: { 'data-explainer-state-value-for': 'computed-value' },
      textContent: `#${index}0${index}0${index}0`,
    }),
  ));
  const nodes = [
    ['primary-rule', '.primary { color: blue; }'],
    ['override-rule', '.primary { color: pink; }'],
    ['computed-value', '#000000'],
  ].map(([id, value]) => new FixtureElement({
    attributes: { 'data-explainer-node': id },
    classes: ['visual-node'],
  }).append(new FixtureElement({ tagName: 'code', textContent: value })));

  root.append(
    controls.append(...stateIds.map((id, index) => new FixtureElement({
      attributes: {
        'data-explainer-state-control': id,
        'aria-pressed': String(index === 0),
      },
      textContent: id,
    }))),
    conclusion,
    ...nodes,
    ...states,
    transcript.append(...stateIds.map((id) => new FixtureElement({
      classes: ['visual-transcript-item'],
      textContent: `${id} transcript`,
    }))),
  );
  return root;
}

global.document = { activeElement: null };

test('mount activates one state and preserves the transcript', () => {
  const root = makeExplainerFixture(['base', 'override', 'fixed']);
  assert.equal(mount(root), true);
  root.querySelector('[data-explainer-state-control="override"]').click();
  assert.equal(root.querySelector('[aria-pressed="true"]').dataset.explainerStateControl, 'override');
  assert.equal(root.querySelector('[data-explainer-state="override"]').getAttribute('aria-current'), 'step');
  assert.equal(root.querySelector('[data-explainer-state="base"]').hidden, true);
  assert.equal(root.querySelector('[data-explainer-conclusion]').textContent, 'override conclusion');
  assert.equal(root.querySelectorAll('.visual-transcript-item').length, 3);
});

test('mount applies producer state metadata to the unique static canvas', () => {
  const root = makeExplainerFixture(['base', 'override']);
  assert.equal(mount(root), true);
  root.querySelector('[data-explainer-state-control="override"]').click();

  assert.equal(root.querySelector('[data-explainer-state="override"]').hidden, true);
  assert.equal(root.querySelector('[data-explainer-state="override"]').getAttribute('aria-current'), 'step');
  assert.equal(root.querySelector('[data-explainer-node="primary-rule"]').classList.contains('is-active'), false);
  assert.equal(root.querySelector('[data-explainer-node="override-rule"]').classList.contains('is-active'), true);
  assert.equal(
    root.querySelector('[data-explainer-node="computed-value"]').querySelector('code').textContent,
    '#101010',
  );
  assert.equal(root.querySelector('[data-explainer-conclusion]').textContent, 'override conclusion');
  assert.equal(root.querySelectorAll('.visual-transcript-item').length, 2);
});

test('ArrowRight and End move between state buttons without leaving the explainer', () => {
  const root = makeExplainerFixture(['one', 'two', 'three']);
  mount(root);
  root.querySelector('[data-explainer-state-control="one"]').dispatchEvent(key('ArrowRight'));
  assert.equal(document.activeElement.dataset.explainerStateControl, 'two');
  document.activeElement.dispatchEvent(key('End'));
  assert.equal(document.activeElement.dataset.explainerStateControl, 'three');
  assert.equal(root.querySelector('[aria-pressed="true"]').dataset.explainerStateControl, 'three');
});

test('mount and mountAll do not duplicate state-control listeners', () => {
  const root = makeExplainerFixture(['one', 'two']);
  assert.equal(mount(root), true);
  assert.equal(mount(root), true);
  root.querySelector('[data-explainer-state-control="one"]').dispatchEvent(key('ArrowRight'));
  assert.equal(root.querySelector('[data-explainer-state-control="two"]').focusCount, 1);

  const secondRoot = makeExplainerFixture(['one', 'two']);
  const fixtureDocument = {
    querySelectorAll(selector) {
      return selector === '[data-visual-explainer]' ? [secondRoot] : [];
    },
  };
  assert.equal(mountAll(fixtureDocument), 1);
  assert.equal(mountAll(fixtureDocument), 1);
  secondRoot.querySelector('[data-explainer-state-control="one"]').dispatchEvent(key('ArrowRight'));
  assert.equal(secondRoot.querySelector('[data-explainer-state-control="two"]').focusCount, 1);
});
