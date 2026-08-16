const test = require('node:test');
const assert = require('node:assert/strict');

const examples = require('../../web/examples.js');

test('example registry exposes only fixed identifiers', () => {
  assert.equal(examples.has('form-save-state'), true);
  assert.equal(examples.has('api-request-response'), true);
  assert.equal(examples.has('user-supplied-script'), false);
  assert.equal(examples.ids().length, 20);
});

test('example definitions never compile content as executable code', () => {
  for (const id of examples.ids()) {
    const definition = examples.get(id);
    assert.equal(typeof definition.render, 'function');
    assert.equal(Object.hasOwn(definition, 'script'), false);
  }
});
