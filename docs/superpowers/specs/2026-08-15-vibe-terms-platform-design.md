# Vibe Terms Platform Design Specification

**Status:** Approved design

**Date:** 2026-08-15 (Asia/Singapore)

**Working name:** Vibe Terms

**Primary audience:** People with little or no programming experience who use AI-assisted coding tools

## 1. Executive summary

Vibe Terms is an open-source, multilingual Vibe Coding terminology platform. It combines a public, search-first technical dictionary with an optional learning system inspired by spaced-repetition vocabulary products.

The product is dictionary-first. A visitor should be able to arrive with an unfamiliar term, error message, abbreviation, or framework-specific component name and reach a clear explanation quickly. The learning system is an enhancement rather than the site's primary gate: every public term remains accessible without an account.

The initial public release targets approximately 500 canonical terms across eight languages:

- English (`en`), the canonical authoring language
- Simplified Chinese (`zh-cn`)
- Traditional Chinese (`zh-tw`)
- Japanese (`ja`)
- Korean (`ko`)
- German (`de`)
- Russian (`ru`)
- Hindi (`hi`)

The site will cover every term currently represented by the reference site vibe-hub.org through canonical terms, aliases, or explicit source mappings, while expanding into underrepresented areas such as debugging, security, databases, deployment, accessibility, AI agents, MCP, RAG, evaluation, and product practice.

The official hosted service will initially be free to use, but the project does not promise that hosted service will remain free forever. The source code and content remain separately licensed and independently deployable.

## 2. Product goals

### 2.1 Primary goals

1. Help a complete beginner understand software and AI-coding terminology without requiring prior computer science knowledge.
2. Make terms discoverable through localized names, English canonical names, acronyms, aliases, misspellings, and framework-specific names.
3. Present each term in layers, starting with a plain-language explanation and allowing deeper engineering detail to be expanded.
4. Provide a progressive learning path and adaptive review system without requiring an account.
5. Preserve learning data locally for guests and synchronize it across devices for signed-in users.
6. Publish all dictionary content in a Git-based, reviewable, reusable format.
7. Support community contribution through GitHub Issues and Pull Requests only.
8. Keep the public dictionary usable even when authentication or cloud synchronization is unavailable.
9. Remain portable beyond the initial Codex Sites deployment target.

### 2.2 Non-goals for the initial release

The initial release will not include:

- Paid memberships, subscriptions, coupons, or feature paywalls
- Email reminders, push notifications, or operating-system notifications
- Public user profiles, leaderboards, social feeds, or competitive rankings
- Website-based public content submissions
- Multi-stage editorial comments, assignments, or enterprise approval workflows
- Live collaborative editing
- Native mobile applications
- AI chat as the primary way to browse the dictionary
- Real-time dependence on Supabase for rendering public term pages
- Support for multiple interchangeable production databases in the first implementation
- A promise of permanent free hosted service

## 3. Confirmed product decisions

The following decisions are fixed for this specification:

- The product is dictionary-first.
- The homepage uses a category-exploration information architecture.
- The main audience is a complete programming beginner.
- The first public release targets about 500 canonical terms.
- The site supports eight languages.
- English is the sole canonical content source.
- Localized files are translations and adaptations of the English source.
- Term pages use a layered teaching format.
- The learning system combines recommended paths with custom word lists.
- Review uses three beginner-friendly ratings backed by an adaptive scheduler.
- Guests can use the complete public dictionary and learning system without an account.
- Guest learning data is stored locally in the browser.
- Signed-in users can synchronize data through Supabase.
- Authentication supports email one-time codes, Google, and GitHub.
- GitHub is the sole source of truth for terminology content.
- The maintainer studio creates files and Pull Requests rather than writing production content to a database.
- Supabase stores user-owned data only.
- Codex Sites is the initial deployment target, not a permanent platform dependency.
- Code uses the Apache License 2.0.
- Terminology, translations, and teaching content use CC BY-SA 4.0.
- Community contributions are accepted through GitHub only.

## 4. User groups and principal journeys

### 4.1 Guest visitor

A guest can:

- Search and browse every published term
- Switch language and color theme
- Begin a recommended learning path
- Choose a daily new-term target
- Review due terms
- Create custom lists
- Bookmark terms
- Mark terms as learned
- View local learning statistics
- Export or import local learning data

Guest data is stored locally. The interface must clearly explain that clearing browser data or changing devices can remove unsynchronized progress.

### 4.2 Signed-in learner

A signed-in learner can do everything a guest can, plus:

- Synchronize progress across devices
- Merge pre-login guest progress into the account
- Recover data after changing devices
- Export cloud data
- Delete the account and associated cloud data
- Sign out while optionally preserving a local copy

### 4.3 Maintainer or editor

A maintainer uses a local-only studio to:

- Create and edit canonical English entries
- Apply taxonomy, prerequisites, aliases, and reference-site mappings
- Generate translation drafts through a pluggable AI provider adapter
- Review source and translation side by side
- Validate glossary consistency and required fields
- Preview localized pages
- write content files to a branch
- Run validation and tests
- Commit changes and open a GitHub Pull Request

The studio never publishes directly to the official site and never treats Supabase as the content authority.

### 4.4 Open-source contributor

A contributor can:

- Report a term omission or error through a GitHub Issue
- Edit code, English source content, or translations through a Pull Request
- Run the same validation locally as continuous integration
- Preview the resulting site before review

## 5. Information architecture

### 5.1 Primary navigation

The main navigation includes:

- Home
- Terms
- Categories
- Learning paths
- Today's learning
- Global search
- Language selector
- Light, dark, and system theme control
- Sign in or account menu

On mobile, search and current learning are prioritized. Secondary navigation is placed in a compact menu.

### 5.2 Dual taxonomy

Each term is organized along two independent dimensions.

#### Technical domain

The initial allocation is approximately:

| Domain | Target count |
|---|---:|
| AI and Vibe Coding | 70 |
| Computing and development environment | 35 |
| Web and networking | 35 |
| Product and requirements | 35 |
| UI, UX, and accessibility | 55 |
| Frontend development | 75 |
| Backend and APIs | 45 |
| Data and databases | 40 |
| Git and collaboration | 25 |
| Testing and debugging | 35 |
| Security and privacy | 30 |
| Deployment, performance, and operations | 20 |
| **Total** | **500** |

A term may have one primary domain and multiple secondary domain tags.

#### Project lifecycle stage

Each term has one primary learning-stage placement:

1. Form an idea
2. Define requirements
3. Design the experience
4. Establish the development environment
5. Build interface and logic
6. Connect data and identity
7. Test and protect
8. Deploy and maintain

The UI allows users to browse by technical domain or learn in lifecycle order.

### 5.3 Reference-site baseline

A versioned baseline file maps every reference-site term to the new system. Each mapping has one of these relationships:

- `canonical`: the reference term is retained as a canonical term
- `alias`: the reference term maps to a more general canonical term
- `merged`: several narrow terms map to one canonical concept
- `split`: one broad reference term maps to several more precise canonical terms
- `deprecated-name`: the term remains searchable but is not preferred

Automated validation prevents a baseline term from becoming unmapped.

## 6. Public page design

### 6.1 Homepage

The homepage is category-exploration first, with search still prominent.

Sections appear in this order:

1. Global search hero
2. Technical-domain map
3. Project-lifecycle map
4. Continue-learning panel for returning users
5. Beginner learning-path entry point
6. Recently added or substantially updated terms
7. Open-source contribution and licensing summary

Each category card contains:

- Localized category name
- Short beginner-friendly description
- Published term count
- Three representative terms
- User learning progress when available
- A clear entry action

### 6.2 Term detail page

The top of every term page displays:

- Localized title
- English canonical name
- Acronyms and aliases
- Primary domain and lifecycle stage
- Difficulty
- One-sentence definition
- Plain-language analogy
- Bookmark action
- Add-to-plan action
- Mark-as-mastered action

The remaining sections are ordered as follows:

1. How it works
2. Why it matters in Vibe Coding
3. Example in the recurring "AI learning assistant" project
4. Copyable AI instruction example
5. Common mistakes and confusions
6. Three-question quiz
7. Prerequisite terms
8. Related terms
9. Primary sources
10. Translation status and contributors

Beginner content is visible by default. Engineering detail is placed in accessible disclosure sections.

### 6.3 Category page

A category page provides:

- Category explanation
- Suggested beginner entry point
- Sort by recommended order, alphabetical order, difficulty, or update date
- Filters for lifecycle stage and learning status
- Progress indicator
- Related learning paths

### 6.4 Learning-path page

A learning path contains ordered stages, prerequisites, estimated term count, and completion progress. The initial built-in path is a zero-to-Vibe-Coding curriculum. Users may also create custom lists from search results, category pages, or bookmarks.

## 7. Content model

### 7.1 Repository layout

```text
vibe-terms/
├── apps/
│   ├── web/
│   └── studio/
├── packages/
│   ├── content-schema/
│   ├── content-loader/
│   ├── search-core/
│   ├── learning-core/
│   ├── local-store/
│   ├── cloud-sync/
│   └── ui/
├── content/
│   ├── terms/
│   ├── taxonomy/
│   ├── paths/
│   ├── glossaries/
│   └── baselines/
├── supabase/
│   ├── migrations/
│   └── policies/
├── scripts/
├── docs/
└── licenses/
```

### 7.2 Term directory

Each term has one directory:

```text
content/terms/authentication/
├── meta.yaml
├── en.yaml
├── zh-cn.yaml
├── zh-tw.yaml
├── ja.yaml
├── ko.yaml
├── de.yaml
├── ru.yaml
└── hi.yaml
```

### 7.3 Language-independent metadata

`meta.yaml` contains:

```yaml
id: term_authentication
slug: authentication
canonical_name: Authentication
acronyms: []
aliases:
  - Auth
primary_domain: security-and-privacy
secondary_domains:
  - backend-and-apis
lifecycle_stage: connect-data-and-identity
difficulty: beginner
prerequisites:
  - identity
  - client-server
related_terms:
  - authorization
  - session
  - oauth
reference_mappings:
  - source: vibe-hub
    source_term: Authentication
    relationship: canonical
sources:
  - title: HTTP authentication
    url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Authentication
    source_type: official-documentation
content_version: 1
```

### 7.4 Localized teaching content

Each locale file contains:

```yaml
title: Authentication
short_definition: A concise beginner-friendly definition.
analogy: A precise everyday analogy.
mechanism: |
  A layered explanation of how the concept works.
why_it_matters: |
  Why a Vibe Coding user needs to understand it.
project_example: |
  A recurring-project example.
ai_prompt_example: |
  A copyable instruction for an AI coding assistant.
common_mistakes:
  - A common misconception or failure mode.
quiz:
  - id: authentication-q1
    type: single-choice
    question: A localized question.
    options:
      - Option A
      - Option B
      - Option C
    correct_option: 1
    explanation: A localized explanation.
publication:
  status: published
localization:
  source_locale: en
  source_content_version: 1
  machine_generated: false
  reviewed_by:
    - github-handle
```

The English locale uses the same schema and records itself as the source locale. It is canonical rather than translated.

### 7.5 Locale publication and freshness states

Each locale has one publication state:

- `missing`: no locale file exists
- `draft`: content is incomplete or machine-generated and unreviewed
- `reviewed`: human review is complete but the locale is not yet public
- `published`: the locale is eligible for the public build
- `withdrawn`: a previously public locale has been intentionally removed

For non-English locales, freshness is derived by comparing `source_content_version` with the English `content_version`. An older translation is `stale`. A stale translation that was previously published remains available at its last reviewed version, displays a localized out-of-date notice, and can be updated independently of the other languages. Maintainers may withdraw it when the English change corrects a safety-critical or meaning-breaking error.

Full public-release certification requires every locale to be published and current. Routine post-launch builds warn about stale published translations but do not make unrelated languages unavailable.

## 8. Content workflow and GitHub governance

### 8.1 Source of truth

GitHub is the sole content source of truth. Production content is built only from reviewed files merged into the protected default branch.

### 8.2 Maintainer studio workflow

The studio runs locally and consists of:

- A React interface
- A localhost Node service with repository file access
- A content-schema validator
- A translation-provider adapter
- Git and GitHub CLI integration

A complete edit follows this flow:

1. Create or select a branch
2. Edit canonical English content
3. Validate metadata and term relationships
4. Generate translation drafts
5. Review translations side by side
6. Preview pages in each locale
7. Mark reviewed locales
8. Write files
9. Run validation and tests
10. Commit
11. Open a Pull Request

The studio does not hold a production database administrator credential.

### 8.3 Continuous integration checks

Every Pull Request must pass:

- YAML schema validation
- Unique ID and slug validation
- Alias collision detection
- Baseline coverage validation
- Prerequisite existence validation
- Directed-cycle detection in required prerequisite paths
- Related-term existence validation
- Required source validation
- Locale completeness and status validation
- Stale translation detection
- Broken internal-link detection
- External-link format checks
- Build verification
- Search-index generation
- Unit tests
- Accessibility smoke tests
- Preview deployment when supported by the target platform

### 8.4 Contribution policy

Public contribution happens only through GitHub.

- Issues are used for omissions, errors, taxonomy proposals, and design discussion.
- Pull Requests are used for code or content changes.
- A contribution guide defines file structure, validation commands, translation expectations, source standards, and licensing.
- Content contributors agree that their contributions are distributed under CC BY-SA 4.0.
- Code contributors agree that their contributions are distributed under Apache-2.0.

## 9. Search design

### 9.1 Build-time indexes

The build process creates one compact search index per locale. Public search does not require Supabase.

Each index includes:

- Localized title
- English canonical title
- Acronyms
- Localized aliases
- Framework-specific aliases
- Short definition
- Category labels
- Lifecycle stage labels
- Common misspellings where curated

### 9.2 Ranking

Results are ranked in this order:

1. Exact localized-title match
2. Exact English canonical-title match
3. Exact acronym or alias match
4. Prefix match
5. Curated misspelling match
6. Fuzzy title match
7. Definition-content match

### 9.3 Tokenization

- Chinese, Japanese, and Korean indexes use character n-grams with normalized punctuation and width.
- English, German, Russian, and Hindi indexes use locale-aware token normalization.
- Diacritics and case are normalized for matching while display text remains unchanged.
- Search accepts localized queries and English technical names on every locale.

### 9.4 Search acceptance criteria

- Searching `JWT`, a localized equivalent of "token," or `JSON Web Token` leads to the same canonical term.
- Every reference-site baseline name returns at least one correct result.
- A common one-character typing error in a term title still returns the intended term within the first five results.
- Search remains usable offline after the relevant locale index has been cached.

## 10. Learning system

### 10.1 Learning sources

A learner can study from:

- The built-in zero-to-Vibe-Coding path
- A technical category
- A lifecycle stage
- A custom list
- Bookmarks
- Terms manually added from detail pages

### 10.2 Daily target

The default target is three new terms per day. The allowed setting is 1 to 30 new terms per day.

When a user selects more than 20, the interface warns that future review volume may grow substantially but does not block the choice.

### 10.3 Daily queue order

The queue is constructed as:

1. Overdue and due reviews
2. New terms up to the configured target
3. Optional extra practice

The interface shows due-review count and new-term target separately.

### 10.4 Card interaction

Each learning card has four steps:

1. Show the localized term and ask for recall
2. Reveal the short definition and analogy
3. Allow the learner to expand the mechanism, project example, and AI prompt
4. Record one of three ratings

The ratings are:

- `again`: not recognized
- `partial`: some impression
- `mastered`: confidently understood

Localized labels remain beginner-friendly and do not expose scheduling jargon.

### 10.5 Adaptive scheduler

`learning-core` defines a scheduler interface rather than embedding scheduling logic in UI components. The initial implementation uses an FSRS-compatible model or an equivalently validated adaptive spaced-repetition algorithm.

The scheduler tracks, at minimum:

- Term ID
- Learner state
- Difficulty estimate
- Stability estimate
- Last review timestamp
- Next due timestamp
- Review count
- Lapse count
- Last rating
- Content version last reviewed

The implementation maps the three UI ratings to scheduler grades through a documented adapter. Scheduling tests use deterministic fixtures and must not depend on wall-clock time.

### 10.6 Learning statistics

The initial statistics include:

- New terms learned today
- Reviews completed today
- Current due count
- Accuracy by recent review rating
- Consecutive active days
- Progress by category and path
- Estimated reviews due tomorrow

No public ranking is created.

## 11. Guest storage and account synchronization

### 11.1 Local-first rule

All learning actions write to local storage first. The initial implementation uses IndexedDB for structured data and `localStorage` only for small preferences such as theme, active locale, and migration flags.

The public dictionary and guest learning flow work without authentication or network connectivity after required assets are cached.

### 11.2 Local data model

The local database contains:

- `profile_settings`
- `learning_plans`
- `custom_lists`
- `custom_list_items`
- `bookmarks`
- `term_states`
- `review_events`
- `daily_activity`
- `sync_metadata`

Every mutable entity has a stable ID, creation timestamp, update timestamp, and deletion marker where set semantics require it.

### 11.3 Authentication

Supabase authentication supports:

- Email one-time code
- Google OAuth
- GitHub OAuth

Authentication is optional for browsing and learning. OAuth providers are loaded only when the user initiates sign-in and are not required for public page rendering.

### 11.4 Guest-to-account merge

After the first successful sign-in on a browser with guest data, the product displays a clear merge action. The default action is to merge, not overwrite.

Conflict rules are:

- Review events: union by immutable `event_id`
- Bookmarks: add/remove set with tombstones
- Custom-list membership: add/remove set with tombstones
- Settings: latest valid update wins
- Path enrollment: union, preserving the most advanced valid position
- Term scheduler state: recomputed from the merged review-event history

The merge is idempotent. Repeating it cannot duplicate review events or list items.

### 11.5 Cloud data

Supabase stores user-owned data only:

- Profile and learning preferences
- Learning plans
- Custom lists and membership
- Bookmarks
- Review events
- Derived scheduler state
- Daily activity summaries
- Device sync metadata

Public terminology content is not authored in Supabase.

### 11.6 Security policies

Every user-owned table uses row-level security. A user can read and modify only rows belonging to the authenticated user ID. Service-role credentials never appear in public client code.

### 11.7 Export, import, and deletion

Guests and signed-in users can export learning data in a documented JSON format. Guests can restore from JSON. Signed-in users can delete cloud data and the authentication account. The deletion flow states whether a local copy will remain and offers an explicit choice.

## 12. Application architecture

### 12.1 Selected stack

The initial stack is:

- Astro for static page generation and routing
- React for interactive islands
- TypeScript across applications and packages
- Supabase for authentication and user-data synchronization
- IndexedDB through a typed local-store adapter
- YAML for source content
- A monorepo package manager and workspace configuration
- Static build output as the primary deployment artifact

### 12.2 Architectural boundaries

#### `content-schema`

Defines and validates term metadata, locale content, taxonomy, paths, and baseline mappings. It has no UI dependency.

#### `content-loader`

Loads YAML files, resolves relationships, produces page data, and emits build diagnostics.

#### `search-core`

Builds locale indexes and performs ranked client-side queries. It has no dependency on Supabase.

#### `learning-core`

Creates daily queues, maps ratings, calculates schedules, and derives learning statistics. It accepts clock and persistence interfaces for deterministic tests.

#### `local-store`

Implements browser persistence and schema migrations. UI code does not access IndexedDB directly.

#### `cloud-sync`

Implements authenticated synchronization, merge semantics, retry, and conflict handling. It depends on data interfaces rather than UI components.

#### `ui`

Contains shared accessible components, tokens, and layout primitives. It does not own domain state.

#### `apps/web`

Composes public pages and learning interactions. It consumes the package interfaces.

#### `apps/studio`

Provides the local maintainer workflow and repository-writing service.

### 12.3 Portability requirement

Platform-specific deployment configuration is isolated from application code. The repository must be buildable into ordinary static assets and runnable locally without Codex Sites.

The vertical prototype must validate Codex Sites deployment, redirects, OAuth callback handling, environment variables, and static asset limits before the project commits to platform-specific optimizations.

## 13. Internationalization and SEO

### 13.1 URL scheme

All pages use explicit locale prefixes:

```text
/en/terms/authentication
/zh-cn/terms/authentication
/zh-tw/terms/authentication
/ja/terms/authentication
/ko/terms/authentication
/de/terms/authentication
/ru/terms/authentication
/hi/terms/authentication
```

The root route suggests a locale from browser preferences but does not repeatedly force redirect after the user has selected a language.

### 13.2 Localized metadata

Every indexable page includes:

- Correct HTML `lang`
- Localized title and description
- Canonical URL
- `hreflang` links for published equivalents
- Open Graph metadata
- Structured data suitable for a defined term
- Inclusion in a localized sitemap

Missing, draft, reviewed-but-unpublished, and withdrawn locales are not indexed. A stale locale that remains published stays indexable and displays its last-reviewed date and an out-of-date notice.

### 13.3 Terminology consistency

Each locale has a glossary file containing approved translations of recurring technical terms. The studio and CI flag inconsistent glossary usage but permit documented exceptions when a term has a context-specific translation.

### 13.4 Typography

The design uses privacy-preserving system-font stacks by default. The site does not require loading third-party font services. Font fallback must support Latin, Cyrillic, CJK scripts, and Devanagari without breaking layout.

## 14. Visual and interaction design

The visual direction is a modern editorial knowledge map, not a game clone or terminal-themed developer toy.

Design principles:

- Search and comprehension dominate decoration.
- Light, dark, and system themes are equal first-class modes.
- Body text uses controlled reading width and comfortable line height.
- Technical domains may use consistent accent colors, but color is never the only information carrier.
- Cards have moderate radius and clear hierarchy.
- Motion is subtle and respects reduced-motion preferences.
- Interactive controls are keyboard accessible.
- Focus indicators are always visible.
- Content disclosures use native or equivalently accessible behavior.
- Mobile layouts prioritize search, current learning, and readable content over dense category grids.

Exact color tokens and component dimensions are implementation-level decisions, provided they satisfy these constraints and accessibility tests.

## 15. Reliability, privacy, and security

### 15.1 Reliability

- Public dictionary pages render without Supabase.
- Authentication failure does not block guest learning.
- Cloud synchronization uses retry with bounded exponential backoff.
- A failed sync leaves local data intact and visibly reports pending state.
- Schema migrations are versioned for both IndexedDB and Supabase.
- Content builds fail closed when required validation fails.

### 15.2 Privacy

- Browsing does not require an account.
- Sensitive learning data is not publicly exposed.
- The product does not create public rankings.
- Analytics, if introduced, must be minimal, documented, and nonessential to page rendering.
- Users can export and delete their data.
- Guest users are warned about the limits of local-only persistence.

### 15.3 Security

- Every Supabase user table uses row-level security.
- OAuth redirects use explicit allowlists.
- Content rendering sanitizes any supported rich-text or Markdown output during build.
- External links use safe target behavior.
- Translation-provider and GitHub credentials remain local to the studio or protected CI secrets.
- No privileged Supabase key is shipped to the browser.
- Dependency and secret scanning run in CI.
- Threat modeling covers account takeover, data leakage, malicious content contributions, supply-chain attacks, and sync corruption before public launch.

## 16. Error handling

The product provides explicit, recoverable states for:

- Search index unavailable
- Unsupported or disabled browser storage
- IndexedDB quota exceeded
- Corrupted local import file
- Offline state
- Authentication cancellation or provider failure
- Cloud sync conflict
- Cloud sync retry exhaustion
- Stale content version during review
- Missing translation
- Broken prerequisite relationship during build
- GitHub CLI not authenticated in the studio
- Translation provider unavailable

Errors must explain what happened, whether local data is safe, and the next available action. Raw stack traces are not shown to end users.

## 17. Testing strategy

### 17.1 Content tests

- All 500 target canonical terms exist before public-release certification.
- Every reference-site baseline term maps to a valid canonical term.
- Every public-release term has eight published locale files.
- IDs, slugs, and canonical names are unique where required.
- Prerequisite references exist and required-path graphs are acyclic.
- Related-term references exist.
- Published sources use valid URLs and approved source types.
- Public-release certification requires every locale file to match the current English source version.
- Routine post-launch builds allow a previously published stale locale only with a warning and visible out-of-date metadata.

### 17.2 Unit tests

- Search normalization and ranking
- Daily-queue creation
- Scheduler rating mapping
- Deterministic scheduling fixtures
- Guest-to-account merge
- Tombstone behavior
- Export and import validation
- Content-schema parsing
- Baseline mapping

### 17.3 Integration tests

- Guest study session persisted across reload
- Sign-in and guest-data merge
- Offline reviews synchronized after reconnect
- Two-device event reconciliation
- Account deletion
- Local export and restore
- Locale routing and fallback
- Theme persistence

### 17.4 End-to-end tests

- Search a localized alias and open the canonical term
- Complete a daily session as a guest
- Sign in with a test authentication flow and merge data
- Create and study a custom list
- Switch locale without losing the canonical term context
- Submit a valid studio content change and generate a Pull Request branch

### 17.5 Accessibility tests

- Keyboard-only navigation
- Visible focus
- Landmark and heading structure
- Form labels and error associations
- Disclosure behavior
- Color contrast
- Reduced motion
- Screen-reader announcement of learning-card state changes

### 17.6 Resilience tests

- Supabase unavailable
- Network intermittently unavailable
- Browser storage disabled
- Storage quota reached
- Duplicate synchronization delivery
- OAuth callback error
- Stale client content version

## 18. Delivery milestones

### 18.1 Vertical prototype

Scope:

- 12 representative terms
- All eight locales
- Homepage, category page, term page, and search
- Guest learning with local storage
- One recommended learning path
- Supabase authentication and minimal cloud sync
- Codex Sites deployment validation

Exit criteria:

- The complete dictionary-to-learning flow works on desktop and mobile.
- Public content remains usable with Supabase unavailable.
- Guest data can merge into a signed-in test account without duplication.
- All eight locale routes build and expose correct metadata.
- The deployment target supports the required static routes and OAuth callbacks, or a documented portable fallback is selected.

### 18.2 Internal alpha

Scope:

- 100 canonical terms
- All technical categories
- Maintainer studio
- Translation draft and review workflow
- GitHub Pull Request generation
- Adaptive review scheduler
- Custom lists and bookmarks
- Robust import, export, and sync

Exit criteria:

- A maintainer can add a term and seven translations without manually creating files.
- CI rejects invalid content and accepts a complete valid contribution.
- Search quality is acceptable in all eight languages against a curated query set.
- Sync and scheduler test suites pass deterministically.

### 18.3 Public release

Scope:

- Approximately 500 canonical terms
- Eight reviewed and published locales per release term
- Complete reference-site baseline mapping
- Guest and signed-in learning flows
- Recommended paths and custom lists
- Open-source repository, contribution guide, and dual licensing
- Codex Sites production deployment or the validated portable fallback

Exit criteria:

- Content, functional, security, accessibility, and resilience release tests pass.
- All migration and rollback procedures are documented.
- User export and account deletion work in production.
- The public site clearly states that hosted pricing may change in the future.

## 19. Success measures

The first release is considered successful when it demonstrates:

- High search success for curated beginner queries in all eight languages
- A measurable share of term-page visitors reaching a useful explanation without opening external resources
- Repeat guest usage without mandatory sign-in
- Meaningful completion of recommended learning sessions
- Reliable guest-to-account merge
- External GitHub contributions to either code or content
- No critical accessibility or security defects at launch

Exact analytics targets are deliberately deferred until the vertical prototype establishes realistic baselines. This does not block implementation because success events and measurement points are already defined.

## 20. Principal risks and mitigations

### 20.1 Translation quality at scale

**Risk:** Four thousand localized term documents can contain inconsistent or misleading technical language.

**Mitigation:** English canonical source, per-locale glossaries, machine drafts marked as drafts, human review, source-version tracking, and CI stale-translation checks.

### 20.2 Content scope overwhelms product delivery

**Risk:** The team attempts to finish all 500 terms before validating search and learning flows.

**Mitigation:** Vertical prototype and 100-term alpha gates. Content production scales only after the complete system works.

### 20.3 Local data loss

**Risk:** Guests clear browser data or change devices.

**Mitigation:** Clear warning, JSON export and restore, optional account sync, and local-first durable storage.

### 20.4 Platform dependency

**Risk:** Codex Sites constraints or availability change.

**Mitigation:** Static portable output, isolated platform configuration, and deployment validation in the prototype milestone.

### 20.5 Synchronization corruption

**Risk:** Devices overwrite each other's progress.

**Mitigation:** Immutable review events, idempotent merges, tombstones for set removal, scheduler recomputation, and deterministic conflict tests.

### 20.6 Open-source licensing confusion

**Risk:** Contributors or downstream users misunderstand which license applies.

**Mitigation:** Separate root code license and content license, clear file-path coverage, contribution notice, and generated-site attribution guidance.

### 20.7 Hosted operating cost

**Risk:** The official service outgrows free infrastructure limits.

**Mitigation:** No permanent-free promise, static public content, local guest learning, portable deployment, and the ability to introduce sustainable hosted-service policies without changing the open-source licenses.

## 21. Licensing

- Source code is licensed under Apache License 2.0.
- Terminology, translations, quizzes, analogies, explanations, and other editorial content are licensed under CC BY-SA 4.0.
- Repository documentation explicitly identifies which paths are code and which paths are content.
- The official hosted service may adopt future pricing or limits without altering the rights granted by the open-source licenses.

## 22. Approval and change control

This document records the approved product and architecture direction. Implementation changes that alter any of the following require an explicit specification amendment:

- Canonical content language
- Supported locale set
- GitHub as content source of truth
- Guest access to the full learning system
- Local-first data storage
- Supabase's user-data-only role
- Selected license pair
- Dictionary-first information architecture
- Public-release baseline coverage requirement

Lower-level implementation choices may change through the normal engineering plan when they preserve the behavior and boundaries defined here.
