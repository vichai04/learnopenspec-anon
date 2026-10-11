"""Shared layout and UI pieces. Styling comes only from theme tokens."""

import reflex as rx

from . import theme
from .state import AppState


def _nav_link(label: rx.Var | str, href: str) -> rx.Component:
    return rx.el.a(label, href=href, class_name="block rounded-lg px-3 py-2 text-sm text-muted hover:bg-surface-2 hover:text-ink")


def _nav_items() -> rx.Component:
    return rx.fragment(
        _nav_link(AppState.s["nav_dashboard"], "/"),
        _nav_link(AppState.s["nav_claims"], "/claims"),
    )


def sidebar() -> rx.Component:
    """Left navigation on medium screens and up."""
    return rx.el.aside(
        rx.el.div(
            rx.el.div(AppState.s["app"], class_name="text-base font-semibold px-3 pt-1 pb-4"),
            _nav_items(),
            class_name="flex flex-col gap-1",
        ),
        class_name="hidden md:flex md:flex-col md:w-56 md:shrink-0 border-r border-border bg-surface p-4 min-h-screen",
    )


def topbar() -> rx.Component:
    """Compact navigation for phone width."""
    return rx.el.header(
        rx.el.div(
            rx.el.div(AppState.s["app"], class_name="text-base font-semibold"),
            lang_toggle(),
            class_name="flex items-center justify-between",
        ),
        rx.el.nav(_nav_items(), class_name="flex gap-2 mt-3"),
        class_name="md:hidden border-b border-border bg-surface px-4 py-3",
    )


def lang_toggle() -> rx.Component:
    return rx.el.button(
        AppState.s["lang_toggle"],
        on_click=AppState.toggle_lang,
        class_name=theme.BTN,
    )


def shell(*children: rx.Component) -> rx.Component:
    """Page frame: sidebar on desktop, top bar on phones, then the page content."""
    return rx.el.div(
        sidebar(),
        rx.el.div(
            topbar(),
            rx.el.main(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(AppState.s["as_of"], class_name="text-xs text-muted"),
                        rx.el.div(lang_toggle(), class_name="hidden md:block"),
                        class_name="flex items-center justify-between mb-4",
                    ),
                    rx.cond(
                        AppState.error != "",
                        rx.el.div(AppState.error, class_name="rounded-card border border-status-rejected bg-surface p-4 text-status-rejected mb-4"),
                    ),
                    *children,
                    class_name="mx-auto max-w-6xl flex flex-col gap-4 px-4 py-6 md:px-8",
                ),
            ),
            class_name="flex-1 min-w-0",
        ),
        class_name=theme.PAGE + " flex",
    )


def metric_tile(label: rx.Var | str, value: rx.Var | str, hint: rx.Var | str | None = None) -> rx.Component:
    children = [
        rx.el.div(label, class_name="text-xs font-medium text-muted"),
        rx.el.div(value, class_name="mt-1 text-3xl font-semibold tabular-nums"),
    ]
    if hint is not None:
        children.append(rx.el.div(hint, class_name="mt-1 text-xs text-muted"))
    return rx.el.div(*children, class_name=theme.CARD)


def status_tag(status: rx.Var | str) -> rx.Component:
    """Status pill. Colors come from the theme's status tokens."""
    base = "inline-block rounded-full border px-2 py-0.5 text-xs "
    return rx.el.span(
        status,
        class_name=rx.match(
            status,
            ("approved", base + "text-status-approved border-status-approved"),
            ("partial", base + "text-status-partial border-status-partial"),
            ("rejected", base + "text-status-rejected border-status-rejected"),
            ("pended", base + "text-status-pended border-status-pended"),
            ("ready", base + "text-status-ready border-status-ready"),
            ("needs_correction", base + "text-status-needs border-status-needs"),
            ("submitted", base + "text-status-ready border-status-ready"),
            ("pending", base + "text-status-partial border-status-partial"),
            base + "text-muted border-border",
        ),
    )


def notice() -> rx.Component:
    return rx.el.div(AppState.s["synthetic_notice"], class_name="rounded-card border border-border bg-surface-2 px-4 py-3 text-xs text-muted")


def card(title: rx.Var | str, *children: rx.Component) -> rx.Component:
    return rx.el.section(
        rx.el.div(title, class_name=theme.CARD_TITLE),
        *children,
        class_name=theme.CARD,
    )


def table(headers: list[rx.Var | str], *rows: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.table(
            rx.el.thead(rx.el.tr(*[rx.el.th(h, class_name=theme.TH) for h in headers])),
            rx.el.tbody(*rows),
            class_name="w-full min-w-max border-collapse",
        ),
        class_name="overflow-x-auto rounded-lg border border-border",
    )


def td(content: rx.Var | rx.Component | str, class_name: str = "") -> rx.Component:
    return rx.el.td(content, class_name=f"{theme.TD} {class_name}".strip())


def claim_tabs(claim_no: rx.Var | str) -> rx.Component:
    return rx.el.nav(
        rx.el.a(AppState.s["tab_normalization"], href="/claims/" + claim_no + "/normalization", class_name=theme.BTN),
        rx.el.a(AppState.s["tab_validation"], href="/claims/" + claim_no + "/validation", class_name=theme.BTN),
        rx.el.a(AppState.s["tab_rules"], href="/claims/" + claim_no + "/rules", class_name=theme.BTN),
        class_name="flex flex-wrap gap-2",
    )


def claim_header() -> rx.Component:
    return card(
        rx.el.span(AppState.s["claim_no"], ": ", AppState.claim["claim_no"]),
        rx.el.div(
            rx.el.div(
                rx.el.span(AppState.s["hospital"], class_name="text-muted text-xs"),
                rx.el.div(AppState.claim["hospital_name"], class_name="text-sm"),
            ),
            rx.el.div(
                rx.el.span(AppState.s["payer"], class_name="text-muted text-xs"),
                rx.el.div(AppState.claim["payer_id"], class_name="text-sm"),
            ),
            rx.el.div(
                rx.el.span(AppState.s["status"], class_name="text-muted text-xs"),
                rx.el.div(status_tag(AppState.claim["claim_status"]), class_name="mt-1"),
            ),
            rx.el.div(
                rx.el.span(AppState.s["amount"], class_name="text-muted text-xs"),
                rx.el.div(AppState.claim["amount"], class_name="text-sm tabular-nums"),
            ),
            class_name="grid grid-cols-2 md:grid-cols-4 gap-4",
        ),
        claim_tabs(AppState.claim_no),
    )
