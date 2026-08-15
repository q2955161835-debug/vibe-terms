const test = require('node:test');
const assert = require('node:assert/strict');

const {
  buildDailyQueue,
  clampDailyCount,
  normalizeSearchText,
  scheduleReview,
  scoreTerm,
} = require('../../web/core.js');

test('normalizes Unicode, separators, and case for multilingual search', () => {
  assert.equal(normalizeSearchText('  Context_Window  '), 'context window');
  assert.equal(normalizeSearchText('ＡＰＩ'), 'api');
});

test('ranks exact title matches above definition-only matches', () => {
  const term = {
    title: 'API',
    canonical_name: 'Application Programming Interface',
    aliases: ['接口'],
    short_definition: 'Software communication contract',
  };
  assert.ok(scoreTerm(term, 'api') > scoreTerm(term, 'contract'));
  assert.ok(scoreTerm(term, '接口') > 0);
});

test('clamps the configurable daily new-term count', () => {
  assert.equal(clampDailyCount(0), 1);
  assert.equal(clampDailyCount('8'), 8);
  assert.equal(clampDailyCount(99), 30);
  assert.equal(clampDailyCount('not-a-number'), 3);
});

test('prioritizes due reviews and limits only unseen new terms', () => {
  const now = Date.parse('2026-08-15T00:00:00Z');
  const terms = [
    { slug: 'a', learning_order: 1 },
    { slug: 'b', learning_order: 2 },
    { slug: 'c', learning_order: 3 },
    { slug: 'd', learning_order: 4 },
  ];
  const progress = [
    { slug: 'b', nextReviewAt: now - 1, queued: false, introducedOn: '2026-08-10' },
    { slug: 'c', nextReviewAt: now + 86_400_000, queued: false, introducedOn: '2026-08-15' },
  ];
  assert.deepEqual(
    buildDailyQueue(terms, progress, 2, now).map((term) => term.slug),
    ['b', 'a'],
  );
});

test('mastered schedules a future review instead of hiding the term forever', () => {
  const now = Date.parse('2026-08-15T00:00:00Z');
  const next = scheduleReview(undefined, 'mastered', now);
  assert.equal(next.rating, 'mastered');
  assert.equal(next.reviews, 1);
  assert.equal(next.intervalDays, 3);
  assert.equal(next.nextReviewAt, now + 3 * 86_400_000);
  assert.equal(next.introducedOn, '2026-08-15');
  assert.equal(next.dailySessionDate, '2026-08-15');

  const later = scheduleReview(next, 'mastered', next.nextReviewAt);
  assert.ok(later.intervalDays > next.intervalDays);
  assert.ok(later.nextReviewAt > next.nextReviewAt);
});


test('does not replenish the daily new-term allowance after a reload', () => {
  const now = Date.parse('2026-08-15T12:00:00Z');
  const terms = [
    { slug: 'a', learning_order: 1 },
    { slug: 'b', learning_order: 2 },
    { slug: 'c', learning_order: 3 },
  ];
  const progress = [
    {
      slug: 'a',
      rating: 'mastered',
      introducedOn: '2026-08-15',
      nextReviewAt: now + 3 * 86_400_000,
    },
  ];
  assert.deepEqual(
    buildDailyQueue(terms, progress, 1, now).map((term) => term.slug),
    [],
  );
});
