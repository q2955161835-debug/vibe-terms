from __future__ import annotations

import datetime as dt
import html
import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from .config import HTML_LANG, LANGUAGE_NAMES, PRODUCT_NAME, BuildConfig
from .indexes import (
    build_exercises_index,
    build_knowledge_graph,
    build_search_index,
    build_terms_index,
)
from .models import Catalog
from .urls import UrlBuilder


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _json(value: object, *, pretty: bool = False) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ).replace("</", "<\\/")


def _read_ui(content_root: Path, locales: tuple[str, ...]) -> dict[str, dict[str, str]]:
    raw = yaml.safe_load((content_root / "ui.yaml").read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != set(locales):
        raise ValueError("content/ui.yaml must define exactly the supported locales")
    return raw


def _domain_name(domain: dict[str, Any], locale: str) -> str:
    return str(domain.get(locale) or domain.get("en") or domain["id"])


def _route_file(output_root: Path, route: str) -> Path:
    if route == "/":
        return output_root / "index.html"
    relative = route.strip("/")
    return output_root / relative / "index.html"


def _write_page(output_root: Path, route: str, value: str) -> None:
    target = _route_file(output_root, route)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def _is_external(url: str) -> bool:
    return url.startswith(("https://", "http://", "mailto:", "tel:"))


class SiteRenderer:
    def __init__(self, config: BuildConfig, catalog: Catalog) -> None:
        self.config = config
        self.catalog = catalog
        self.urls = UrlBuilder(config.site_url, config.base_path)
        self.ui = _read_ui(config.content_root, catalog.locales)
        self.output = config.output_root
        self.assets = self.output / "assets"
        self.web = config.content_root.parent / "web"
        self.routes: list[str] = []
        self.sitemap_routes: list[str] = ["/"]
        self.term_by_slug = {term["slug"]: term for term in catalog.terms}
        self.topic_by_id = {topic["id"]: topic for topic in catalog.topics}

    def prepare(self) -> None:
        forbidden = {
            self.config.content_root,
            self.config.content_root.parent,
            Path(self.output.anchor),
        }
        if self.output in forbidden:
            raise ValueError(f"refusing unsafe output_root: {self.output}")
        if self.output.exists():
            shutil.rmtree(self.output)
        self.assets.mkdir(parents=True)
        for filename in ("app.js", "core.js", "examples.js", "styles.css", "logo.svg"):
            source = self.web / filename
            if not source.is_file():
                raise ValueError(f"missing required browser asset: {source}")
            shutil.copy2(source, self.assets / filename)

    def add_page(self, route: str, page: str, *, indexable: bool = False) -> None:
        _write_page(self.output, route, page)
        self.routes.append(route)
        if indexable:
            self.sitemap_routes.append(route)

    def label(self, locale: str, key: str, fallback: str) -> str:
        return str(self.ui[locale].get(key) or fallback)

    def head(
        self,
        locale: str,
        title: str,
        description: str,
        locale_path: str,
        *,
        robots: str,
        structured_data: object | None = None,
        canonical_path: str | None = None,
    ) -> str:
        route = f"/{locale}{locale_path}"
        canonical_route = canonical_path or route
        alternate_links = "".join(
            f'<link rel="alternate" hreflang="{HTML_LANG[code]}" href="{_esc(self.urls.absolute(f"/{code}{locale_path}"))}" />'
            for code in self.catalog.locales
        )
        alternate_links += (
            f'<link rel="alternate" hreflang="x-default" href="{_esc(self.urls.absolute("/"))}" />'
        )
        structured = (
            f'<script type="application/ld+json">{_json(structured_data, pretty=True)}</script>'
            if structured_data is not None
            else ""
        )
        return (
            f'<!doctype html><html lang="{_esc(HTML_LANG[locale])}" '
            f'data-base-path="{_esc(self.config.base_path)}" '
            f'data-search-index="{_esc(self.urls.asset(f"assets/search-index.{locale}.json"))}" '
            f'data-exercise-index="{_esc(self.urls.asset(f"assets/exercises.{locale}.json"))}"><head>'
            '<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>'
            f'<title>{_esc(title)} · {PRODUCT_NAME}</title>'
            f'<meta name="description" content="{_esc(description)}"/>'
            f'<meta name="robots" content="{_esc(robots)}"/><meta name="color-scheme" content="light dark"/>'
            f'<meta property="og:type" content="website"/><meta property="og:title" content="{_esc(title)} · {PRODUCT_NAME}"/>'
            f'<meta property="og:description" content="{_esc(description)}"/>'
            f'<meta property="og:url" content="{_esc(self.urls.absolute(canonical_route))}"/>'
            f'<link rel="icon" href="{_esc(self.urls.asset("assets/logo.svg"))}" type="image/svg+xml"/>'
            f'<link rel="stylesheet" href="{_esc(self.urls.asset("assets/styles.css"))}"/>'
            f'<link rel="manifest" href="{_esc(self.urls.page("manifest.webmanifest"))}"/>'
            f'<link rel="canonical" href="{_esc(self.urls.absolute(canonical_route))}"/>'
            f'{alternate_links}<script>try{{document.documentElement.dataset.theme=localStorage.getItem("vibe-theme")||"system"}}catch(e){{document.documentElement.dataset.theme="system"}}</script>'
            f'{structured}</head>'
        )

    def search_form(self, locale: str, *, mobile: bool = False) -> str:
        suffix = "mobile" if mobile else "desktop"
        search_label = self.label(locale, "search", "Search terms, topics, and paths")
        return (
            f'<form class="global-search {suffix}-search" data-global-search role="search">'
            f'<label class="visually-hidden" for="global-search-{suffix}">{_esc(search_label)}</label>'
            f'<input id="global-search-{suffix}" type="search" data-search-input autocomplete="off" '
            f'placeholder="{_esc(search_label)}" role="combobox" aria-autocomplete="list" '
            f'aria-controls="global-results-{suffix}" aria-expanded="false"/>'
            f'<button type="submit">{_esc(self.label(locale, "search_btn", "Search"))}</button>'
            f'<div id="global-results-{suffix}" class="search-results" data-search-results role="listbox" aria-live="polite" hidden></div>'
            '</form>'
        )

    def header(self, locale: str, locale_path: str) -> str:
        options = "".join(
            f'<option value="{code}" {"selected" if code == locale else ""}>{_esc(LANGUAGE_NAMES[code])}</option>'
            for code in self.catalog.locales
        )
        return (
            '<header class="topbar">'
            f'<a class="brand" href="{_esc(self.urls.page(f"/{locale}/"))}"><img src="{_esc(self.urls.asset("assets/logo.svg"))}" alt="" width="25" height="25"/><span>VIBE TERMS</span></a>'
            '<nav aria-label="Primary">'
            f'<a href="{_esc(self.urls.page(f"/{locale}/terms/"))}">{_esc(self.label(locale, "terms", "Terms"))}</a>'
            f'<a href="{_esc(self.urls.page(f"/{locale}/knowledge/"))}">{_esc(self.label(locale, "knowledge", "Knowledge"))}</a>'
            f'<a href="{_esc(self.urls.page(f"/{locale}/paths/"))}">{_esc(self.label(locale, "route", "Paths"))}</a>'
            f'<a href="{_esc(self.urls.page(f"/{locale}/practice/"))}">{_esc(self.label(locale, "practice", "Practice"))}</a>'
            '</nav>'
            f'{self.search_form(locale)}'
            '<div class="nav-actions">'
            f'<button type="button" data-search-open aria-haspopup="dialog">{_esc(self.label(locale, "search_btn", "Search"))}</button>'
            f'<select class="locale-picker" data-locale-picker data-path="{_esc(locale_path)}" aria-label="{_esc(self.label(locale, "language", "Language"))}">{options}</select>'
            f'<button class="theme-toggle" type="button" aria-label="{_esc(self.label(locale, "theme_system", "Use system theme"))}">◐</button>'
            '</div></header>'
            '<dialog id="mobile-search-dialog">'
            f'<button type="button" data-search-close aria-label="{_esc(self.label(locale, "close", "Close"))}">×</button>{self.search_form(locale, mobile=True)}'
            '</dialog>'
        )

    def shell(
        self,
        locale: str,
        title: str,
        description: str,
        body: str,
        locale_path: str,
        *,
        indexable: bool,
        structured_data: object | None = None,
        canonical_path: str | None = None,
    ) -> str:
        robots = "index,follow" if indexable else "noindex,follow"
        runtime_keys = (
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
            "practice_complete",
            "open_exercise",
            "next",
            "practice_unavailable",
        )
        runtime = {key: self.ui[locale].get(key, key) for key in runtime_keys}
        return (
            self.head(
                locale,
                title,
                description,
                locale_path,
                robots=robots,
                structured_data=structured_data,
                canonical_path=canonical_path,
            )
            + f'<body data-base-path="{_esc(self.config.base_path)}"><a class="skip-link" href="#main-content">{_esc(self.label(locale, "skip", "Skip to content"))}</a>'
            + self.header(locale, locale_path)
            + f'<main id="main-content">{body}</main>'
            + f'<footer><span>{PRODUCT_NAME} · Apache-2.0 code · CC BY-SA 4.0 content</span></footer>'
            + f'<script type="application/json" id="ui-messages">{_json(runtime)}</script>'
            + f'<script src="{_esc(self.urls.asset("assets/core.js"))}" defer></script>'
            + f'<script src="{_esc(self.urls.asset("assets/examples.js"))}" defer></script>'
            + f'<script src="{_esc(self.urls.asset("assets/app.js"))}" defer></script></body></html>'
        )

    def term_link(self, locale: str, term: dict[str, Any], *, row: bool = False) -> str:
        localized = term["localized"][locale]
        class_name = "term-row" if row else "chip"
        details = (
            f'<span><strong>{_esc(localized["title"])}</strong><small>{_esc(term["canonical_name"])}</small></span>'
            f'<em>{_esc(localized["short_definition"])}</em>'
            if row
            else _esc(localized["title"])
        )
        return (
            f'<a class="{class_name}" data-domain="{_esc(term["primary_domain"])}" '
            f'href="{_esc(self.urls.page(f"/{locale}/terms/{term["slug"]}/"))}">{details}</a>'
        )

    def term_list(self, locale: str, terms: list[dict[str, Any]]) -> str:
        return '<div class="term-list">' + "".join(
            self.term_link(locale, term, row=True) for term in terms
        ) + "</div>"

    def build_gateway(self) -> None:
        cards = "".join(
            f'<a class="language-card" href="{_esc(self.urls.page(f"/{locale}/"))}"><strong>{_esc(LANGUAGE_NAMES[locale])}</strong><span>{_esc(locale)}</span></a>'
            for locale in self.catalog.locales
        )
        fallback = "".join(
            f'<a class="chip" href="{_esc(self.urls.page(f"/{locale}/"))}">{_esc(LANGUAGE_NAMES[locale])}</a>'
            for locale in self.catalog.locales
        )
        page = (
            f'<!doctype html><html lang="en" data-base-path="{_esc(self.config.base_path)}" data-search-index="{_esc(self.urls.asset("assets/search-index.en.json"))}" data-exercise-index="{_esc(self.urls.asset("assets/exercises.en.json"))}"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>'
            f'<title>Choose language · {PRODUCT_NAME}</title><meta name="robots" content="index,follow"/>'
            f'<link rel="icon" href="{_esc(self.urls.asset("assets/logo.svg"))}"/><link rel="stylesheet" href="{_esc(self.urls.asset("assets/styles.css"))}"/>'
            f'<link rel="manifest" href="{_esc(self.urls.page("manifest.webmanifest"))}"/><link rel="canonical" href="{_esc(self.urls.absolute("/"))}"/></head><body data-base-path="{_esc(self.config.base_path)}">'
            f'<a class="skip-link" href="#main-content">Skip to content</a>{self.header("en", "/")}<main id="main-content" class="language-fallback"><p class="gateway-brand">VIBE TERMS</p><h1>Choose your language</h1><p>A local-first Vibe Coding terminology guide with no account required.</p><div class="language-grid">{cards}</div>'
            f'<noscript><section><h2>Language links</h2><div class="language-list">{fallback}</div></section></noscript></main><script type="application/json" id="ui-messages">{_json(self.ui["en"])}</script>'
            f'<script src="{_esc(self.urls.asset("assets/core.js"))}" defer></script><script src="{_esc(self.urls.asset("assets/examples.js"))}" defer></script><script src="{_esc(self.urls.asset("assets/app.js"))}" defer></script></body></html>'
        )
        self.add_page("/", page, indexable=True)

    def build_indexes(self, locale: str) -> None:
        payloads = {
            f"terms.{locale}.json": build_terms_index(self.catalog, locale, self.urls),
            f"exercises.{locale}.json": build_exercises_index(
                self.catalog, locale, self.urls
            ),
            f"search-index.{locale}.json": build_search_index(
                self.catalog, locale, self.urls
            ),
            f"knowledge-graph.{locale}.json": build_knowledge_graph(
                self.catalog, locale, self.urls
            ),
        }
        for filename, payload in payloads.items():
            (self.assets / filename).write_text(_json(payload), encoding="utf-8")

    def build_home(self, locale: str) -> None:
        ui = self.ui[locale]
        cards: list[str] = []
        for domain in self.catalog.domains:
            terms = [
                term
                for term in self.catalog.terms
                if term["primary_domain"] == domain["id"]
            ]
            topics = [
                topic for topic in self.catalog.topics if topic["domain"] == domain["id"]
            ]
            samples = " · ".join(topic["names"][locale] for topic in topics[:3])
            cards.append(
                f'<a class="domain-card" href="{_esc(self.urls.page(f"/{locale}/knowledge/{domain["id"]}/"))}"><span class="domain-name">{_esc(_domain_name(domain, locale))}</span><span class="domain-examples">{_esc(samples)}</span><strong>{len(terms)} {_esc(self.label(locale, "terms_unit", "terms"))}</strong></a>'
            )
        paths = "".join(
            f'<a class="path-card" href="{_esc(self.urls.page(f"/{locale}/paths/{path["slug"]}/"))}"><span class="domain-name">{_esc(path["localized"][locale]["title"])}</span><span class="domain-examples">{_esc(path["localized"][locale]["summary"])}</span><strong>{len(path["chapters"])} chapters</strong></a>'
            for path in self.catalog.paths
        )
        first_terms = "".join(
            self.term_link(locale, term) for term in self.catalog.terms[:6]
        )
        body = (
            f'<section class="hero"><div class="eyebrow">{_esc(ui["hero_eyebrow"])}</div><h1>{_esc(ui["hero"])}</h1><p>{_esc(ui["sub"])}</p>'
            f'<form id="home-search-form" class="search-wrap" data-global-search role="search"><div class="search-shell"><input id="home-search" type="search" data-search-input autocomplete="off" placeholder="{_esc(ui["search"])}" aria-label="{_esc(ui["search"])}" role="combobox" aria-autocomplete="list" aria-controls="search-results" aria-expanded="false"/><button type="submit">{_esc(ui["search_btn"])}</button></div><div id="search-results" class="search-results" data-search-results role="listbox" aria-live="polite" hidden></div></form></section>'
            f'<section><div class="section-head"><h2>{_esc(ui["knowledge"])}</h2><a href="{_esc(self.urls.page(f"/{locale}/knowledge/"))}">{_esc(ui["all_terms"])}</a></div><div class="domain-grid">{"".join(cards)}</div></section>'
            f'<section><div class="section-head"><h2>{_esc(ui["route"])}</h2><a href="{_esc(self.urls.page(f"/{locale}/paths/"))}">{_esc(ui["route"])}</a></div><div class="domain-grid">{paths}</div></section>'
            f'<section><div class="section-head"><h2>{_esc(ui["trending"])}</h2></div><div class="chip-row">{first_terms}</div></section>'
        )
        indexable = all(
            term["localized"][locale]["status"] == "published"
            for term in self.catalog.terms
        )
        self.add_page(
            f"/{locale}/",
            self.shell(locale, "Vibe Coding Terms", ui["sub"], body, "/", indexable=indexable),
            indexable=indexable,
        )

    def build_terms(self, locale: str) -> None:
        title = self.label(locale, "all_terms", "All terms")
        body = (
            f'<section class="category-hero"><div class="eyebrow">{_esc(self.label(locale, "terms", "Terms"))}</div><h1>{_esc(title)}</h1><p>{len(self.catalog.terms)} terms across {len(self.catalog.domains)} domains.</p></section>'
            + self.term_list(locale, list(self.catalog.terms))
        )
        indexable = all(
            term["localized"][locale]["status"] == "published"
            for term in self.catalog.terms
        )
        self.add_page(
            f"/{locale}/terms/",
            self.shell(locale, title, title, body, "/terms/", indexable=indexable),
            indexable=indexable,
        )

    def build_knowledge(self, locale: str) -> None:
        title = self.label(locale, "knowledge", "Knowledge map")
        domain_sections: list[str] = []
        for domain in self.catalog.domains:
            topics = [
                topic for topic in self.catalog.topics if topic["domain"] == domain["id"]
            ]
            topic_links = "".join(
                f'<li><a href="{_esc(self.urls.page(f"/{locale}/knowledge/{domain["id"]}/{topic["id"]}/"))}">{_esc(topic["names"][locale])}</a> <span>{len(topic["terms"])}</span></li>'
                for topic in topics
            )
            term_links = "".join(
                f'<li>{self.term_link(locale, self.term_by_slug[slug])}</li>'
                for topic in topics
                for slug in topic["terms"]
            )
            domain_sections.append(
                f'<section><h2><a href="{_esc(self.urls.page(f"/{locale}/knowledge/{domain["id"]}/"))}">{_esc(_domain_name(domain, locale))}</a></h2><ul class="topic-list">{topic_links}</ul><details><summary>{_esc(self.label(locale, "all_terms", "All terms"))}</summary><ul>{term_links}</ul></details></section>'
            )
        body = f'<section class="category-hero"><div class="eyebrow">{_esc(title)}</div><h1>{_esc(title)}</h1><p>{_esc(self.label(locale, "knowledge_intro", "Browse domains, topics, and prerequisite relationships."))}</p></section><div class="knowledge-list">{"".join(domain_sections)}</div>'
        indexable = all(
            term["localized"][locale]["status"] == "published"
            for term in self.catalog.terms
        )
        self.add_page(
            f"/{locale}/knowledge/",
            self.shell(locale, title, title, body, "/knowledge/", indexable=indexable),
            indexable=indexable,
        )

    def build_domain_and_topics(self, locale: str) -> None:
        for domain in self.catalog.domains:
            domain_id = domain["id"]
            domain_title = _domain_name(domain, locale)
            domain_terms = [
                term for term in self.catalog.terms if term["primary_domain"] == domain_id
            ]
            topics = [
                topic for topic in self.catalog.topics if topic["domain"] == domain_id
            ]
            topic_links = "".join(
                f'<a class="chip" href="{_esc(self.urls.page(f"/{locale}/knowledge/{domain_id}/{topic["id"]}/"))}">{_esc(topic["names"][locale])} ({len(topic["terms"])})</a>'
                for topic in topics
            )
            body = f'<section class="category-hero"><a class="back" href="{_esc(self.urls.page(f"/{locale}/knowledge/"))}">← {_esc(self.label(locale, "knowledge", "Knowledge"))}</a><h1>{_esc(domain_title)}</h1><div class="chip-row">{topic_links}</div></section>{self.term_list(locale, domain_terms)}'
            indexable = all(
                term["localized"][locale]["status"] == "published"
                for term in domain_terms
            )
            route = f"/{locale}/knowledge/{domain_id}/"
            self.add_page(
                route,
                self.shell(
                    locale,
                    domain_title,
                    domain_title,
                    body,
                    f"/knowledge/{domain_id}/",
                    indexable=indexable,
                ),
                indexable=indexable,
            )
            legacy_route = f"/{locale}/categories/{domain_id}/"
            legacy_body = f'<section class="category-hero"><p>{_esc(self.label(locale, "compatibility_notice", "This category route is kept for compatibility."))}</p><h1>{_esc(domain_title)}</h1><a class="button" href="{_esc(self.urls.page(route))}">{_esc(self.label(locale, "knowledge", "Knowledge"))}</a></section>{self.term_list(locale, domain_terms)}'
            self.add_page(
                legacy_route,
                self.shell(
                    locale,
                    domain_title,
                    domain_title,
                    legacy_body,
                    f"/categories/{domain_id}/",
                    indexable=False,
                    canonical_path=self.urls.page(route),
                ),
            )
            for topic in topics:
                topic_terms = [self.term_by_slug[slug] for slug in topic["terms"]]
                topic_title = topic["names"][locale]
                topic_body = f'<section class="category-hero"><a class="back" href="{_esc(self.urls.page(route))}">← {_esc(domain_title)}</a><h1>{_esc(topic_title)}</h1><p>{_esc(topic["descriptions"][locale])}</p></section>{self.term_list(locale, topic_terms)}'
                topic_indexable = all(
                    term["localized"][locale]["status"] == "published"
                    for term in topic_terms
                )
                topic_route = f"/{locale}/knowledge/{domain_id}/{topic['id']}/"
                self.add_page(
                    topic_route,
                    self.shell(
                        locale,
                        topic_title,
                        topic["descriptions"][locale],
                        topic_body,
                        f"/knowledge/{domain_id}/{topic['id']}/",
                        indexable=topic_indexable,
                    ),
                    indexable=topic_indexable,
                )

    def example_html(
        self, locale: str, term: dict[str, Any], localized: dict[str, Any]
    ) -> str:
        example = term["example"]
        heading = _esc(self.label(locale, "example", "Dynamic example"))
        if example["mode"] == "static":
            return (
                f'<section id="example" data-section="example"><h2>{heading}</h2><div class="example-module" data-example-root data-example-id="{_esc(example["id"])}" data-example-mode="static">'
                f'<p>{_esc(localized["project_example"])}</p><div data-example-state="context"><strong>{_esc(localized["title"])}</strong><p>{_esc(localized["mechanism"])}</p><p>{_esc(localized["boundary"])}</p></div></div></section>'
            )
        return (
            f'<section id="example" data-section="example"><h2>{heading}</h2><div class="example-module" data-example-root data-example-id="{_esc(example["id"])}" data-example-mode="{_esc(example["mode"])}">'
            f'<p>{_esc(localized["project_example"])}</p><div class="example-controls"><button type="button" data-example-control="context" aria-pressed="true">{_esc(self.label(locale, "context", "Context"))}</button><button type="button" data-example-control="verify" aria-pressed="false">{_esc(self.label(locale, "verify", "Verify"))}</button></div>'
            f'<div data-example-state="context"><strong>{_esc(localized["title"])}</strong><p>{_esc(localized["mechanism"])}</p></div>'
            f'<div data-example-state="verify"><strong>{_esc(self.label(locale, "verification_boundary", "Verification boundary"))}</strong><p>{_esc(localized["boundary"])}</p></div>'
            f'<noscript><p>{_esc(self.label(locale, "example_noscript", "Both example states are shown in the text above; JavaScript only enhances the controls."))}</p></noscript></div></section>'
        )

    def exercise_html(self, locale: str, term: dict[str, Any]) -> str:
        localized = term["localized"][locale]
        exercise = {
            **localized["exercise"],
            "id": f"{term['slug']}:{locale}:1",
            "slug": term["slug"],
        }
        choices = "".join(
            f'<label><input type="radio" name="answer" value="{_esc(option["id"])}"/> <span>{_esc(option["label"])}</span></label>'
            for option in exercise["options"]
        )
        return (
            f'<section id="exercise" data-section="exercise"><h2>{_esc(self.label(locale, "exercise", "Exercise"))}</h2><div data-exercise data-content-status="{_esc(exercise["content_status"])}">'
            f'<script type="application/json" data-exercise-payload>{_json(exercise)}</script><form><fieldset><legend>{_esc(exercise["prompt"])}</legend>{choices}</fieldset><button type="submit">{_esc(self.label(locale, "check_answer", "Check answer"))}</button></form><p data-exercise-feedback role="status" hidden></p></div></section>'
        )

    def build_term_pages(self, locale: str) -> None:
        ordered_terms = list(self.catalog.terms)
        for index, term in enumerate(ordered_terms):
            localized = term["localized"][locale]
            related = "".join(
                self.term_link(locale, self.term_by_slug[slug])
                for slug in term.get("related_terms", [])
            ) or "—"
            sources = "".join(
                f'<li><a href="{_esc(source["url"] if _is_external(source["url"]) else self.urls.page(source["url"]))}">{_esc(source["title"])}</a>{f" <small>{_esc(self.label(locale, 'internal_provenance', 'internal provenance'))}</small>" if source.get("kind") == "internal-provenance" else ""}</li>'
                for source in localized["sources"]
            )
            status = (
                ""
                if localized["status"] == "published"
                else f'<span class="status">{_esc(self.label(locale, "draft", "Draft"))}</span>'
            )
            prerequisites = "".join(
                self.term_link(locale, self.term_by_slug[slug])
                for slug in term.get("prerequisites", [])
            ) or f'<span>{_esc(self.label(locale, "no_prerequisites", "No required prerequisite"))}</span>'
            memberships: list[str] = []
            for path in self.catalog.paths:
                for chapter in path["chapters"]:
                    if term["slug"] not in chapter.get("term_slugs", []):
                        continue
                    title = path["localized"][locale]["title"]
                    chapter_title = next(
                        item["title"]
                        for item in path["localized"][locale]["chapters"]
                        if item["id"] == chapter["id"]
                    )
                    memberships.append(
                        f'<a class="chip" href="{_esc(self.urls.page(f"/{locale}/paths/{path["slug"]}/{chapter["id"]}/"))}">{_esc(title)} · {_esc(chapter_title)}</a>'
                    )
            previous_link = ""
            next_link = ""
            if index > 0:
                previous = ordered_terms[index - 1]
                previous_link = f'<a rel="prev" href="{_esc(self.urls.page(f"/{locale}/terms/{previous["slug"]}/"))}">← {_esc(previous["localized"][locale]["title"])}</a>'
            if index + 1 < len(ordered_terms):
                following = ordered_terms[index + 1]
                next_link = f'<a rel="next" href="{_esc(self.urls.page(f"/{locale}/terms/{following["slug"]}/"))}">{_esc(following["localized"][locale]["title"])} →</a>'
            aliases = " · ".join(str(alias) for alias in term.get("aliases", [])) or "—"
            body = (
                f'<article class="term-detail" data-term-page data-term-slug="{_esc(term["slug"])}"><a class="back" href="{_esc(self.urls.page(f"/{locale}/terms/"))}">← {_esc(self.label(locale, "back", "Back"))}</a>'
                f'<div class="term-heading"><div><div class="meta-line"><a href="{_esc(self.urls.page(f"/{locale}/knowledge/{term["primary_domain"]}/"))}">{_esc(term["primary_domain"])}</a>{status}</div><h1>{_esc(localized["title"])}</h1><p class="canonical">{_esc(term["canonical_name"])}</p><div class="term-fields"><span class="term-field">{_esc(term.get("difficulty", "—"))}</span><span class="term-field">{_esc(" / ".join(term.get("lifecycle_stages", [])))}</span></div><p><strong>{_esc(self.label(locale, "aliases", "Aliases"))}:</strong> {_esc(aliases)}</p></div><button type="button" data-bookmark data-term-slug="{_esc(term["slug"])}" aria-pressed="false">☆ {_esc(self.label(locale, "bookmark", "Bookmark"))}</button></div>'
                f'<section data-section="user-says"><h2>{_esc(self.label(locale, "user_says", "You may say"))}</h2><p>{_esc(localized["user_says"])}</p></section>'
                f'<section data-section="definition"><h2>{_esc(self.label(locale, "short_definition", "Short definition"))}</h2><p class="lead">{_esc(localized["short_definition"])}</p></section>'
                f'<section data-section="prerequisites"><h2>{_esc(self.label(locale, "prerequisites", "Prerequisites"))}</h2><div class="chip-row">{prerequisites}</div></section>'
                f'<section data-section="mechanism"><h2>{_esc(self.label(locale, "mechanism", "How it works"))}</h2><p>{_esc(localized["mechanism"])}</p></section>'
                f'<section data-section="boundary"><h2>{_esc(self.label(locale, "boundary", "Boundary"))}</h2><p>{_esc(localized["boundary"])}</p></section>'
                + self.example_html(locale, term, localized)
                + f'<section data-section="why-it-matters"><h2>{_esc(self.label(locale, "why", "Why it matters"))}</h2><p>{_esc(localized["why_it_matters"])}</p></section>'
                f'<section data-section="project-example"><h2>{_esc(self.label(locale, "project_example", "Project example"))}</h2><p>{_esc(localized["project_example"])}</p></section>'
                + self.exercise_html(locale, term)
                + f'<section class="prompt-box" data-section="agent-prompt"><h2>{_esc(self.label(locale, "prompt", "Tell your AI"))}</h2><pre>{_esc(localized["ai_prompt_example"])}</pre><button type="button" data-copy="{_esc(localized["ai_prompt_example"])}">{_esc(self.label(locale, "copy", "Copy"))}</button></section>'
                f'<section data-section="common-mistake"><h2>{_esc(self.label(locale, "mistake", "Common mistake"))}</h2><p>{_esc(localized["common_mistake"])}</p></section>'
                f'<section><h2>{_esc(self.label(locale, "related", "Related terms"))}</h2><div class="chip-row">{related}</div></section>'
                f'<section data-section="project-paths"><h2>{_esc(self.label(locale, "project_paths", "Project paths"))}</h2><div class="chip-row">{"".join(memberships) or "—"}</div></section>'
                f'<section data-section="sources"><h2>{_esc(self.label(locale, "sources", "Sources and provenance"))}</h2><ul>{sources}</ul></section><nav class="term-pagination" aria-label="{_esc(self.label(locale, "term_sequence", "Term sequence"))}">{previous_link}{next_link}</nav></article>'
            )
            route = f"/{locale}/terms/{term['slug']}/"
            structured = {
                "@context": "https://schema.org",
                "@type": "DefinedTerm",
                "name": term["canonical_name"],
                "alternateName": [localized["title"], *term.get("aliases", [])],
                "description": localized["short_definition"],
                "url": self.urls.absolute(route),
                "inDefinedTermSet": PRODUCT_NAME,
            }
            indexable = localized["status"] == "published"
            self.add_page(
                route,
                self.shell(
                    locale,
                    localized["title"],
                    localized["short_definition"],
                    body,
                    f"/terms/{term['slug']}/",
                    indexable=indexable,
                    structured_data=structured,
                ),
                indexable=indexable,
            )

    def build_paths(self, locale: str) -> None:
        title = self.label(locale, "route", "Project paths")
        cards = "".join(
            f'<a class="path-card" href="{_esc(self.urls.page(f"/{locale}/paths/{path["slug"]}/"))}"><span class="domain-name">{_esc(path["localized"][locale]["title"])}</span><span class="domain-examples">{_esc(path["localized"][locale]["summary"])}</span><strong>{len(path["chapters"])} {_esc(self.label(locale, "chapters_unit", "chapters"))}</strong></a>'
            for path in self.catalog.paths
        )
        body = f'<section class="category-hero"><div class="eyebrow">{_esc(title)}</div><h1>{_esc(title)}</h1><p>{_esc(self.label(locale, "path_intro", "Learn terms in the order a real project needs them."))}</p></section><div class="domain-grid">{cards}</div>'
        indexable = all(
            path["localized"][locale]["status"] == "published"
            for path in self.catalog.paths
        )
        self.add_page(
            f"/{locale}/paths/",
            self.shell(locale, title, title, body, "/paths/", indexable=indexable),
            indexable=indexable,
        )
        for path in self.catalog.paths:
            localized = path["localized"][locale]
            localized_chapters = {
                chapter["id"]: chapter for chapter in localized["chapters"]
            }
            chapter_links = "".join(
                f'<li><span>{chapter["order"]}</span><a href="{_esc(self.urls.page(f"/{locale}/paths/{path["slug"]}/{chapter["id"]}/"))}"><strong>{_esc(localized_chapters[chapter["id"]]["title"])}</strong><small>{_esc(localized_chapters[chapter["id"]]["summary"])}</small></a></li>'
                for chapter in path["chapters"]
            )
            path_body = f'<article class="path-detail"><a class="back" href="{_esc(self.urls.page(f"/{locale}/paths/"))}">← {_esc(title)}</a><h1>{_esc(localized["title"])}</h1><p class="lead">{_esc(localized["summary"])}</p><ol class="path-chapters">{chapter_links}</ol></article>'
            route = f"/{locale}/paths/{path['slug']}/"
            path_indexable = localized["status"] == "published"
            structured = {
                "@context": "https://schema.org",
                "@type": "Course",
                "name": localized["title"],
                "description": localized["summary"],
                "url": self.urls.absolute(route),
            }
            self.add_page(
                route,
                self.shell(
                    locale,
                    localized["title"],
                    localized["summary"],
                    path_body,
                    f"/paths/{path['slug']}/",
                    indexable=path_indexable,
                    structured_data=structured,
                ),
                indexable=path_indexable,
            )
            for position, chapter in enumerate(path["chapters"]):
                chapter_text = localized_chapters[chapter["id"]]
                terms = [self.term_by_slug[slug] for slug in chapter["term_slugs"]]
                term_links = "".join(self.term_link(locale, term) for term in terms)
                next_link = ""
                if position + 1 < len(path["chapters"]):
                    next_chapter = path["chapters"][position + 1]
                    next_link = f'<a class="button" href="{_esc(self.urls.page(f"/{locale}/paths/{path["slug"]}/{next_chapter["id"]}/"))}">{_esc(self.label(locale, "next_chapter", "Next chapter"))}</a>'
                chapter_body = (
                    f'<article class="path-chapter" data-path-slug="{_esc(path["slug"])}" data-chapter-id="{_esc(chapter["id"])}"><a class="back" href="{_esc(self.urls.page(route))}">← {_esc(localized["title"])}</a><p class="eyebrow">{chapter["order"]} / {len(path["chapters"])}</p><h1>{_esc(chapter_text["title"])}</h1><p class="lead">{_esc(chapter_text["summary"])}</p>'
                    f'<section><h2>{_esc(self.label(locale, "outcome", "Outcome"))}</h2><p>{_esc(chapter_text["outcome"])}</p></section><section><h2>{_esc(self.label(locale, "terms", "Terms"))}</h2><div class="chip-row">{term_links}</div></section><section><h2>{_esc(self.label(locale, "checkpoint", "Checkpoint"))}</h2><p>{_esc(chapter_text["checkpoint"])}</p><label><input type="checkbox" data-path-complete/> {_esc(self.label(locale, "mark_complete", "Mark complete locally"))}</label></section>{next_link}</article>'
                )
                chapter_route = f"/{locale}/paths/{path['slug']}/{chapter['id']}/"
                self.add_page(
                    chapter_route,
                    self.shell(
                        locale,
                        chapter_text["title"],
                        chapter_text["summary"],
                        chapter_body,
                        f"/paths/{path['slug']}/{chapter['id']}/",
                        indexable=path_indexable,
                    ),
                    indexable=path_indexable,
                )

    def build_practice(self, locale: str) -> None:
        exercises = build_exercises_index(self.catalog, locale, self.urls)
        domains = "".join(
            f'<option value="domain:{_esc(domain["id"])}">{_esc(_domain_name(domain, locale))}</option>'
            for domain in self.catalog.domains
        )
        fallback = "".join(
            f'<li><a href="{_esc(exercise["url"])}">{_esc(exercise["title"])} — {_esc(exercise["question"])}</a></li>'
            for exercise in exercises
        )
        body = (
            f'<section class="learn-header" data-practice-root><div><div class="eyebrow">{_esc(self.label(locale, "practice_eyebrow", "LOCAL PRACTICE"))}</div><h1>{_esc(self.label(locale, "practice", "Practice"))}</h1><p>{_esc(self.label(locale, "practice_intro", "Questions are static; attempts and review timing stay in this browser."))}</p></div>'
            f'<label>{_esc(self.label(locale, "scope", "Scope"))}<select data-practice-scope><option value="all">{_esc(self.label(locale, "all_terms", "All terms"))}</option>{domains}</select></label><p data-practice-status role="status"></p><div data-practice-card></div></section>'
            f'<section><h2>{_esc(self.label(locale, "local_data", "Local data"))}</h2><button type="button" data-export-local>{_esc(self.label(locale, "export", "Export"))}</button><label>{_esc(self.label(locale, "import", "Import"))}<input type="file" data-import-local accept="application/json"/></label><button type="button" data-clear-local>{_esc(self.label(locale, "clear_local", "Clear local data"))}</button></section>'
            f'<noscript><section><h2>{_esc(self.label(locale, "all_questions", "All questions"))}</h2><ul>{fallback}</ul></section></noscript>'
        )
        indexable = all(exercise["status"] == "published" for exercise in exercises)
        self.add_page(
            f"/{locale}/practice/",
            self.shell(locale, self.label(locale, "practice", "Practice"), self.label(locale, "practice_intro", "Practice Vibe Coding terms"), body, "/practice/", indexable=indexable),
            indexable=indexable,
        )

    def build_learn_compatibility(self, locale: str) -> None:
        ui = self.ui[locale]
        body = (
            f'<section class="learn-header"><div><div class="eyebrow">{_esc(ui["learning_eyebrow"])}</div><h1>{_esc(ui["learn_title"])}</h1><p>{_esc(ui["learn_sub"])}</p></div><label class="daily-setting">{_esc(ui["daily"])}<input id="daily-count" type="number" min="1" max="30" value="3" inputmode="numeric"/></label></section>'
            f'<div class="learning-stats"><strong id="learn-progress">0 / 0</strong><span class="storage-note">{_esc(ui["local"])}</span></div><div id="learning-status" class="learning-status" role="status" hidden></div><section id="learning-card" class="learning-card" aria-live="polite"><div class="learning-empty"><button class="button" id="start-learning" type="button">{_esc(ui["start"])}</button></div></section>'
            f'<template id="learning-template"><div class="learn-meta"><span class="learn-position"></span><span class="learn-domain"></span></div><h2 class="learn-title" tabindex="-1"></h2><p class="learn-canonical"></p><button class="reveal button-secondary" type="button">{_esc(ui["reveal"])}</button><div class="learn-answer" hidden><p class="learn-definition"></p><p class="learn-analogy"></p><div class="rating-row"><button type="button" data-rating="again">{_esc(ui["again"])}</button><button type="button" data-rating="partial">{_esc(ui["partial"])}</button><button type="button" data-rating="mastered">{_esc(ui["mastered"])}</button></div></div></template>'
        )
        self.add_page(
            f"/{locale}/learn/",
            self.shell(locale, ui["learn_title"], ui["learn_sub"], body, "/learn/", indexable=False),
        )

    def build_artifacts(self) -> None:
        manifest = {
            "name": PRODUCT_NAME,
            "short_name": PRODUCT_NAME,
            "description": "A multilingual Vibe Coding terminology guide.",
            "start_url": self.urls.page("/"),
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#3457f1",
            "lang": "en",
            "icons": [
                {
                    "src": self.urls.asset("assets/logo.svg"),
                    "sizes": "any",
                    "type": "image/svg+xml",
                    "purpose": "any",
                }
            ],
        }
        (self.output / "manifest.webmanifest").write_text(
            _json(manifest, pretty=True), encoding="utf-8"
        )
        robots = ["User-agent: *", "Allow: /"]
        if self.config.site_url:
            robots.append(f"Sitemap: {self.urls.absolute('/sitemap.xml')}")
        (self.output / "robots.txt").write_text("\n".join(robots) + "\n", encoding="utf-8")
        sitemap_entries = "".join(
            f'<url><loc>{_esc(self.urls.absolute(route))}</loc></url>'
            for route in sorted(set(self.sitemap_routes))
        )
        (self.output / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"{sitemap_entries}</urlset>",
            encoding="utf-8",
        )
        language_links = "".join(
            f'<a href="{_esc(self.urls.page(f"/{locale}/"))}">{_esc(LANGUAGE_NAMES[locale])}</a>'
            for locale in self.catalog.locales
        )
        (self.output / "404.html").write_text(
            f'<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="robots" content="noindex,follow"/><link rel="stylesheet" href="{_esc(self.urls.asset("assets/styles.css"))}"/></head><body><main><h1>Page not found</h1><p>{language_links}</p></main></body></html>',
            encoding="utf-8",
        )
        (self.output / ".nojekyll").write_text("", encoding="utf-8")
        build_info = {
            "builtAt": dt.datetime.now(dt.UTC).isoformat(),
            "locales": list(self.catalog.locales),
            "termCount": len(self.catalog.terms),
            "domainCount": len(self.catalog.domains),
            "topicCount": len(self.catalog.topics),
            "pathCount": len(self.catalog.paths),
            "siteUrl": self.config.site_url or None,
            "basePath": self.config.base_path,
            "authentication": False,
        }
        (self.output / "build-info.json").write_text(
            _json(build_info, pretty=True), encoding="utf-8"
        )

    def build(self) -> list[str]:
        self.prepare()
        self.build_gateway()
        for locale in self.catalog.locales:
            self.build_indexes(locale)
            self.build_home(locale)
            self.build_terms(locale)
            self.build_knowledge(locale)
            self.build_domain_and_topics(locale)
            self.build_term_pages(locale)
            self.build_paths(locale)
            self.build_practice(locale)
            self.build_learn_compatibility(locale)
        self.build_artifacts()
        return self.routes


def build_site(config: BuildConfig, catalog: Catalog) -> list[str]:
    """Generate a complete host-independent static site and return public routes."""

    return SiteRenderer(config, catalog).build()
