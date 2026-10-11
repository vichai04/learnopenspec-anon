"""Dark dashboard theme: Tailwind tokens and the status palette.

Pages use these tokens by name (bg-surface, text-muted, status-approved, ...),
so colors change here and nowhere else.
"""

import reflex as rx

COLORS = {
    "page": "#0b1017",
    "surface": "#121a24",
    "surface-2": "#1a2532",
    "border": "#243142",
    "ink": "#e6edf5",
    "muted": "#8b9ab0",
    "accent": "#4f8cff",
    "accent-ink": "#0b1017",
    "status-approved": "#34d399",
    "status-partial": "#fbbf24",
    "status-rejected": "#f87171",
    "status-pended": "#94a3b8",
    "status-ready": "#34d399",
    "status-needs": "#f87171",
}

TAILWIND_CONFIG = {
    "theme": {
        "extend": {
            "colors": COLORS,
            "fontFamily": {
                "sans": ["Inter", "Noto Sans Thai", "system-ui", "sans-serif"],
            },
            "borderRadius": {
                "card": "0.75rem",
            },
        }
    }
}

PLUGINS = [rx.plugins.TailwindV4Plugin(config=TAILWIND_CONFIG)]

# Shared class strings so pages stay consistent.
PAGE = "min-h-screen bg-page text-ink font-sans"
CARD = "rounded-card border border-border bg-surface p-4 md:p-5"
CARD_TITLE = "text-sm font-medium text-muted mb-3"
TH = "px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-muted bg-surface-2"
TD = "px-3 py-2 text-sm border-t border-border"
BTN = "rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm hover:border-accent"
BTN_ACTIVE = "rounded-lg border border-accent bg-accent px-3 py-1.5 text-sm text-accent-ink"
INPUT = "rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-ink"

STATUS_CLASS = {
    "approved": "text-status-approved border-status-approved",
    "partial": "text-status-partial border-status-partial",
    "rejected": "text-status-rejected border-status-rejected",
    "pended": "text-status-pended border-status-pended",
    "ready": "text-status-ready border-status-ready",
    "needs_correction": "text-status-needs border-status-needs",
}
