"""Shared navigation helpers for the custom mega-menu and the left ToC.

This is the single place the nav "rules" live, so the templates stay dumb.

on_nav annotates every Section with:
    section.index_page      its own index page ("Overview"), or None. The section
                            title links here, and this page is never listed as a
                            child entry.
    section.has_subsection  True if any child is itself a Section.

on_nav also tags separators. A nav entry whose target is the sentinel "sep:" (a
harmless external-link value that passes a --strict build, e.g.
`- "---": "sep:"`) is marked for the templates:
    item.is_separator       True for a sentinel entry
    item.separator_label    None for a divider whose title is only dashes (a plain
                            rule); otherwise the title text, for a labelled divider

on_page_context exposes, for pages kept out of the nav (the per-method pages):
    localnav_host           the owning nav page (the class index), or None
    localnav_chain          [host, host.parent, ... top-level section], or []
so the left ToC can render a method page exactly as its parent class's page.
"""


SEPARATOR_URL = "sep:"      # nav sentinel target marking a divider (see mkdocs.yml)
_DASHES = set("-—–─")       # a title of only these is a plain rule, with no label


def _annotate(items):
    for item in items:
        if getattr(item, "is_section", False):
            item.index_page = next(
                (c for c in item.children
                 if getattr(c, "is_page", False) and c.is_index),
                None,
            )
            item.has_subsection = any(
                getattr(c, "is_section", False) for c in item.children
            )
            _annotate(item.children)


def _annotate_separators(items):
    """Tag every item with is_separator, and separator_label for the ones that are.
    A title of only dashes is a plain rule (label None); any other title is a
    labelled divider carrying that text."""
    for item in items:
        item.is_separator = (getattr(item, "is_link", False)
                             and getattr(item, "url", None) == SEPARATOR_URL)
        if item.is_separator:
            label = (item.title or "").strip()
            item.separator_label = None if label and set(label) <= _DASHES else label
        elif getattr(item, "is_section", False):
            _annotate_separators(item.children)


def on_nav(nav, config, files):
    _annotate(nav.items)
    _annotate_separators(nav.items)
    return nav


def _parent_url(url):
    trimmed = url.rstrip("/")
    if "/" not in trimmed:
        return None
    return trimmed.rsplit("/", 1)[0] + "/"


def on_page_context(context, page, config, nav):
    context["localnav_host"] = None
    context["localnav_chain"] = []

    nav_pages = {p.url: p for p in nav.pages}
    if page.url in nav_pages:
        return context  # already in the nav; mkdocs marks the active path

    parent_url = _parent_url(page.url)
    host = nav_pages.get(parent_url) if parent_url else None
    if host is None:
        return context

    chain = []
    node = host
    while node is not None:
        chain.append(node)
        node = node.parent

    context["localnav_host"] = host
    context["localnav_chain"] = chain
    return context
