# Vibe Terms Vertical Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a portable, deployable vertical prototype that proves the complete dictionary-to-learning flow with 12 canonical terms, eight locale routes, guest-first local learning, optional Supabase authentication and synchronization, and a validated Codex Sites deployment path.

**Architecture:** Public terminology content is loaded from Git-tracked YAML and statically rendered by Astro. React islands provide search, learning, authentication, and synchronization without making public pages depend on Supabase. Domain packages expose typed interfaces; IndexedDB and Supabase are adapters behind those interfaces, so the static dictionary remains usable when cloud services fail.

**Tech Stack:** Node.js 24 in CI with a minimum supported version of 22.12.0, pnpm 11.4.0, Astro 7.1.6, React 19.2.7, TypeScript 5.9.x, Zod 4.x, YAML 2.x, Vitest 4.1.x, Playwright 1.x, Dexie 4.x, `fake-indexeddb`, `ts-fsrs` 5.4.1, Supabase JavaScript 2.x, Supabase CLI, and plain CSS with design tokens.

## Global Constraints

- Supported locales are exactly `en`, `zh-cn`, `zh-tw`, `ja`, `ko`, `de`, `ru`, and `hi`.
- English is the sole canonical authoring locale; all other locale files carry `source_content_version` metadata.
- Git is the sole source of truth for terminology content; Supabase stores user-owned learning data only.
- Public term and category pages must render without Supabase, authentication, or client-side JavaScript.
- Guest browsing and learning must not require an account; structured guest data is stored in IndexedDB.
- UI code must not access IndexedDB or Supabase directly; it consumes repository interfaces from `local-store` and `cloud-sync`.
- Authentication supports email one-time code, Google OAuth, and GitHub OAuth, but providers load only after the user opens sign-in.
- The prototype uses 12 representative canonical terms and all eight locale routes. Non-English prototype copy may remain visibly marked `draft`; production builds include only `published` content.
- Learning feedback exposes only `again`, `partial`, and `mastered`; the scheduler adapter maps these to pinned FSRS grades.
- `mastered` maps to FSRS `Good`, not `Easy`, to avoid granting excessive intervals from one confident answer.
- Every Supabase user-owned table has row-level security. No service-role key is shipped to the browser.
- The build artifact is ordinary static HTML, CSS, JavaScript, and JSON. Codex Sites is the first deployment target, not a runtime dependency.
- Light, dark, and system themes are first-class. All interactive controls must be keyboard reachable with visible focus.
- Source code is Apache-2.0. Editorial content under `content/` is CC BY-SA 4.0.
- No payment, reminder, public profile, leaderboard, website-based public submission, or AI chat feature is included.
- Pin exact dependency versions in `pnpm-lock.yaml`; automated dependency updates must not silently cross major versions.
- Never commit `.env`, Supabase secrets, OAuth client secrets, SMTP credentials, GitHub tokens, or translation-provider keys.

## Scope and Follow-on Plans

This plan implements only the approved **vertical prototype** milestone. It deliberately excludes the local maintainer studio, 100-term alpha corpus, public custom lists, full import/export UI, account deletion workflow, complete reference-site baseline, and 500-term release certification. Those belong in two later plans:

1. `vibe-terms-internal-alpha`: 100 terms, maintainer studio, translation workflow, custom lists, robust import/export, and complete sync semantics.
2. `vibe-terms-public-release`: approximately 500 terms, complete baseline mapping, eight reviewed locales, production operations, migration and rollback documentation, and release certification.

## Planned File Map

```text
vibe-terms/
├── .github/workflows/ci.yml
├── .gitignore
├── .nvmrc
├── AGENTS.md
├── CONTRIBUTING.md
├── LICENSE
├── LICENSE-CONTENT
├── README.md
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
├── tsconfig.base.json
├── vitest.workspace.ts
├── apps/
│   └── web/
│       ├── astro.config.mjs
│       ├── package.json
│       ├── public/
│       │   ├── manifest.webmanifest
│       │   └── robots.txt
│       ├── scripts/generate-service-worker.mjs
│       └── src/
│           ├── components/
│           │   ├── auth/AuthIsland.tsx
│           │   ├── learning/LearningSession.tsx
│           │   ├── search/SearchIsland.tsx
│           │   └── shell/LocalePicker.astro
│           ├── config/locales.ts
│           ├── layouts/BaseLayout.astro
│           ├── lib/content.ts
│           ├── lib/runtime.ts
│           ├── pages/index.astro
│           ├── pages/[locale]/index.astro
│           ├── pages/[locale]/categories/[domain].astro
│           ├── pages/[locale]/learn/index.astro
│           ├── pages/[locale]/login/callback.astro
│           ├── pages/[locale]/terms/[slug].astro
│           ├── scripts/register-service-worker.ts
│           └── styles/global.css
├── content/
│   ├── baselines/vibe-hub.prototype.yaml
│   ├── paths/zero-to-vibe.prototype.yaml
│   ├── taxonomy/domains.yaml
│   ├── taxonomy/lifecycle.yaml
│   └── terms/<slug>/{meta,en,zh-cn,zh-tw,ja,ko,de,ru,hi}.yaml
├── packages/
│   ├── content-schema/src/{diagnostics,index,schemas,types}.ts
│   ├── content-loader/src/{index,load-repository,publication,relationships}.ts
│   ├── search-core/src/{distance,index,normalize,query,types}.ts
│   ├── learning-core/src/{daily-queue,fsrs-adapter,index,statistics,types}.ts
│   ├── local-store/src/{database,export-format,index,repository,types}.ts
│   ├── cloud-sync/src/{index,merge,retry,supabase-repository,types}.ts
│   └── ui/src/{Button,Disclosure,StatusMessage,index}.tsx
├── scripts/
│   ├── build-search-index.ts
│   ├── validate-content.ts
│   └── verify-deployment.mjs
├── supabase/
│   ├── config.toml
│   ├── migrations/202608150001_vertical_prototype.sql
│   └── tests/vertical_prototype_rls.sql
└── tests/e2e/
    ├── accessibility.spec.ts
    ├── guest-learning.spec.ts
    ├── locale-routing.spec.ts
    └── search.spec.ts
```

---

### Task 1: Bootstrap the Monorepo and Quality Commands

**Files:**
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `.nvmrc`
- Create: `.gitignore`
- Create: `tsconfig.base.json`
- Create: `vitest.workspace.ts`
- Create: `AGENTS.md`
- Create: package manifests under `apps/web/package.json` and `packages/*/package.json`
- Test: `packages/content-schema/src/workspace.test.ts`

**Interfaces:**
- Consumes: approved design specification only.
- Produces: workspace package names, root commands, TypeScript baseline, and test runner conventions used by every later task.

- [ ] **Step 1: Create the root package manifest and workspace definition**

Use this exact command surface:

```json
{
  "name": "vibe-terms",
  "private": true,
  "packageManager": "pnpm@11.4.0",
  "engines": {
    "node": ">=22.12.0"
  },
  "scripts": {
    "build": "pnpm -r --if-present build",
    "check": "pnpm lint && pnpm typecheck && pnpm test && pnpm validate:content && pnpm build",
    "dev": "pnpm --filter @vibe-terms/web dev",
    "lint": "pnpm -r --if-present lint",
    "test": "vitest run",
    "test:watch": "vitest",
    "typecheck": "pnpm -r --if-present typecheck",
    "validate:content": "tsx scripts/validate-content.ts"
  },
  "devDependencies": {
    "@types/node": "^24.0.0",
    "cross-env": "^10.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.9.0",
    "vitest": "^4.1.0"
  }
}
```

```yaml
# pnpm-workspace.yaml
packages:
  - apps/*
  - packages/*

minimumReleaseAge: 1440
```

Set `.nvmrc` to `24` and configure `.gitignore` to exclude `node_modules`, `.astro`, `dist`, `.env*` except `.env.example`, Playwright output, Supabase temporary files, and local studio credentials.

- [ ] **Step 2: Create focused workspace package manifests**

Use these exact package names:

```text
@vibe-terms/web
@vibe-terms/content-schema
@vibe-terms/content-loader
@vibe-terms/search-core
@vibe-terms/learning-core
@vibe-terms/local-store
@vibe-terms/cloud-sync
@vibe-terms/ui
```

Every library package must expose only `./src/index.ts` during development and declare `type: module`. Do not create a build orchestrator such as Turborepo; pnpm recursive commands are sufficient for the prototype.

- [ ] **Step 3: Add the failing workspace smoke test**

```ts
// packages/content-schema/src/workspace.test.ts
import { describe, expect, it } from 'vitest';
import rootPackage from '../../../package.json';

const requiredScripts = ['build', 'check', 'lint', 'test', 'typecheck', 'validate:content'];

describe('workspace contract', () => {
  it('pins the package manager and exposes every quality command', () => {
    expect(rootPackage.packageManager).toBe('pnpm@11.4.0');
    for (const script of requiredScripts) {
      expect(rootPackage.scripts).toHaveProperty(script);
    }
  });
});
```

- [ ] **Step 4: Run the test and confirm the bootstrap failure**

Run:

```bash
corepack enable
corepack prepare pnpm@11.4.0 --activate
pnpm install
pnpm test packages/content-schema/src/workspace.test.ts
```

Expected before package manifests and Vitest workspace are complete: FAIL because the workspace cannot resolve all declared projects or the test file is not discovered.

- [ ] **Step 5: Add TypeScript and Vitest workspace configuration**

`tsconfig.base.json` must enable `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`, `resolveJsonModule`, and `moduleResolution: Bundler`. `vitest.workspace.ts` must discover `packages/*/src/**/*.test.ts` and `apps/*/src/**/*.test.ts` in a Node environment by default.

- [ ] **Step 6: Run the root quality commands**

Run:

```bash
pnpm test
pnpm typecheck
```

Expected: PASS with one workspace smoke test and no TypeScript errors.

- [ ] **Step 7: Commit the bootstrap**

```bash
git add package.json pnpm-workspace.yaml pnpm-lock.yaml .nvmrc .gitignore tsconfig.base.json vitest.workspace.ts AGENTS.md apps packages
git commit -m "chore: bootstrap Vibe Terms monorepo"
```

---

### Task 2: Define the Canonical Content Schemas and Diagnostics

**Files:**
- Create: `packages/content-schema/src/types.ts`
- Create: `packages/content-schema/src/schemas.ts`
- Create: `packages/content-schema/src/diagnostics.ts`
- Create: `packages/content-schema/src/index.ts`
- Test: `packages/content-schema/src/schemas.test.ts`

**Interfaces:**
- Consumes: no earlier runtime interface.
- Produces: `LOCALES`, `Locale`, `TermMeta`, `LocaleContent`, `Taxonomy`, `LearningPath`, `Baseline`, `Diagnostic`, `parseTermMeta()`, and `parseLocaleContent()`.

- [ ] **Step 1: Write failing schema tests**

```ts
import { describe, expect, it } from 'vitest';
import { parseLocaleContent, parseTermMeta } from './index';

describe('content schemas', () => {
  it('rejects a non-kebab-case slug', () => {
    expect(() =>
      parseTermMeta({
        id: 'term_authentication',
        slug: 'Authentication',
        canonical_name: 'Authentication',
        acronyms: [],
        aliases: [],
        primary_domain: 'security-and-privacy',
        secondary_domains: [],
        lifecycle_stage: 'connect-data-and-identity',
        difficulty: 'beginner',
        prerequisites: [],
        related_terms: [],
        reference_mappings: [],
        sources: [{ title: 'MDN', url: 'https://developer.mozilla.org/', source_type: 'official-documentation' }],
        content_version: 1
      })
    ).toThrow(/slug/i);
  });

  it('requires exactly three quiz questions', () => {
    expect(() =>
      parseLocaleContent({
        title: 'Authentication',
        short_definition: 'Checks who a user is.',
        analogy: 'Showing an ID card.',
        mechanism: 'A verifier checks submitted credentials against trusted identity data.',
        why_it_matters: 'Without it, private accounts cannot be protected.',
        project_example: 'The learning assistant verifies a learner before loading cloud progress.',
        ai_prompt_example: 'Add optional email OTP sign-in without blocking guest access.',
        common_mistakes: ['Confusing authentication with authorization.'],
        quiz: [],
        publication: { status: 'published' },
        localization: {
          source_locale: 'en',
          source_content_version: 1,
          machine_generated: false,
          reviewed_by: ['maintainer']
        }
      })
    ).toThrow(/quiz/i);
  });
});
```

- [ ] **Step 2: Run the tests and verify failure**

Run:

```bash
pnpm vitest run packages/content-schema/src/schemas.test.ts
```

Expected: FAIL because `parseTermMeta` and `parseLocaleContent` do not exist.

- [ ] **Step 3: Implement locale and metadata schemas**

The exported locale constant must be:

```ts
export const LOCALES = ['en', 'zh-cn', 'zh-tw', 'ja', 'ko', 'de', 'ru', 'hi'] as const;
export type Locale = (typeof LOCALES)[number];
```

Implement Zod 4 schemas with these invariants:

```text
Term ID: /^term_[a-z0-9]+(?:_[a-z0-9]+)*$/
Slug: /^[a-z0-9]+(?:-[a-z0-9]+)*$/
content_version: positive integer
publication.status: missing | draft | reviewed | published | withdrawn
reference relationship: canonical | alias | merged | split | deprecated-name
difficulty: beginner | intermediate | advanced
quiz length: exactly 3
correct_option: integer between 0 and options.length - 1
source URL: HTTPS only
```

`LocaleContent.localization.source_locale` is always `en`. English content must have `machine_generated: false`; non-English content may be machine generated only when publication status is `draft`.

- [ ] **Step 4: Implement structured diagnostics**

```ts
export type DiagnosticSeverity = 'error' | 'warning';

export interface Diagnostic {
  code: string;
  severity: DiagnosticSeverity;
  path: string;
  message: string;
  termId?: string;
  locale?: Locale;
}
```

Do not throw for repository-wide relationship problems. Return diagnostics so CI can report every content issue in one run. Schema parse failures may be converted into diagnostics at the loader boundary.

- [ ] **Step 5: Run schema tests**

Run:

```bash
pnpm vitest run packages/content-schema/src/schemas.test.ts
pnpm typecheck
```

Expected: PASS.

- [ ] **Step 6: Commit the schema package**

```bash
git add packages/content-schema
git commit -m "feat: define terminology content schemas"
```

---

### Task 3: Add the Prototype Taxonomy, Learning Path, and 12-Term Corpus

**Files:**
- Create: `content/taxonomy/domains.yaml`
- Create: `content/taxonomy/lifecycle.yaml`
- Create: `content/paths/zero-to-vibe.prototype.yaml`
- Create: `content/baselines/vibe-hub.prototype.yaml`
- Create: 12 directories under `content/terms/`
- Create: `docs/content/prototype-translation-review.md`
- Test: `packages/content-schema/src/prototype-content.test.ts`

**Interfaces:**
- Consumes: schemas from Task 2.
- Produces: a deterministic 12-term fixture used by loader, search, web, learning, localization, and deployment tests.

- [ ] **Step 1: Write the failing corpus-shape test**

```ts
import { readdir } from 'node:fs/promises';
import { describe, expect, it } from 'vitest';
import { LOCALES } from './index';

const expectedSlugs = [
  'software',
  'vibe-coding',
  'prompt',
  'frontend',
  'backend',
  'api',
  'component',
  'state',
  'database',
  'authentication',
  'git',
  'deployment'
];

describe('prototype corpus', () => {
  it('contains twelve terms and every locale file', async () => {
    const directories = (await readdir('content/terms')).sort();
    expect(directories).toEqual([...expectedSlugs].sort());
    for (const slug of expectedSlugs) {
      const files = await readdir(`content/terms/${slug}`);
      expect(files).toContain('meta.yaml');
      for (const locale of LOCALES) expect(files).toContain(`${locale}.yaml`);
    }
  });
});
```

- [ ] **Step 2: Run the test and verify failure**

Run:

```bash
pnpm vitest run packages/content-schema/src/prototype-content.test.ts
```

Expected: FAIL because `content/terms` does not exist.

- [ ] **Step 3: Create the exact prototype term graph**

Use this metadata table:

| Slug | Canonical name | Primary domain | Lifecycle stage | Prerequisites |
|---|---|---|---|---|
| `software` | Software | computing-and-development-environment | form-an-idea | none |
| `vibe-coding` | Vibe Coding | ai-and-vibe-coding | form-an-idea | software |
| `prompt` | Prompt | ai-and-vibe-coding | define-requirements | vibe-coding |
| `frontend` | Frontend | frontend-development | build-interface-and-logic | software |
| `backend` | Backend | backend-and-apis | build-interface-and-logic | software |
| `api` | API | backend-and-apis | connect-data-and-identity | frontend, backend |
| `component` | Component | frontend-development | build-interface-and-logic | frontend |
| `state` | State | frontend-development | build-interface-and-logic | component |
| `database` | Database | data-and-databases | connect-data-and-identity | backend |
| `authentication` | Authentication | security-and-privacy | connect-data-and-identity | api, database |
| `git` | Git | git-and-collaboration | establish-development-environment | software |
| `deployment` | Deployment | deployment-performance-and-operations | deploy-and-maintain | frontend, backend, git |

The zero-to-Vibe path uses the row order above. The prototype baseline maps the corresponding reference-site names and aliases, including `Auth` to `authentication` and `Deploy` to `deployment`.

- [ ] **Step 4: Create all eight locale files without claiming false review**

For each term:

- `en.yaml` uses `publication.status: published`, `machine_generated: false`, and `reviewed_by: [project-maintainer]`.
- The seven translated files use `publication.status: draft`, `machine_generated: true`, `reviewed_by: []`, and the same `source_content_version` as English.
- Every file contains all teaching fields and exactly three quiz questions.
- Every localized page contains localized title, definition, analogy, mechanism, importance, example, prompt, mistakes, quiz, and explanation. Do not mix English body copy into translated files.
- Draft translations display a visible draft notice in prototype mode and are excluded from production mode until reviewed.

Use these localized titles as the glossary anchor:

| Term | zh-cn | zh-tw | ja | ko | de | ru | hi |
|---|---|---|---|---|---|---|---|
| Software | 软件 | 軟體 | ソフトウェア | 소프트웨어 | Software | Программное обеспечение | सॉफ़्टवेयर |
| Vibe Coding | 氛围编程 | 氛圍編程 | バイブコーディング | 바이브 코딩 | Vibe Coding | Вайб-кодинг | वाइब कोडिंग |
| Prompt | 提示词 | 提示詞 | プロンプト | 프롬프트 | Prompt | Промпт | प्रॉम्प्ट |
| Frontend | 前端 | 前端 | フロントエンド | 프런트엔드 | Frontend | Фронтенд | फ़्रंटएंड |
| Backend | 后端 | 後端 | バックエンド | 백엔드 | Backend | Бэкенд | बैकएंड |
| API | 应用程序接口 | 應用程式介面 | API | API | API | API | API |
| Component | 组件 | 元件 | コンポーネント | 컴포넌트 | Komponente | Компонент | कंपोनेंट |
| State | 状态 | 狀態 | 状態 | 상태 | Zustand | Состояние | स्थिति |
| Database | 数据库 | 資料庫 | データベース | 데이터베이스 | Datenbank | База данных | डेटाबेस |
| Authentication | 身份认证 | 身分驗證 | 認証 | 인증 | Authentifizierung | Аутентификация | प्रमाणीकरण |
| Git | Git | Git | Git | Git | Git | Git | Git |
| Deployment | 部署 | 部署 | デプロイ | 배포 | Bereitstellung | Развертывание | परिनियोजन |

- [ ] **Step 5: Add a translation review checklist**

`docs/content/prototype-translation-review.md` must require reviewers to verify technical meaning, beginner readability, terminology consistency, prompt safety, quiz correctness, punctuation conventions, and absence of untranslated body text before changing a locale from `draft` to `reviewed` or `published`.

- [ ] **Step 6: Run the corpus test**

Run:

```bash
pnpm vitest run packages/content-schema/src/prototype-content.test.ts
```

Expected: PASS with 12 term directories and 96 locale files.

- [ ] **Step 7: Commit prototype content**

```bash
git add content docs/content packages/content-schema/src/prototype-content.test.ts
git commit -m "content: add multilingual prototype corpus"
```

---

### Task 4: Implement Repository Loading, Publication Rules, and Relationship Validation

**Files:**
- Create: `packages/content-loader/src/load-repository.ts`
- Create: `packages/content-loader/src/publication.ts`
- Create: `packages/content-loader/src/relationships.ts`
- Create: `packages/content-loader/src/index.ts`
- Create: `scripts/validate-content.ts`
- Test: `packages/content-loader/src/load-repository.test.ts`
- Test: `packages/content-loader/src/relationships.test.ts`

**Interfaces:**
- Consumes: `TermMeta`, `LocaleContent`, taxonomy, path, and baseline schemas.
- Produces: `loadRepository(root, options)`, `RepositorySnapshot`, `getPublishableTerms(locale, mode)`, and repository diagnostics.

```ts
export interface LoadRepositoryOptions {
  mode: 'prototype' | 'production';
}

export interface LoadedTerm {
  meta: TermMeta;
  locales: Partial<Record<Locale, LocaleContent>>;
}

export interface RepositorySnapshot {
  termsBySlug: ReadonlyMap<string, LoadedTerm>;
  domains: readonly DomainDefinition[];
  lifecycleStages: readonly LifecycleStageDefinition[];
  paths: readonly LearningPath[];
  baseline: Baseline;
  diagnostics: readonly Diagnostic[];
}
```

- [ ] **Step 1: Write failing loader tests**

Test these exact behaviors:

```text
- Loads 12 canonical terms from the repository root.
- Production mode exposes English but excludes draft Chinese for a prototype term.
- Prototype mode exposes the draft Chinese file with `isDraft: true` metadata.
- A missing prerequisite produces diagnostic code `missing-prerequisite`.
- A directed prerequisite cycle produces diagnostic code `prerequisite-cycle`.
- An unmapped baseline entry produces diagnostic code `unmapped-baseline-term`.
- A stale published translation produces a warning, not an error.
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pnpm vitest run packages/content-loader/src
```

Expected: FAIL because loader exports do not exist.

- [ ] **Step 3: Implement YAML loading and schema conversion**

Use `node:fs/promises`, `node:path`, and `yaml`. Sort directory and file names before reading so diagnostics and generated artifacts are deterministic across operating systems.

- [ ] **Step 4: Implement graph validation**

Use depth-first search with `unvisited`, `visiting`, and `visited` states. Report the exact cycle path, for example `frontend -> component -> frontend`, rather than returning a generic graph error.

- [ ] **Step 5: Implement publication filtering**

Rules:

```text
prototype mode: include published, reviewed, and draft; attach visible status metadata
production mode: include only published
withdrawn: never public
missing locale: no route for that locale
stale published locale: route remains public with stale notice
stale reviewed or draft locale: visible only in prototype mode
```

- [ ] **Step 6: Implement the content validation CLI**

`pnpm validate:content` prints diagnostics grouped by severity and exits `1` when any error exists. Warnings do not fail prototype validation. Add `--production` to enforce production publication rules.

- [ ] **Step 7: Run loader tests and validation**

Run:

```bash
pnpm vitest run packages/content-loader/src
pnpm validate:content
```

Expected: PASS; draft locale notices appear as warnings only.

- [ ] **Step 8: Commit the loader**

```bash
git add packages/content-loader scripts/validate-content.ts
git commit -m "feat: load and validate terminology repository"
```

---

### Task 5: Build the Locale-aware Search Engine

**Files:**
- Create: `packages/search-core/src/types.ts`
- Create: `packages/search-core/src/normalize.ts`
- Create: `packages/search-core/src/distance.ts`
- Create: `packages/search-core/src/query.ts`
- Create: `packages/search-core/src/index.ts`
- Create: `scripts/build-search-index.ts`
- Test: `packages/search-core/src/query.test.ts`

**Interfaces:**
- Consumes: publishable term projections from `content-loader`.
- Produces: `SearchDocument`, `SearchIndex`, `buildSearchIndex()`, `search()`, and locale JSON files consumed by the web app.

```ts
export interface SearchDocument {
  termId: string;
  slug: string;
  locale: Locale;
  localizedTitle: string;
  canonicalTitle: string;
  acronyms: string[];
  aliases: string[];
  misspellings: string[];
  shortDefinition: string;
  domainLabels: string[];
  lifecycleLabel: string;
}

export interface SearchResult {
  document: SearchDocument;
  score: number;
  reason: 'localized-exact' | 'canonical-exact' | 'alias-exact' | 'prefix' | 'misspelling' | 'fuzzy-title' | 'definition';
}
```

- [ ] **Step 1: Write failing ranking tests**

Test that:

```text
- `Authentication` ranks authentication first on every locale.
- `身份认证` ranks authentication first in zh-cn.
- `Auth` ranks authentication first through an alias.
- A one-character typo such as `autentication` returns authentication within the first five.
- An exact localized title outranks a definition-only match.
- Empty or punctuation-only queries return an empty array.
```

- [ ] **Step 2: Run the tests and verify failure**

Run:

```bash
pnpm vitest run packages/search-core/src/query.test.ts
```

Expected: FAIL because `search` is undefined.

- [ ] **Step 3: Implement normalization**

Apply Unicode NFKC normalization, locale-aware lowercase conversion, punctuation folding, whitespace collapse, and diacritic removal for matching only. Preserve original display strings.

For `zh-cn`, `zh-tw`, `ja`, and `ko`, generate overlapping 1-, 2-, and 3-character n-grams after punctuation normalization. For `en`, `de`, `ru`, and `hi`, split with `Intl.Segmenter` when available and fall back to Unicode whitespace and punctuation boundaries.

- [ ] **Step 4: Implement deterministic scoring**

Use these base scores:

```text
localized exact: 1000
canonical exact: 950
alias or acronym exact: 900
localized or canonical prefix: 800
curated misspelling exact: 760
fuzzy title: 600 - normalized Damerau-Levenshtein penalty
short-definition token overlap: 300 + overlap ratio * 100
```

Tie-break by shorter title, then canonical title, then slug. Return at most 20 results.

- [ ] **Step 5: Generate one static index per locale**

`tsx scripts/build-search-index.ts --mode prototype --out apps/web/public/search` must generate:

```text
apps/web/public/search/en.json
apps/web/public/search/zh-cn.json
apps/web/public/search/zh-tw.json
apps/web/public/search/ja.json
apps/web/public/search/ko.json
apps/web/public/search/de.json
apps/web/public/search/ru.json
apps/web/public/search/hi.json
```

Include `contentVersion`, `generatedAt`, and sorted documents. The web build must invoke this script before `astro build`.

- [ ] **Step 6: Run search tests and inspect artifact size**

Run:

```bash
pnpm vitest run packages/search-core/src/query.test.ts
pnpm tsx scripts/build-search-index.ts --mode prototype --out /tmp/vibe-search
find /tmp/vibe-search -type f -maxdepth 1 -print -exec wc -c {} \;
```

Expected: all tests pass; each prototype locale index is valid JSON and under 100 KB uncompressed.

- [ ] **Step 7: Commit search core**

```bash
git add packages/search-core scripts/build-search-index.ts
git commit -m "feat: add multilingual static search"
```

---

### Task 6: Build the Astro Shell, Locale Routes, Theme, and Design Tokens

**Files:**
- Create: `apps/web/astro.config.mjs`
- Create: `apps/web/src/config/locales.ts`
- Create: `apps/web/src/layouts/BaseLayout.astro`
- Create: `apps/web/src/styles/global.css`
- Create: `apps/web/src/pages/index.astro`
- Create: `apps/web/src/pages/[locale]/index.astro`
- Create: `apps/web/src/components/shell/LocalePicker.astro`
- Test: `apps/web/src/config/locales.test.ts`

**Interfaces:**
- Consumes: locale constant and repository snapshot.
- Produces: static locale routing, HTML metadata shell, navigation, and theme contract used by all public pages.

- [ ] **Step 1: Write failing locale configuration tests**

```ts
import { describe, expect, it } from 'vitest';
import { getLocaleHref, isLocale, locales } from './locales';

describe('locale routing', () => {
  it('contains exactly the approved locales', () => {
    expect(locales.map((item) => item.code)).toEqual(['en', 'zh-cn', 'zh-tw', 'ja', 'ko', 'de', 'ru', 'hi']);
  });

  it('preserves the canonical term path while switching locale', () => {
    expect(getLocaleHref('/zh-cn/terms/authentication', 'de')).toBe('/de/terms/authentication');
  });

  it('rejects unsupported locale strings', () => {
    expect(isLocale('fr')).toBe(false);
  });
});
```

- [ ] **Step 2: Run the test and verify failure**

Run:

```bash
pnpm vitest run apps/web/src/config/locales.test.ts
```

Expected: FAIL because locale helpers do not exist.

- [ ] **Step 3: Configure Astro for portable static output**

Use `output: 'static'`, React integration, trailing slash policy `never`, site URL from `PUBLIC_SITE_URL` with `https://example.invalid` only during local tests, and Astro 7 CSP configuration. Do not add a hosting adapter.

The web package build command must be:

```json
{
  "scripts": {
    "build": "pnpm run build:prototype",
    "build:prototype": "cross-env CONTENT_MODE=prototype tsx ../../scripts/build-search-index.ts --mode prototype --out public/search && astro build && node scripts/generate-service-worker.mjs",
    "build:production": "cross-env CONTENT_MODE=production tsx ../../scripts/build-search-index.ts --mode production --out public/search && astro build && node scripts/generate-service-worker.mjs",
    "dev": "cross-env CONTENT_MODE=prototype astro dev",
    "preview": "astro preview",
    "typecheck": "astro check"
  }
}
```

Use the root `cross-env` dependency so the same commands work on Windows, macOS, Linux, and CI.

- [ ] **Step 4: Implement theme initialization without a flash**

Before visible content renders, an inline script reads `localStorage['vibe-terms:theme']` and sets `data-theme` to `light`, `dark`, or the current system preference. The theme control persists only `light`, `dark`, or `system`.

- [ ] **Step 5: Implement the base layout and visual tokens**

Use semantic landmarks: skip link, header, navigation, main, and footer. Define CSS custom properties for background, surface, text, muted text, border, focus ring, category accents, spacing, type scale, radius, and shadow. Use system font stacks that support CJK, Cyrillic, Latin, and Devanagari. Do not fetch fonts from third-party origins.

- [ ] **Step 6: Implement the root locale chooser**

`/` must render an accessible locale selection page in static HTML. A small client script may recommend a browser-matching locale but must never force redirect or make the page blank without JavaScript.

- [ ] **Step 7: Run route and build checks**

Run:

```bash
pnpm --filter @vibe-terms/web typecheck
pnpm --filter @vibe-terms/web build
find apps/web/dist -maxdepth 3 -type f | sort | sed -n '1,80p'
```

Expected: `/index.html` plus eight locale home pages build successfully.

- [ ] **Step 8: Commit the web shell**

```bash
git add apps/web
git commit -m "feat: add multilingual Astro application shell"
```

---

### Task 7: Render Homepage, Category Pages, Term Pages, and Search UI

**Files:**
- Create: `apps/web/src/lib/content.ts`
- Create: `apps/web/src/pages/[locale]/categories/[domain].astro`
- Create: `apps/web/src/pages/[locale]/terms/[slug].astro`
- Create: `apps/web/src/components/search/SearchIsland.tsx`
- Create: `packages/ui/src/Button.tsx`
- Create: `packages/ui/src/Disclosure.tsx`
- Create: `packages/ui/src/StatusMessage.tsx`
- Create: `packages/ui/src/index.ts`
- Test: `apps/web/src/lib/content.test.ts`
- Test: `apps/web/src/components/search/SearchIsland.test.tsx`

**Interfaces:**
- Consumes: `RepositorySnapshot`, static search indexes, and locale route helpers.
- Produces: the dictionary-first public browsing flow and reusable accessible UI primitives.

- [ ] **Step 1: Write failing page-projection tests**

Test `getTermPageData(locale, slug, mode)` for:

```text
- English authentication page has canonical and localized title.
- Chinese draft page includes draft notice metadata in prototype mode.
- Production mode returns not-found for an unpublished locale.
- Related and prerequisite links preserve locale.
- Category counts include only routes visible in the selected mode.
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pnpm vitest run apps/web/src/lib/content.test.ts
```

Expected: FAIL because page projection functions do not exist.

- [ ] **Step 3: Implement static path generation**

Use `getStaticPaths()` for every locale, domain, and visible term. Do not query Supabase. A term page must show:

```text
localized title
English canonical name
acronyms and aliases
primary domain and lifecycle stage
difficulty
short definition
analogy
draft or stale notice when applicable
mechanism
why it matters
project example
copyable AI prompt
common mistakes
three-question quiz
prerequisites
related terms
sources
localization status
```

Use native `<details>` and `<summary>` for deeper sections unless a tested custom disclosure is required.

- [ ] **Step 4: Implement the category-exploration homepage**

Render, in order:

```text
search hero
technical-domain card grid
project lifecycle sequence
continue-learning mount point
beginner path entry
recently updated prototype terms
open-source and licensing summary
```

Category cards include localized name, description, count, three representative terms, and a link. When no local learning data exists, omit progress rather than showing a fake zero percent badge.

- [ ] **Step 5: Implement the search island**

The search island loads only the current locale JSON, debounces input by 100 ms, uses `aria-controls` and `aria-activedescendant`, supports Arrow Up, Arrow Down, Enter, and Escape, and provides a non-JavaScript link to the terms index. Display the ranking reason only in development diagnostics, not to ordinary users.

- [ ] **Step 6: Test search interaction**

Use React Testing Library to verify keyboard selection, empty state, network failure state, and that `Auth` opens `/en/terms/authentication`.

- [ ] **Step 7: Build and inspect static output**

Run:

```bash
pnpm vitest run apps/web/src packages/ui/src
pnpm --filter @vibe-terms/web build
```

Expected: term and category pages exist for every prototype-visible locale; English production mode contains 12 public term pages.

- [ ] **Step 8: Commit public dictionary pages**

```bash
git add apps/web packages/ui
git commit -m "feat: render searchable terminology dictionary"
```

---

### Task 8: Implement the FSRS-backed Learning Core

**Files:**
- Create: `packages/learning-core/src/types.ts`
- Create: `packages/learning-core/src/fsrs-adapter.ts`
- Create: `packages/learning-core/src/daily-queue.ts`
- Create: `packages/learning-core/src/statistics.ts`
- Create: `packages/learning-core/src/index.ts`
- Test: `packages/learning-core/src/fsrs-adapter.test.ts`
- Test: `packages/learning-core/src/daily-queue.test.ts`

**Interfaces:**
- Consumes: term IDs, current time supplied by caller, review history, and path order.
- Produces: `LearningScheduler`, `createDailyQueue()`, `recordReview()`, and `deriveLearningStatistics()`.

```ts
export type BeginnerRating = 'again' | 'partial' | 'mastered';

export interface Clock {
  now(): Date;
}

export interface ReviewEvent {
  eventId: string;
  termId: string;
  rating: BeginnerRating;
  reviewedAt: string;
  deviceId: string;
  contentVersion: number;
}

export interface TermLearningState {
  termId: string;
  fsrsCard: unknown;
  dueAt: string;
  lastReviewAt: string | null;
  reviewCount: number;
  lapseCount: number;
  lastRating: BeginnerRating | null;
  contentVersionLastReviewed: number | null;
}
```

- [ ] **Step 1: Write failing scheduler mapping tests**

```ts
import { describe, expect, it } from 'vitest';
import { mapBeginnerRating } from './fsrs-adapter';

describe('beginner rating mapping', () => {
  it('maps the three UI ratings conservatively', () => {
    expect(mapBeginnerRating('again')).toBe(1);
    expect(mapBeginnerRating('partial')).toBe(2);
    expect(mapBeginnerRating('mastered')).toBe(3);
  });
});
```

Use pinned `ts-fsrs` rating values `Again = 1`, `Hard = 2`, and `Good = 3`.

- [ ] **Step 2: Write failing daily queue tests**

Test that overdue reviews come first, then due reviews, then new path terms up to the configured target; duplicate term IDs never appear; and target values outside `1..30` are rejected.

- [ ] **Step 3: Run tests and verify failure**

Run:

```bash
pnpm vitest run packages/learning-core/src
```

Expected: FAIL because scheduler and queue functions do not exist.

- [ ] **Step 4: Implement the FSRS adapter**

Wrap `createEmptyCard()`, `fsrs()`, and `scheduler.next(card, reviewDate, rating)` from `ts-fsrs@5.4.1`. Serialize only documented card fields into local storage. Never call `new Date()` inside the core; use the supplied `Clock` or explicit date parameter.

- [ ] **Step 5: Implement queue and statistics functions**

`createDailyQueue()` accepts due states, path order, already learned IDs, and `dailyNewTermTarget`. Sort by due timestamp and then stable term ID. `deriveLearningStatistics()` returns new terms today, reviews today, due count, recent rating distribution, active-day streak, path completion, and tomorrow due estimate.

- [ ] **Step 6: Run deterministic tests**

Freeze the clock at `2026-08-15T00:00:00.000Z`. Assert event IDs are supplied by the caller, scheduling is repeatable for the same card and timestamp, and no test depends on the machine timezone.

Run:

```bash
pnpm vitest run packages/learning-core/src
```

Expected: PASS.

- [ ] **Step 7: Commit the learning core**

```bash
git add packages/learning-core
git commit -m "feat: add adaptive learning scheduler"
```

---

### Task 9: Implement Local-first Guest Persistence with Dexie

**Files:**
- Create: `packages/local-store/src/types.ts`
- Create: `packages/local-store/src/database.ts`
- Create: `packages/local-store/src/repository.ts`
- Create: `packages/local-store/src/export-format.ts`
- Create: `packages/local-store/src/index.ts`
- Test: `packages/local-store/src/repository.test.ts`

**Interfaces:**
- Consumes: learning-core event and state types.
- Produces: `LocalLearningRepository`, IndexedDB schema version 1, migration boundary, and prototype export validation.

```ts
export interface LocalLearningRepository {
  getSettings(): Promise<ProfileSettings>;
  updateSettings(patch: Partial<ProfileSettings>): Promise<ProfileSettings>;
  listBookmarks(): Promise<BookmarkRecord[]>;
  setBookmark(termId: string, bookmarked: boolean, at: string): Promise<void>;
  listReviewEvents(): Promise<ReviewEvent[]>;
  appendReviewEvent(event: ReviewEvent): Promise<'inserted' | 'duplicate'>;
  getTermStates(): Promise<TermLearningState[]>;
  putTermState(state: TermLearningState): Promise<void>;
  getDailyActivity(date: string): Promise<DailyActivity | null>;
  putDailyActivity(activity: DailyActivity): Promise<void>;
  hasGuestData(): Promise<boolean>;
}
```

- [ ] **Step 1: Write failing repository tests with `fake-indexeddb`**

Test exact behavior:

```text
- Default daily target is 3.
- Daily target rejects 0 and 31.
- Duplicate review event ID returns `duplicate` and creates one row.
- Bookmark removal writes a tombstone rather than deleting history.
- Data survives closing and reopening the Dexie instance.
- `hasGuestData()` is false for defaults only and true after a review or bookmark.
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pnpm vitest run packages/local-store/src/repository.test.ts
```

Expected: FAIL because the database and repository do not exist.

- [ ] **Step 3: Define IndexedDB schema version 1**

Create tables:

```text
profile_settings: key, updatedAt
learning_plans: id, sourceType, sourceId, updatedAt, deletedAt
bookmarks: termId, updatedAt, deletedAt
term_states: termId, dueAt, updatedAt
review_events: eventId, termId, reviewedAt, deviceId
 daily_activity: date, updatedAt
sync_metadata: key, updatedAt
```

Use stable string IDs generated outside the database. Store timestamps as ISO 8601 strings in UTC.

- [ ] **Step 4: Implement local-first repository operations**

All writes use Dexie transactions when more than one table changes. A review operation appends the immutable event, updates term state, and updates daily activity in one transaction.

- [ ] **Step 5: Implement prototype export validation**

Define a versioned JSON envelope:

```ts
export interface LearningExportV1 {
  format: 'vibe-terms-learning-export';
  version: 1;
  exportedAt: string;
  settings: ProfileSettings;
  bookmarks: BookmarkRecord[];
  reviewEvents: ReviewEvent[];
  termStates: TermLearningState[];
  dailyActivity: DailyActivity[];
}
```

The prototype exposes export logic for testing and future UI, but the full import/export screen is deferred to the alpha plan.

- [ ] **Step 6: Run repository tests**

Run:

```bash
pnpm vitest run packages/local-store/src
```

Expected: PASS.

- [ ] **Step 7: Commit local persistence**

```bash
git add packages/local-store
git commit -m "feat: persist guest learning locally"
```

---

### Task 10: Build the Guest Learning Session UI

**Files:**
- Create: `apps/web/src/pages/[locale]/learn/index.astro`
- Create: `apps/web/src/components/learning/LearningSession.tsx`
- Create: `apps/web/src/lib/runtime.ts`
- Test: `apps/web/src/components/learning/LearningSession.test.tsx`

**Interfaces:**
- Consumes: content page projections, `LearningScheduler`, `LocalLearningRepository`, and current locale.
- Produces: complete guest daily session, daily target control, three-button rating flow, and local statistics.

- [ ] **Step 1: Write failing interaction tests**

Verify:

```text
- The first card initially shows title and recall instruction only.
- Reveal displays short definition and analogy.
- Expand displays mechanism, project example, and AI prompt.
- Rating writes one review event and advances exactly once.
- Reload reconstructs the session from local data.
- Daily target accepts 1 and 30, warns above 20, and rejects values outside the range.
- IndexedDB failure leaves the dictionary usable and shows a clear persistence warning.
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pnpm vitest run apps/web/src/components/learning/LearningSession.test.tsx
```

Expected: FAIL because the component does not exist.

- [ ] **Step 3: Implement dependency injection for browser services**

`runtime.ts` creates production adapters lazily in the browser. Tests pass in memory repositories and fixed clocks. Do not instantiate Dexie during Astro server rendering.

- [ ] **Step 4: Implement the four-step learning card**

Use a state machine with states `recall`, `revealed`, `expanded`, and `saving`. Disable rating buttons while saving. Announce state changes through an `aria-live="polite"` region. Keep focus on the next card heading after a rating.

- [ ] **Step 5: Implement local progress and warnings**

Display new terms completed today, reviews completed today, due count, streak, and tomorrow estimate. Show a persistent but non-blocking message explaining that guest progress belongs to the current browser and may be lost if browser storage is cleared.

- [ ] **Step 6: Run component and package tests**

Run:

```bash
pnpm vitest run apps/web/src/components/learning packages/learning-core/src packages/local-store/src
```

Expected: PASS.

- [ ] **Step 7: Commit guest learning**

```bash
git add apps/web/src/pages apps/web/src/components/learning apps/web/src/lib/runtime.ts
git commit -m "feat: add local-first guest learning flow"
```

---

### Task 11: Create Supabase User Tables, RLS Policies, and Authentication Client

**Files:**
- Create: `supabase/config.toml`
- Create: `supabase/migrations/202608150001_vertical_prototype.sql`
- Create: `supabase/tests/vertical_prototype_rls.sql`
- Create: `packages/cloud-sync/src/types.ts`
- Create: `packages/cloud-sync/src/supabase-repository.ts`
- Create: `apps/web/src/components/auth/AuthIsland.tsx`
- Create: `apps/web/src/pages/[locale]/login/callback.astro`
- Create: `.env.example`

**Interfaces:**
- Consumes: local learning records and Supabase authenticated user ID.
- Produces: passwordless and OAuth entry points, user-owned cloud tables, and a typed cloud repository.

- [ ] **Step 1: Write the SQL migration**

Create these prototype tables:

```sql
create table public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  locale text not null default 'en',
  daily_new_term_target integer not null default 3 check (daily_new_term_target between 1 and 30),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.bookmarks (
  user_id uuid not null references auth.users(id) on delete cascade,
  term_id text not null,
  updated_at timestamptz not null,
  deleted_at timestamptz,
  primary key (user_id, term_id)
);

create table public.review_events (
  event_id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  term_id text not null,
  rating text not null check (rating in ('again', 'partial', 'mastered')),
  reviewed_at timestamptz not null,
  device_id text not null,
  content_version integer not null check (content_version > 0),
  created_at timestamptz not null default now()
);

create table public.term_states (
  user_id uuid not null references auth.users(id) on delete cascade,
  term_id text not null,
  state jsonb not null,
  due_at timestamptz not null,
  updated_at timestamptz not null,
  primary key (user_id, term_id)
);
```

Enable RLS on every table. Policies require `auth.uid() = user_id` for select, insert, update, and delete. Add no public content tables.

- [ ] **Step 2: Write failing pgTAP RLS tests**

Test that an authenticated user can access own rows, cannot read or modify another user's rows, anonymous access is denied, and service-role behavior is not required by client tests.

- [ ] **Step 3: Run the local Supabase tests**

Run:

```bash
supabase start
supabase db reset
supabase test db
```

Expected: migration succeeds and all RLS tests pass.

- [ ] **Step 4: Implement the typed Supabase repository**

The browser client uses only `PUBLIC_SUPABASE_URL` and `PUBLIC_SUPABASE_ANON_KEY`. Export methods for current session, own profile, bookmarks, review-event upsert by immutable ID, term-state upsert, and batch reads after a cursor timestamp.

- [ ] **Step 5: Implement optional authentication UI**

Expose:

```text
Email one-time code form
Continue with Google
Continue with GitHub
Cancel and continue as guest
```

Use a two-stage email-code flow: call `signInWithOtp({ email, options: { shouldCreateUser: true } })`, render a six-digit code form, and verify it with `verifyOtp({ email, token, type: 'email' })`. Configure the Supabase email template to show `{{ .Token }}` rather than relying on a magic link. Use `signInWithOAuth()` for Google and GitHub with an explicit callback URL under the current locale. Do not initialize provider SDKs at page load.

- [ ] **Step 6: Document required external configuration**

`.env.example` contains only public variable names and inert examples. `README.md` must state that production email OTP requires a configured SMTP sender and that OAuth redirect URLs must include local preview, Codex Sites preview, and production origins.

- [ ] **Step 7: Run TypeScript and SQL tests**

Run:

```bash
pnpm typecheck
supabase test db
```

Expected: PASS.

- [ ] **Step 8: Commit authentication and cloud schema**

```bash
git add supabase packages/cloud-sync apps/web/src/components/auth apps/web/src/pages .env.example README.md
git commit -m "feat: add optional Supabase authentication"
```

---

### Task 12: Implement Idempotent Guest-to-Account Merge and Cloud Sync

**Files:**
- Create: `packages/cloud-sync/src/merge.ts`
- Create: `packages/cloud-sync/src/retry.ts`
- Create: `packages/cloud-sync/src/index.ts`
- Test: `packages/cloud-sync/src/merge.test.ts`
- Test: `packages/cloud-sync/src/retry.test.ts`
- Modify: `apps/web/src/components/auth/AuthIsland.tsx`

**Interfaces:**
- Consumes: `LocalLearningRepository`, Supabase repository, authenticated user ID, device ID, and clock.
- Produces: `mergeGuestData()`, `syncPendingChanges()`, bounded retry, and visible sync state.

```ts
export interface MergeSummary {
  insertedReviewEvents: number;
  duplicateReviewEvents: number;
  mergedBookmarks: number;
  updatedSettings: boolean;
  recomputedTermStates: number;
}

export interface SyncStatus {
  state: 'idle' | 'syncing' | 'pending' | 'error';
  pendingCount: number;
  lastSuccessfulSyncAt: string | null;
  message: string | null;
}
```

- [ ] **Step 1: Write failing merge tests**

Test:

```text
- Union review events by event ID.
- Running the same merge twice inserts no duplicates.
- Newer bookmark tombstone wins over an older add.
- Newer valid settings timestamp wins.
- Term state is recomputed from merged review history rather than copied blindly.
- A cloud failure preserves every local record and marks sync pending.
```

- [ ] **Step 2: Run merge tests and verify failure**

Run:

```bash
pnpm vitest run packages/cloud-sync/src
```

Expected: FAIL because merge functions do not exist.

- [ ] **Step 3: Implement pure merge rules first**

Pure functions accept arrays and timestamps and return merged records plus a summary. They must not import Supabase, Dexie, React, or global time.

- [ ] **Step 4: Implement bounded exponential backoff**

Use delays of 500 ms, 1 s, 2 s, and 4 s with at most four attempts. Inject the sleep function in tests. Do not retry authentication errors, validation errors, or RLS denials.

- [ ] **Step 5: Implement guest merge orchestration**

After the first successful sign-in and only when `hasGuestData()` is true, display a merge choice with **Merge local progress** as the primary action and **Keep cloud progress only** as a secondary destructive action requiring confirmation. The merge action uploads immutable events, reconciles sets, recomputes states, and writes the merged result back locally.

- [ ] **Step 6: Expose visible sync state**

The account menu shows `Synced`, `Syncing`, `Pending offline`, or a recoverable error. It must explicitly state that local data remains safe when retry is exhausted.

- [ ] **Step 7: Run merge, repository, and component tests**

Run:

```bash
pnpm vitest run packages/cloud-sync/src packages/local-store/src apps/web/src/components/auth
```

Expected: PASS.

- [ ] **Step 8: Commit synchronization**

```bash
git add packages/cloud-sync apps/web/src/components/auth
git commit -m "feat: merge and sync learner progress"
```

---

### Task 13: Add Offline Caching and Explicit Resilience States

**Files:**
- Create: `apps/web/scripts/generate-service-worker.mjs`
- Create: `apps/web/src/scripts/register-service-worker.ts`
- Create: `apps/web/public/manifest.webmanifest`
- Modify: `apps/web/src/layouts/BaseLayout.astro`
- Modify: `apps/web/src/components/search/SearchIsland.tsx`
- Modify: `apps/web/src/components/learning/LearningSession.tsx`
- Test: `apps/web/src/lib/resilience.test.ts`

**Interfaces:**
- Consumes: static build output and runtime adapter errors.
- Produces: precached prototype shell, cached search indexes, offline navigation, and user-facing recoverable error states.

- [ ] **Step 1: Write failing resilience tests**

Test messages for:

```text
search index unavailable
IndexedDB unavailable
IndexedDB quota exceeded
offline cloud sync
authentication cancellation
sync retry exhaustion
```

Every message states what failed, whether local data is safe, and the next action. No raw stack trace appears.

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pnpm vitest run apps/web/src/lib/resilience.test.ts
```

Expected: FAIL because resilience mappings do not exist.

- [ ] **Step 3: Generate a deterministic service worker after build**

The script walks `dist/`, includes HTML, CSS, JavaScript, JSON search indexes, manifest, and icons, sorts URLs, and emits `dist/sw.js`. Cache name includes a SHA-256 digest of the URL list. Use cache-first for hashed assets and network-first with cached fallback for HTML.

- [ ] **Step 4: Register the service worker only in production builds**

Registration failure must be ignored after logging a concise development warning. The site remains fully usable online without service worker support.

- [ ] **Step 5: Add a browser storage fallback**

If IndexedDB cannot open, allow dictionary browsing and a non-persistent demo learning session. Disable claims that progress is saved and provide a retry button. Never silently fall back to storing the structured learning database in `localStorage`.

- [ ] **Step 6: Run offline preview checks**

Run the production preview, visit English home, one term, search, and learning page, then disable network in Playwright and reload those pages. Expected: cached pages and current locale search remain usable; cloud sync reports pending.

- [ ] **Step 7: Commit resilience support**

```bash
git add apps/web/scripts apps/web/src apps/web/public
git commit -m "feat: support offline dictionary and learning"
```

---

### Task 14: Add SEO, Accessibility, and End-to-End Acceptance Tests

**Files:**
- Create: `tests/e2e/search.spec.ts`
- Create: `tests/e2e/guest-learning.spec.ts`
- Create: `tests/e2e/locale-routing.spec.ts`
- Create: `tests/e2e/accessibility.spec.ts`
- Create: `playwright.config.ts`
- Modify: `apps/web/src/layouts/BaseLayout.astro`
- Modify: term and category pages

**Interfaces:**
- Consumes: built web app and prototype corpus.
- Produces: release-level browser tests, localized metadata, and machine-readable term markup.

- [ ] **Step 1: Write failing Playwright tests**

Cover these journeys:

```text
Search `Auth` and open `/en/terms/authentication`.
Search `身份认证` and open `/zh-cn/terms/authentication`.
Complete one guest review, reload, and confirm progress remains.
Switch a term from zh-cn to de without losing the slug.
Use the entire search result list and learning card with keyboard only.
Run axe on home, term, category, and learning pages with no serious or critical violations.
```

- [ ] **Step 2: Run tests and verify failures**

Run:

```bash
pnpm --filter @vibe-terms/web build
pnpm exec playwright test
```

Expected: at least metadata or accessibility assertions fail before final markup is added.

- [ ] **Step 3: Add localized SEO metadata**

Every term page includes localized title and description, canonical URL, all available `hreflang` alternates, Open Graph metadata, and `DefinedTerm` JSON-LD. Generate a multilingual sitemap from static paths. Draft prototype pages set `robots: noindex`; production-published pages are indexable.

- [ ] **Step 4: Fix accessibility findings**

Required checks:

```text
one h1 per page
logical heading order
skip link
visible focus
labeled inputs
associated error messages
44 CSS pixel minimum touch targets for primary controls
no color-only status communication
reduced-motion support
aria-live announcement for learning state changes
```

- [ ] **Step 5: Run the full browser suite**

Run:

```bash
pnpm exec playwright test
```

Expected: PASS on Chromium desktop and a mobile viewport project.

- [ ] **Step 6: Commit acceptance coverage**

```bash
git add tests playwright.config.ts apps/web
git commit -m "test: cover dictionary and learning journeys"
```

---

### Task 15: Add CI, Licensing, Contributor Documentation, and Security Checks

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `LICENSE`
- Create: `LICENSE-CONTENT`
- Create: `CONTRIBUTING.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: every root quality command.
- Produces: reproducible pull-request checks and unambiguous license boundaries.

- [ ] **Step 1: Create the CI workflow**

Use Ubuntu 24.04, Node 24, pnpm 11.4.0, and a frozen lockfile. Jobs:

```text
quality: install, lint, typecheck, unit tests, content validation
build: prototype static build and artifact upload
browser: Playwright Chromium tests against built preview
supabase: local database reset and pgTAP tests
dependency-security: pnpm audit with high severity failure threshold
secret-scan: gitleaks action or an equivalent pinned scanner
```

Grant read-only repository permissions unless artifact upload requires more. Do not expose Supabase production secrets to pull requests.

- [ ] **Step 2: Add license files and path guidance**

`LICENSE` contains Apache License 2.0. `LICENSE-CONTENT` contains CC BY-SA 4.0 legal code or an authoritative notice plus link, according to repository policy. README and CONTRIBUTING state:

```text
code outside content/: Apache-2.0
content/, quizzes, translations, analogies, and editorial copy: CC BY-SA 4.0
```

- [ ] **Step 3: Document local setup and validation**

README includes Node and pnpm versions, install command, development command, content modes, test commands, Supabase local setup, environment variables, static build location, and the fact that hosted pricing may change even though the project is open source.

- [ ] **Step 4: Document contribution rules**

CONTRIBUTING covers GitHub Issues and Pull Requests only, English canonical changes, translation status, source quality, content file layout, validation commands, license agreement, and prohibition on committing secrets or marking machine translation as human reviewed.

- [ ] **Step 5: Run CI commands locally**

Run:

```bash
pnpm install --frozen-lockfile
pnpm check
supabase test db
pnpm exec playwright test
```

Expected: PASS.

- [ ] **Step 6: Commit repository governance**

```bash
git add .github LICENSE LICENSE-CONTENT README.md CONTRIBUTING.md AGENTS.md
git commit -m "chore: add CI and open source governance"
```

---

### Task 16: Validate Codex Sites Deployment and Portable Fallback

**Files:**
- Create: `scripts/verify-deployment.mjs`
- Create: `docs/deployment/codex-sites-prototype.md`
- Create: `docs/deployment/portable-static-fallback.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: `apps/web/dist`, deployed base URL, Supabase public URL and anonymous key, and configured OAuth redirect origins.
- Produces: verified deployment evidence, exact platform constraints, and a fallback procedure that preserves the static artifact.

- [ ] **Step 1: Implement deployment verification script**

The script accepts `DEPLOYMENT_URL` and checks:

```text
GET / returns 200
GET /en returns 200
GET /en/terms/authentication returns 200
GET /zh-cn/terms/authentication returns 200 in prototype mode
GET /search/en.json returns valid JSON
GET /sw.js returns JavaScript
term page contains canonical, hreflang, and DefinedTerm metadata
unknown term returns the platform's expected not-found response
```

It exits nonzero on any failure and prints concise diagnostics.

- [ ] **Step 2: Build the exact deployment artifact**

Run:

```bash
pnpm exec cross-env PUBLIC_SITE_URL=https://prototype.example pnpm --filter @vibe-terms/web build:prototype
find apps/web/dist -type f | sort > /tmp/vibe-terms-dist-manifest.txt
```

Record artifact file count and total size in the deployment document.

- [ ] **Step 3: Publish through Codex Sites without adding runtime coupling**

Use the Codex Sites publish flow available to the account and select the static artifact or repository build as supported by the current preview. Configure only public environment variables. Do not migrate terminology content or learning data into Sites-specific storage.

Document the exact observed answers to:

```text
Can Sites build Node 24 and pnpm 11.4.0?
Can it publish all static locale routes?
Can it set PUBLIC_SITE_URL, PUBLIC_SUPABASE_URL, and PUBLIC_SUPABASE_ANON_KEY?
Can it preserve OAuth callback paths?
Can public access be enabled for this account and region?
What file, build-time, bandwidth, or route limits are reported?
```

These are deployment findings, not assumptions.

- [ ] **Step 4: Validate authentication callbacks**

Add the deployed callback origins to Supabase's redirect allowlist. Test email OTP, Google, and GitHub in the deployed preview. Confirm that canceling or failing OAuth returns the user to a usable guest page and does not erase local progress.

- [ ] **Step 5: Run deployment verification**

Run:

```bash
pnpm exec cross-env DEPLOYMENT_URL=https://the-actual-preview-origin.example node scripts/verify-deployment.mjs
```

Expected: all route, search, service-worker, and metadata checks pass.

- [ ] **Step 6: Exercise the portable fallback**

Deploy the same `apps/web/dist` artifact to a plain static host or local HTTP server without changing application source. Run the same verification script. The fallback document records the command and any redirect rule required for not-found handling.

- [ ] **Step 7: Run the prototype exit checklist**

Confirm all approved vertical-prototype criteria:

```text
12 canonical terms exist.
All eight locale routes build.
Draft translations are visibly marked and noindexed.
Search resolves localized names, canonical names, and aliases.
Guest learning survives reload.
Public content works with Supabase unavailable.
Guest merge is idempotent and creates no duplicate events.
Email OTP, Google, and GitHub entry points work in the deployed environment.
Desktop and mobile Playwright suites pass.
Accessibility suite has no serious or critical violations.
Codex Sites either passes deployment validation or the portable fallback is documented and working.
```

- [ ] **Step 8: Commit deployment evidence**

```bash
git add scripts/verify-deployment.mjs docs/deployment README.md
git commit -m "docs: validate prototype deployment path"
```

---

## Final Verification

Run from a clean checkout:

```bash
corepack enable
corepack prepare pnpm@11.4.0 --activate
pnpm install --frozen-lockfile
pnpm check
supabase start
supabase db reset
supabase test db
pnpm exec playwright install --with-deps chromium
pnpm exec playwright test
pnpm --filter @vibe-terms/web build:prototype
git status --short
```

Expected:

```text
All unit, content, SQL, accessibility, integration, and end-to-end tests pass.
The static build succeeds for eight locales.
The working tree is clean.
No secret or production credential exists in tracked files.
```

## Plan Self-review Record

- **Spec coverage:** This plan covers every vertical-prototype requirement from the approved specification: 12 terms, eight locale routes, public dictionary pages, category exploration, multilingual search, guest learning, adaptive scheduling, local persistence, optional authentication, minimal sync, offline behavior, accessibility, CI, and Codex Sites validation.
- **Deferred scope:** Maintainer studio, 100-term alpha, custom list UI, full import/export UI, account deletion, complete baseline, and 500-term certification are explicitly assigned to later plans rather than silently omitted.
- **Type consistency:** Shared names are fixed across tasks: `Locale`, `ReviewEvent`, `TermLearningState`, `LocalLearningRepository`, `MergeSummary`, `SyncStatus`, and the three `BeginnerRating` values.
- **Placeholder scan:** The plan contains no unresolved implementation placeholders. Deployment capability questions are explicit validation outputs because Codex Sites is a changing preview environment, not missing requirements.
