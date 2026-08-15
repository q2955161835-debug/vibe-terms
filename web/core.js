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
    clampDailyCount,
    localDateKey,
    normalizeSearchText,
    scheduleReview,
    scoreTerm,
  };
});
