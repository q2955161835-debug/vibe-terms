const test = require('node:test');
const assert = require('node:assert/strict');

const {
  buildDailyQueue,
  buildPracticeQueue,
  clampDailyCount,
  gradeExercise,
  groupSearchResults,
  migrateLocalStateV1,
  normalizeSearchText,
  scheduleReview,
  scoreSearchDocument,
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

test('groups exact term matches ahead of topics and paths', () => {
  const docs = [
    { type: 'path', title: 'Build an API', canonical_name: '', aliases: [], summary: 'API project' },
    { type: 'term', title: 'API', canonical_name: 'Application Programming Interface', aliases: ['接口'], summary: 'contract' },
    { type: 'topic', title: 'Backend APIs', canonical_name: '', aliases: [], summary: 'HTTP endpoints' },
  ];
  const groups = groupSearchResults(docs, 'API', 8);
  assert.equal(groups.term[0].title, 'API');
  assert.equal(groups.path.length, 1);
  assert.equal(groups.topic.length, 1);
  assert.ok(scoreSearchDocument(groups.term[0], 'API') > scoreSearchDocument(groups.path[0], 'API'));
});

test('grades by stable option id and retains explanations', () => {
  const exercise = {
    id: 'state-save-result',
    type: 'single-choice',
    answer: 'after-success',
    explanations: { 'after-success': 'Correct', 'before-response': 'The request may fail' },
  };
  const result = gradeExercise(exercise, ['after-success']);
  assert.equal(result.correct, true);
  assert.equal(result.explanations['before-response'], 'The request may fail');
});

test('practice queue prioritizes wrong and due attempts within scope', () => {
  const now = 1_000;
  const exercises = [
    { id: 'new', slug: 'new', domain: 'ai-vibe' },
    { id: 'wrong', slug: 'wrong', domain: 'ai-vibe' },
    { id: 'later', slug: 'later', domain: 'web-network' },
  ];
  const attempts = [
    { exerciseId: 'wrong', correct: false, nextReviewAt: 900 },
    { exerciseId: 'later', correct: true, nextReviewAt: 5_000 },
  ];
  assert.deepEqual(
    buildPracticeQueue(exercises, attempts, { domain: 'ai-vibe' }, now).map((item) => item.id),
    ['wrong', 'new'],
  );
});

test('v1 migration is idempotent', () => {
  const rows = [{ slug: 'api', rating: 'mastered', updatedAt: 100 }];
  const once = migrateLocalStateV1(rows, 200);
  assert.deepEqual(migrateLocalStateV1(once, 200), once);
  assert.equal(once.schemaVersion, 2);
  assert.equal(once.termProgress[0].slug, 'api');
});
