(function attachVibeCore(globalScope, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
  if (globalScope) {
    globalScope.VibeCore = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function createVibeCore() {
  'use strict';

  const DAY_MS = 86_400_000;
  const MINUTE_MS = 60_000;
  const DEFAULT_DAILY_COUNT = 3;

  function normalizeSearchText(value) {
    return String(value ?? '')
      .toLocaleLowerCase()
      .normalize('NFKC')
      .replace(/[\s_-]+/g, ' ')
      .trim();
  }

  function scoreTerm(term, rawQuery) {
    const query = normalizeSearchText(rawQuery);
    if (!query) return 0;

    const title = normalizeSearchText(term.title);
    const canonicalName = normalizeSearchText(term.canonical_name);
    const aliases = Array.isArray(term.aliases)
      ? term.aliases.map(normalizeSearchText)
      : [];
    const definition = normalizeSearchText(term.short_definition);

    if (title === query || canonicalName === query) return 100;
    if (aliases.some((alias) => alias === query)) return 92;
    if (title.startsWith(query) || canonicalName.startsWith(query)) return 82;
    if (aliases.some((alias) => alias.startsWith(query))) return 76;
    if (
      title.includes(query) ||
      canonicalName.includes(query) ||
      aliases.some((alias) => alias.includes(query))
    ) {
      return 64;
    }
    if (definition.includes(query)) return 32;
    return 0;
  }

  function scoreSearchDocument(document, rawQuery) {
    const query = normalizeSearchText(rawQuery);
    if (!query) return 0;

    const title = normalizeSearchText(document?.title);
    const canonicalName = normalizeSearchText(document?.canonical_name);
    const aliases = Array.isArray(document?.aliases)
      ? document.aliases.map(normalizeSearchText)
      : [];
    const summary = normalizeSearchText(
      [document?.summary, document?.short_definition, document?.user_phrase]
        .filter(Boolean)
        .join(' '),
    );
    const typeBoost = document?.type === 'term' ? 8 : document?.type === 'topic' ? 4 : 0;

    if (title === query || canonicalName === query) return 120 + typeBoost;
    if (aliases.includes(query)) return 110 + typeBoost;
    if (title.startsWith(query) || canonicalName.startsWith(query)) return 90 + typeBoost;
    if (aliases.some((alias) => alias.startsWith(query))) return 84 + typeBoost;
    if (
      title.includes(query) ||
      canonicalName.includes(query) ||
      aliases.some((alias) => alias.includes(query))
    ) return 68 + typeBoost;
    if (summary.includes(query)) return 32 + typeBoost;
    return 0;
  }

  function groupSearchResults(documents, query, limit = 8) {
    const groups = { term: [], topic: [], path: [] };
    const ranked = (Array.isArray(documents) ? documents : [])
      .map((document) => ({ document, score: scoreSearchDocument(document, query) }))
      .filter(({ document, score }) => score > 0 && groups[document.type])
      .sort((left, right) =>
        right.score - left.score ||
        String(left.document.title).localeCompare(String(right.document.title)),
      );

    let used = 0;
    for (const { document } of ranked) {
      if (used >= Math.max(1, Number(limit) || 8)) break;
      groups[document.type].push(document);
      used += 1;
    }
    return groups;
  }

  function gradeExercise(exercise, selectedIds) {
    const selected = [...new Set((Array.isArray(selectedIds) ? selectedIds : []).map(String))].sort();
    const answer = (Array.isArray(exercise?.answer) ? exercise.answer : [exercise?.answer])
      .filter((value) => value !== undefined && value !== null)
      .map(String)
      .sort();
    return {
      correct: selected.length === answer.length && selected.every((value, index) => value === answer[index]),
      selected,
      answer,
      explanations: { ...(exercise?.explanations || {}) },
    };
  }

  function buildPracticeQueue(exercises, attempts, scope = {}, now = Date.now()) {
    const byId = new Map((attempts || []).map((attempt) => [attempt.exerciseId || attempt.id, attempt]));
    const scoped = (exercises || []).filter((exercise) => {
      if (scope.domain && exercise.domain !== scope.domain) return false;
      if (scope.path && !(exercise.paths || []).includes(scope.path)) return false;
      if (scope.bookmarks && !(scope.bookmarks || []).includes(exercise.slug)) return false;
      return true;
    });
    return scoped.sort((left, right) => {
      const leftAttempt = byId.get(left.id);
      const rightAttempt = byId.get(right.id);
      const priority = (attempt) => {
        if (!attempt) return 2;
        if (attempt.correct === false) return 0;
        if (Number(attempt.nextReviewAt) <= now) return 1;
        return 3;
      };
      return priority(leftAttempt) - priority(rightAttempt) ||
        Number(leftAttempt?.nextReviewAt || 0) - Number(rightAttempt?.nextReviewAt || 0) ||
        String(left.id).localeCompare(String(right.id));
    });
  }

  function migrateLocalStateV1(input, now = Date.now()) {
    if (input && !Array.isArray(input) && input.schemaVersion === 2) {
      return {
        schemaVersion: 2,
        termProgress: Array.isArray(input.termProgress) ? input.termProgress.map((row) => ({ ...row })) : [],
        exerciseAttempts: Array.isArray(input.exerciseAttempts) ? input.exerciseAttempts.map((row) => ({ ...row })) : [],
        pathProgress: Array.isArray(input.pathProgress) ? input.pathProgress.map((row) => ({ ...row })) : [],
        bookmarks: Array.isArray(input.bookmarks) ? [...input.bookmarks] : [],
        recentViews: Array.isArray(input.recentViews) ? [...input.recentViews] : [],
      };
    }
    const rows = Array.isArray(input) ? input : [];
    return {
      schemaVersion: 2,
      termProgress: rows.map((row) => ({ ...row, updatedAt: Number(row.updatedAt) || now })),
      exerciseAttempts: [],
      pathProgress: [],
      bookmarks: [],
      recentViews: [],
    };
  }

  function clampDailyCount(value) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return DEFAULT_DAILY_COUNT;
    return Math.min(30, Math.max(1, Math.round(parsed)));
  }

  function localDateKey(value = Date.now()) {
    const date = value instanceof Date ? value : new Date(value);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function nextReviewAt(row) {
    const value = row?.nextReviewAt ?? row?.dueAt;
    return Number.isFinite(value) ? value : Number.POSITIVE_INFINITY;
  }

  function isDue(row, now) {
    if (!row) return false;
    if (row.queued || row.rating === 'queued') return true;
    return nextReviewAt(row) <= now;
  }

  function buildDailyQueue(terms, progressRows, dailyCount, now = Date.now()) {
    const orderedTerms = [...terms].sort(
      (left, right) =>
        (left.learning_order ?? Number.MAX_SAFE_INTEGER) -
          (right.learning_order ?? Number.MAX_SAFE_INTEGER) ||
        String(left.slug).localeCompare(String(right.slug)),
    );
    const rows = progressRows ?? [];
    const progressBySlug = new Map(rows.map((row) => [row.slug, row]));

    const due = orderedTerms
      .filter((term) => isDue(progressBySlug.get(term.slug), now))
      .sort((left, right) => {
        const leftProgress = progressBySlug.get(left.slug);
        const rightProgress = progressBySlug.get(right.slug);
        const leftDue = leftProgress?.queued ? 0 : nextReviewAt(leftProgress);
        const rightDue = rightProgress?.queued ? 0 : nextReviewAt(rightProgress);
        return (
          leftDue - rightDue ||
          (left.learning_order ?? Number.MAX_SAFE_INTEGER) -
            (right.learning_order ?? Number.MAX_SAFE_INTEGER)
        );
      });

    const today = localDateKey(now);
    const introducedToday = rows.filter((row) => row.introducedOn === today).length;
    const remainingNewTerms = Math.max(
      0,
      clampDailyCount(dailyCount) - introducedToday,
    );
    const dueSlugs = new Set(due.map((term) => term.slug));
    const unseen = orderedTerms
      .filter((term) => !progressBySlug.has(term.slug) && !dueSlugs.has(term.slug))
      .slice(0, remainingNewTerms);

    return [...due, ...unseen];
  }

  function scheduleReview(previous, rating, now = Date.now()) {
    if (!['again', 'partial', 'mastered'].includes(rating)) {
      throw new TypeError(`Unsupported learning rating: ${rating}`);
    }

    const reviews = (previous?.reviews ?? 0) + 1;
    const previousInterval = Math.max(0, Number(previous?.intervalDays) || 0);
    let intervalDays = 0;
    let nextReview;

    if (rating === 'again') {
      if (reviews <= 2) {
        nextReview = now + 10 * MINUTE_MS;
      } else {
        intervalDays = 1;
        nextReview = now + DAY_MS;
      }
    } else if (rating === 'partial') {
      intervalDays =
        previousInterval > 0
          ? Math.max(1, Math.round(previousInterval * 1.6))
          : 1;
      nextReview = now + intervalDays * DAY_MS;
    } else {
      intervalDays =
        previousInterval > 0
          ? Math.min(
              365,
              Math.max(previousInterval + 1, Math.round(previousInterval * 2.3)),
            )
          : 3;
      nextReview = now + intervalDays * DAY_MS;
    }

    const today = localDateKey(now);
    return {
      ...(previous ?? {}),
      rating,
      queued: false,
      reviews,
      intervalDays,
      nextReviewAt: nextReview,
      introducedOn: previous?.introducedOn || today,
      dailySessionDate: today,
      updatedAt: now,
      lastReviewedAt: now,
    };
  }

  return {
    DAY_MS,
    buildDailyQueue,
    buildPracticeQueue,
    clampDailyCount,
    gradeExercise,
    groupSearchResults,
    localDateKey,
    migrateLocalStateV1,
    normalizeSearchText,
    scheduleReview,
    scoreSearchDocument,
    scoreTerm,
  };
});
