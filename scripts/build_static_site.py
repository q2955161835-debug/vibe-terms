from __future__ import annotations

import datetime as dt
import html
import json
import os
import shutil
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
WEB = ROOT / "web"
OUT = ROOT / "site"
ASSETS = OUT / "assets"
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
GITHUB_URL = os.environ.get("GITHUB_URL", "").strip()
PRODUCT_NAME = "Vibe Terms"
LOCALES = ["en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru", "hi"]
HTML_LANG = {
    "en": "en",
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "ja": "ja",
    "ko": "ko",
    "de": "de",
    "ru": "ru",
    "hi": "hi",
}
LANG_NAMES = {
    "en": "English",
    "zh-cn": "简体中文",
    "zh-tw": "繁體中文",
    "ja": "日本語",
    "ko": "한국어",
    "de": "Deutsch",
    "ru": "Русский",
    "hi": "हिन्दी",
}
RUNTIME_MESSAGE_KEYS = (
    "no_results",
    "load_error",
    "loading",
    "done",
    "storage_error",
    "added",
    "queued",
    "copy",
    "copied",
    "copy_failed",
    "theme_system",
    "theme_light",
    "theme_dark",
)
REQUIRED_LOCALIZED_FIELDS = (
    "title",
    "short_definition",
    "analogy",
    "why_it_matters",
    "ai_prompt_example",
    "common_mistake",
    "status",
    "source_content_version",
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def json_script(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def public_url(path: str) -> str:
    return f"{SITE_URL}{path}" if SITE_URL else path


UI: dict[str, dict[str, str]] = read_yaml(CONTENT / "ui.yaml")
domains: list[dict[str, str]] = read_yaml(CONTENT / "taxonomy/domains.yaml")[
    "domains"
]
stages: list[dict[str, str]] = read_yaml(CONTENT / "taxonomy/lifecycle.yaml")[
    "stages"
]
learning_path: dict[str, Any] = read_yaml(
    CONTENT / "paths/zero-to-vibe.yaml"
)
LEARNING_ORDER = {
    slug: index for index, slug in enumerate(learning_path["terms"], start=1)
}

metas: list[dict[str, Any]] = []
for directory in (CONTENT / "terms").iterdir():
    if directory.is_dir():
        metas.append(read_yaml(directory / "meta.yaml"))
metas.sort(
    key=lambda meta: (
        LEARNING_ORDER.get(meta["slug"], 10_000),
        meta["slug"],
    )
)


def validate_content() -> None:
    if sorted(UI) != sorted(LOCALES):
        raise ValueError("content/ui.yaml must define exactly the supported locales")

    baseline_ui_keys = set(UI["en"])
    for locale in LOCALES:
        missing_ui = baseline_ui_keys - set(UI[locale])
        if missing_ui:
            raise ValueError(f"{locale} UI is missing: {sorted(missing_ui)}")
        for key in RUNTIME_MESSAGE_KEYS:
            if not UI[locale].get(key):
                raise ValueError(f"{locale} UI is missing runtime message: {key}")

    domain_ids = {domain["id"] for domain in domains}
    stage_ids = {stage["id"] for stage in stages}
    slugs = {meta["slug"] for meta in metas}
    path_slugs = set(learning_path["terms"])
    if slugs != path_slugs:
        raise ValueError(
            "canonical learning path must include every term exactly once: "
            f"missing={sorted(slugs - path_slugs)}, extra={sorted(path_slugs - slugs)}"
        )

    canonical_names = {meta["canonical_name"] for meta in metas}
    for meta in metas:
        slug = meta["slug"]
        term_dir = CONTENT / "terms" / slug
        if term_dir.name != slug:
            raise ValueError(f"term directory and slug differ for {slug}")
        if meta["primary_domain"] not in domain_ids:
            raise ValueError(f"unknown domain for {slug}: {meta['primary_domain']}")
        if meta["lifecycle_stage"] not in stage_ids:
            raise ValueError(f"unknown lifecycle stage for {slug}")
        for related in meta.get("related_terms", []):
            if related not in canonical_names:
                raise ValueError(f"unknown related term for {slug}: {related}")
        for locale in LOCALES:
            content_path = term_dir / f"{locale}.yaml"
            localized = read_yaml(content_path)
            missing = [
                field for field in REQUIRED_LOCALIZED_FIELDS if field not in localized
            ]
            if missing:
                raise ValueError(f"{content_path} is missing {missing}")
            if localized["source_content_version"] != meta["content_version"]:
                raise ValueError(f"stale source_content_version in {content_path}")


def locale_terms(locale: str) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []
    for meta in metas:
        localized = read_yaml(CONTENT / "terms" / meta["slug"] / f"{locale}.yaml")
        terms.append(
            {
                **meta,
                **localized,
                "learning_order": LEARNING_ORDER[meta["slug"]],
                "domain_title": domain_label(meta["primary_domain"], locale),
            }
        )
    return terms


def domain_label(domain_id: str, locale: str) -> str:
    return next(domain[locale] for domain in domains if domain["id"] == domain_id)


def runtime_messages(locale: str) -> dict[str, str]:
    return {key: UI[locale][key] for key in RUNTIME_MESSAGE_KEYS}


def base_head(
    locale: str,
    title: str,
    description: str,
    path: str,
    *,
    robots: str = "index,follow",
    structured_data: object | None = None,
) -> str:
    page_path = f"/{locale}{path}"
    canonical = public_url(page_path)
    alternates = "\n".join(
        [
            f'<link rel="alternate" hreflang="{HTML_LANG[code]}" href="{esc(public_url(f"/{code}{path}"))}" />'
            for code in LOCALES
        ]
        + [f'<link rel="alternate" hreflang="x-default" href="{esc(public_url("/"))}" />']
    )
    structured = ""
    if structured_data is not None:
        structured = (
            f'<script type="application/ld+json">{json_script(structured_data)}</script>'
        )

    return f'''<!doctype html><html lang="{esc(HTML_LANG[locale])}"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)} · {PRODUCT_NAME}</title><meta name="description" content="{esc(description)}"/><meta name="robots" content="{esc(robots)}"/><meta name="color-scheme" content="light dark"/>
<meta property="og:type" content="website"/><meta property="og:title" content="{esc(title)} · {PRODUCT_NAME}"/><meta property="og:description" content="{esc(description)}"/><meta property="og:url" content="{esc(canonical)}"/>
<link rel="icon" href="/assets/logo.svg" type="image/svg+xml"/><link rel="stylesheet" href="/assets/styles.css"/><link rel="manifest" href="/manifest.webmanifest"/><link rel="canonical" href="{esc(canonical)}"/>{alternates}
<script>try{{document.documentElement.dataset.theme=localStorage.getItem('vibe-theme')||'system'}}catch(e){{document.documentElement.dataset.theme='system'}}</script>{structured}</head>'''


def locale_picker(locale: str, path: str = "/") -> str:
    options = "".join(
        f'<option value="{code}" {"selected" if code == locale else ""}>{esc(LANG_NAMES[code])}</option>'
        for code in LOCALES
    )
    return (
        f'<select class="locale-picker" data-locale-picker aria-label="Language" data-path="{esc(path)}">'
        f"{options}</select>"
    )


def nav(locale: str, path: str = "/") -> str:
    ui = UI[locale]
    return f'''<header class="topbar"><a class="brand" href="/{locale}/"><img src="/assets/logo.svg" alt="" width="25" height="25"/><span>VIBE TERMS</span></a><nav aria-label="Primary"><a href="/{locale}/">{esc(ui['home'])}</a><a href="/{locale}/#all-terms">{esc(ui['terms'])}</a><a href="/{locale}/learn/">{esc(ui['learn'])}</a></nav><div class="nav-actions">{locale_picker(locale, path)}<button class="theme-toggle" type="button" aria-label="{esc(ui['theme_system'])}" title="{esc(ui['theme_system'])}">◐</button></div></header>'''


def shell(
    locale: str,
    title: str,
    description: str,
    body: str,
    path: str = "/",
    *,
    robots: str = "index,follow",
    structured_data: object | None = None,
) -> str:
    messages = json_script(runtime_messages(locale))
    source_link = (
        f'<a href="{esc(GITHUB_URL)}">{esc(UI[locale]["source_code"])}</a>'
        if GITHUB_URL
        else ""
    )
    return (
        base_head(
            locale,
            title,
            description,
            path,
            robots=robots,
            structured_data=structured_data,
        )
        + f'<body><a class="skip-link" href="#main-content">{esc(UI[locale]["skip"])}</a>{nav(locale, path)}'
        + f'<main id="main-content">{body}</main><footer><span>{PRODUCT_NAME} · Apache-2.0 code · CC BY-SA 4.0 content</span>{source_link}</footer>'
        + f'<script type="application/json" id="ui-messages">{messages}</script><script src="/assets/core.js" defer></script><script src="/assets/app.js" defer></script></body></html>'
    )


def prepare_output() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    ASSETS.mkdir(parents=True, exist_ok=True)
    for filename in ("app.js", "core.js", "styles.css", "logo.svg"):
        shutil.copy2(WEB / filename, ASSETS / filename)


def language_links(class_name: str = "chip") -> str:
    return "".join(
        f'<a class="{class_name}" href="/{code}/">{esc(LANG_NAMES[code])}</a>'
        for code in LOCALES
    )


def build_gateway() -> None:
    cards = "".join(
        f'<a class="language-card" href="/{code}/"><strong>{esc(LANG_NAMES[code])}</strong><span>{esc(code)}</span></a>'
        for code in LOCALES
    )
    fallback = language_links()
    root_page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Choose language · {PRODUCT_NAME}</title><meta name="description" content="Choose a language for the multilingual Vibe Coding terminology dictionary."/><meta name="robots" content="index,follow"/><meta name="color-scheme" content="light dark"/><link rel="icon" href="/assets/logo.svg" type="image/svg+xml"/><link rel="stylesheet" href="/assets/styles.css"/><link rel="manifest" href="/manifest.webmanifest"/><script>try{{document.documentElement.dataset.theme=localStorage.getItem('vibe-theme')||'system'}}catch(e){{document.documentElement.dataset.theme='system'}}</script></head><body><a class="skip-link" href="#main-content">Skip to content</a><main id="main-content" class="language-fallback"><p class="gateway-brand">VIBE TERMS</p><h1>Choose your language</h1><p>A beginner-first Vibe Coding terminology dictionary with local, no-login learning.</p><div class="language-grid">{cards}</div><p class="browser-recommendation" aria-live="polite"></p><noscript><section><h2>Language links</h2><p>JavaScript is optional. Choose a language directly:</p><div class="language-list">{fallback}</div></section></noscript></main><script>try{{const saved=localStorage.getItem('vibe-locale');const raw=(navigator.language||'en').toLowerCase();const detected=raw.startsWith('zh-tw')||raw.startsWith('zh-hk')?'zh-tw':raw.startsWith('zh')?'zh-cn':raw.startsWith('ja')?'ja':raw.startsWith('ko')?'ko':raw.startsWith('de')?'de':raw.startsWith('ru')?'ru':raw.startsWith('hi')?'hi':'en';const preferred=saved||detected;const link=document.querySelector(`a[href="/${{preferred}}/"]`);if(link){{link.classList.add('recommended');document.querySelector('.browser-recommendation').textContent=`Suggested: ${{link.querySelector('strong').textContent}}`;}}}}catch(e){{}}</script></body></html>'''
    (OUT / "index.html").write_text(root_page, encoding="utf-8")


def term_rows(terms: list[dict[str, Any]], locale: str) -> str:
    return "".join(
        f'<a class="term-row" data-domain="{esc(term["primary_domain"])}" href="/{locale}/terms/{term["slug"]}/"><span><strong>{esc(term["title"])}</strong><small>{esc(term["canonical_name"]) if term["title"] != term["canonical_name"] else esc(term["short_definition"])}</small></span><em>{esc(term["domain_title"])}</em></a>'
        for term in terms
    )


def build_category_pages(
    locale: str,
    terms: list[dict[str, Any]],
    sitemap_paths: list[str],
) -> None:
    ui = UI[locale]
    categories_dir = OUT / locale / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)

    for domain in domains:
        domain_terms = [
            term for term in terms if term["primary_domain"] == domain["id"]
        ]
        if not domain_terms:
            continue
        domain_name = domain[locale]
        intro = ui["category_intro"].format(
            count=len(domain_terms), domain=domain_name
        )
        page_path = f'/categories/{domain["id"]}/'
        body = f'''<section class="category-hero"><a class="back" href="/{locale}/#all-terms">← {esc(ui['category_back'])}</a><div class="eyebrow">{esc(ui['knowledge'])}</div><h1>{esc(domain_name)}</h1><p>{esc(intro)}</p></section><section class="category-list"><div class="section-head"><h2>{esc(ui['all_terms'])}</h2><span>{len(domain_terms)}</span></div><div class="term-list">{term_rows(domain_terms, locale)}</div></section>'''
        structured_data = {
            "@context": "https://schema.org",
            "@type": "DefinedTermSet",
            "name": domain_name,
            "description": intro,
            "url": public_url(f"/{locale}{page_path}"),
            "hasDefinedTerm": [
                {
                    "@type": "DefinedTerm",
                    "name": term["canonical_name"],
                    "url": public_url(f'/{locale}/terms/{term["slug"]}/'),
                }
                for term in domain_terms
            ],
        }
        publishable = all(term["status"] == "published" for term in domain_terms)
        category_dir = categories_dir / domain["id"]
        category_dir.mkdir(parents=True, exist_ok=True)
        (category_dir / "index.html").write_text(
            shell(
                locale,
                domain_name,
                intro,
                body,
                page_path,
                robots="index,follow" if publishable else "noindex,follow",
                structured_data=structured_data,
            ),
            encoding="utf-8",
        )
        if publishable:
            sitemap_paths.append(f"/{locale}{page_path}")


def build_locale(locale: str, sitemap_paths: list[str]) -> None:
    ui = UI[locale]
    terms = locale_terms(locale)
    locale_dir = OUT / locale
    (locale_dir / "terms").mkdir(parents=True, exist_ok=True)
    (locale_dir / "learn").mkdir(parents=True, exist_ok=True)

    public_terms = [
        {
            key: term[key]
            for key in (
                "slug",
                "canonical_name",
                "aliases",
                "primary_domain",
                "domain_title",
                "lifecycle_stage",
                "difficulty",
                "learning_order",
                "title",
                "short_definition",
                "analogy",
                "why_it_matters",
                "ai_prompt_example",
                "status",
            )
        }
        for term in terms
    ]
    (ASSETS / f"terms.{locale}.json").write_text(
        json.dumps(public_terms, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    cards: list[str] = []
    for domain in domains:
        domain_terms = [
            term for term in terms if term["primary_domain"] == domain["id"]
        ]
        if not domain_terms:
            continue
        examples = " · ".join(esc(term["title"]) for term in domain_terms[:3])
        cards.append(
            f'<a class="domain-card" href="/{locale}/categories/{domain["id"]}/"><span class="domain-name">{esc(domain[locale])}</span><span class="domain-examples">{examples}</span><strong>{len(domain_terms)} {esc(ui["terms_unit"])}</strong></a>'
        )

    stage_html = "".join(
        f'<div class="stage"><span>{index + 1:02d}</span><strong>{esc(stage[locale])}</strong></div>'
        for index, stage in enumerate(stages)
    )
    first_terms = "".join(
        f'<a class="chip" href="/{locale}/terms/{term["slug"]}/">{esc(term["title"])}</a>'
        for term in terms[:6]
    )
    home_body = f'''<section class="hero"><div class="eyebrow">{esc(ui['hero_eyebrow'])}</div><h1>{esc(ui['hero'])}</h1><p>{esc(ui['sub'])}</p><form id="home-search-form" class="search-wrap" role="search"><div class="search-shell"><input id="home-search" autocomplete="off" data-locale="{locale}" placeholder="{esc(ui['search'])}" aria-label="{esc(ui['search'])}" role="combobox" aria-autocomplete="list" aria-controls="search-results" aria-expanded="false"/><button type="submit">{esc(ui['search_btn'])}</button></div><div id="search-results" class="search-results" role="listbox" aria-live="polite" hidden></div></form></section>
<section><div class="section-head"><h2>{esc(ui['knowledge'])}</h2><a href="#all-terms">{esc(ui['all_terms'])}</a></div><div class="domain-grid">{''.join(cards)}</div></section>
<section><div class="section-head"><h2>{esc(ui['route'])}</h2><a href="/{locale}/learn/">{esc(ui['learn'])}</a></div><div class="stage-grid">{stage_html}</div></section>
<section><div class="section-head"><h2>{esc(ui['trending'])}</h2></div><div class="chip-row">{first_terms}</div></section>
<div class="callout"><strong>{esc(ui['learn_title'])}</strong><span>{esc(ui['learn_sub'])}</span><a class="button" href="/{locale}/learn/">{esc(ui['start'])}</a></div>
<section id="all-terms"><div class="section-head"><h2>{esc(ui['all_terms'])}</h2><span>{len(terms)}</span></div><div class="term-list">{term_rows(terms, locale)}</div></section>'''
    home_publishable = all(term["status"] == "published" for term in terms)
    (locale_dir / "index.html").write_text(
        shell(
            locale,
            "Vibe Coding Terms",
            ui["sub"],
            home_body,
            "/",
            robots="index,follow" if home_publishable else "noindex,follow",
        ),
        encoding="utf-8",
    )
    if home_publishable:
        sitemap_paths.append(f"/{locale}/")

    build_category_pages(locale, terms, sitemap_paths)

    for term in terms:
        status = (
            f'<span class="status">{esc(ui["draft"])}</span>'
            if term["status"] != "published"
            else ""
        )
        related: list[str] = []
        for related_name in term.get("related_terms", []):
            match = next(
                (
                    candidate
                    for candidate in terms
                    if candidate["canonical_name"] == related_name
                ),
                None,
            )
            if match:
                related.append(
                    f'<a class="chip" href="/{locale}/terms/{match["slug"]}/">{esc(match["title"])}</a>'
                )
        term_body = f'''<article class="term-detail"><a class="back" href="/{locale}/">← {esc(ui['back'])}</a><div class="term-heading"><div><div class="meta-line"><a href="/{locale}/categories/{term['primary_domain']}/">{esc(term['domain_title'])}</a>{status}</div><h1>{esc(term['title'])}</h1><p class="canonical">{esc(term['canonical_name'])}</p></div><button class="learn-one" type="button" data-term="{esc(term['slug'])}" aria-pressed="false">+ {esc(ui['learn'])}</button></div><p class="lead">{esc(term['short_definition'])}</p><div class="detail-grid"><section><h2>{esc(ui['analogy'])}</h2><p>{esc(term['analogy'])}</p></section><section><h2>{esc(ui['why'])}</h2><p>{esc(term['why_it_matters'])}</p></section></div><section class="prompt-box"><h2>{esc(ui['prompt'])}</h2><pre>{esc(term['ai_prompt_example'])}</pre><button class="copy-prompt" type="button" data-copy="{esc(term['ai_prompt_example'])}">{esc(ui['copy'])}</button></section><section><h2>{esc(ui['mistake'])}</h2><p>{esc(term['common_mistake'])}</p></section><section><h2>{esc(ui['related'])}</h2><div class="chip-row">{''.join(related) or '—'}</div></section></article>'''
        page_path = f"/terms/{term['slug']}/"
        structured_data = {
            "@context": "https://schema.org",
            "@type": "DefinedTerm",
            "name": term["canonical_name"],
            "alternateName": [term["title"], *term.get("aliases", [])],
            "description": term["short_definition"],
            "url": public_url(f"/{locale}{page_path}"),
            "inDefinedTermSet": PRODUCT_NAME,
        }
        term_dir = locale_dir / "terms" / term["slug"]
        term_dir.mkdir(parents=True, exist_ok=True)
        (term_dir / "index.html").write_text(
            shell(
                locale,
                term["title"],
                term["short_definition"],
                term_body,
                page_path,
                robots=(
                    "index,follow"
                    if term["status"] == "published"
                    else "noindex,follow"
                ),
                structured_data=structured_data,
            ),
            encoding="utf-8",
        )
        if term["status"] == "published":
            sitemap_paths.append(f"/{locale}{page_path}")

    learn_body = f'''<section class="learn-header"><div><div class="eyebrow">{esc(ui['learning_eyebrow'])}</div><h1>{esc(ui['learn_title'])}</h1><p>{esc(ui['learn_sub'])}</p></div><label class="daily-setting">{esc(ui['daily'])}<input id="daily-count" type="number" min="1" max="30" value="3" inputmode="numeric"/></label></section><div class="learning-stats"><strong id="learn-progress">0 / 0</strong><span class="storage-note">{esc(ui['local'])}</span></div><div id="learning-status" class="learning-status" role="status" hidden></div><section id="learning-card" class="learning-card" aria-live="polite"><div class="learning-empty"><button class="button" id="start-learning" type="button">{esc(ui['start'])}</button></div></section><template id="learning-template"><div class="learn-meta"><span class="learn-position"></span><span class="learn-domain"></span></div><h2 class="learn-title" tabindex="-1"></h2><p class="learn-canonical"></p><button class="reveal button-secondary" type="button">{esc(ui['reveal'])}</button><div class="learn-answer" hidden><p class="learn-definition"></p><p class="learn-analogy"></p><div class="rating-row"><button type="button" data-rating="again">{esc(ui['again'])}</button><button type="button" data-rating="partial">{esc(ui['partial'])}</button><button type="button" data-rating="mastered">{esc(ui['mastered'])}</button></div></div></template>'''
    (locale_dir / "learn" / "index.html").write_text(
        shell(
            locale,
            ui["learn_title"],
            ui["learn_sub"],
            learn_body,
            "/learn/",
            robots="noindex,follow",
        ),
        encoding="utf-8",
    )


def build_deployment_artifacts(sitemap_paths: list[str]) -> None:
    manifest = {
        "name": PRODUCT_NAME,
        "short_name": PRODUCT_NAME,
        "description": "A multilingual Vibe Coding terminology dictionary for beginners.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#3457f1",
        "lang": "en",
        "icons": [
            {
                "src": "/assets/logo.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any",
            }
        ],
    }
    (OUT / "manifest.webmanifest").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    robots_lines = ["User-agent: *", "Allow: /"]
    if SITE_URL:
        robots_lines.append(f"Sitemap: {SITE_URL}/sitemap.xml")
    (OUT / "robots.txt").write_text(
        "\n".join(robots_lines) + "\n", encoding="utf-8"
    )

    if SITE_URL:
        sitemap_urls = "".join(
            f"<url><loc>{esc(public_url(path))}</loc></url>"
            for path in sorted(set(sitemap_paths))
        )
    else:
        sitemap_urls = "<!-- Rebuild with SITE_URL set before production indexing. -->"
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{sitemap_urls}</urlset>",
        encoding="utf-8",
    )

    not_found_page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Page not found · {PRODUCT_NAME}</title><meta name="robots" content="noindex,follow"/><link rel="icon" href="/assets/logo.svg" type="image/svg+xml"/><link rel="stylesheet" href="/assets/styles.css"/></head><body><a class="skip-link" href="#main-content">Skip to content</a><main id="main-content" class="language-fallback"><p class="gateway-brand">VIBE TERMS</p><h1>Page not found</h1><p>The link may be outdated. Choose a language and continue exploring.</p><div class="language-list">{language_links()}</div></main></body></html>'''
    (OUT / "404.html").write_text(not_found_page, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    build_info = {
        "builtAt": dt.datetime.now(dt.UTC).isoformat(),
        "locales": LOCALES,
        "termCount": len(metas),
        "categoryCount": len(domains),
        "siteUrl": SITE_URL or None,
        "authentication": False,
    }
    (OUT / "build-info.json").write_text(
        json.dumps(build_info, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    validate_content()
    prepare_output()
    build_gateway()
    sitemap_paths = ["/"]
    for locale in LOCALES:
        build_locale(locale, sitemap_paths)
    build_deployment_artifacts(sitemap_paths)
    print(
        f"built {len(LOCALES)} locales, {len(domains)} categories, "
        f"and {len(metas)} terms"
    )


if __name__ == "__main__":
    main()
