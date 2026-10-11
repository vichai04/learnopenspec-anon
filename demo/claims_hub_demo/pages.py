"""Page builders: dashboard, claim list, and the three per-claim views."""

import reflex as rx

from . import theme
from .charts import monthly_outcomes, reasons_bar, reject_rate_line, status_donut
from .components import card, claim_header, metric_tile, notice, shell, status_tag, table, td
from .state import AppState


def _select(label: rx.Var | str, value: rx.Var, options: rx.Var, on_change) -> rx.Component:
    return rx.el.label(
        rx.el.span(label, class_name="block text-xs text-muted mb-1"),
        rx.el.select(
            rx.el.option(AppState.s["all"], value="all"),
            rx.foreach(options, lambda o: rx.el.option(o["label"], value=o["value"])),
            value=rx.cond(value == "", "all", value),
            on_change=on_change,
            class_name=theme.INPUT + " w-full min-w-[12rem]",
        ),
        class_name="block",
    )


def dashboard_page() -> rx.Component:
    return shell(
        rx.el.h1(AppState.s["nav_dashboard"], class_name="text-2xl font-semibold"),
        notice(),
        rx.el.div(
            _select(AppState.s["filter_payer"], AppState.payer, AppState.payer_options, AppState.set_payer),
            _select(AppState.s["filter_hospital"], AppState.hospital, AppState.hospital_options, AppState.set_hospital),
            class_name="flex flex-wrap gap-4",
        ),
        rx.el.div(
            metric_tile(AppState.s["metric_claims"], AppState.metric_claims.to_string()),
            metric_tile(AppState.s["metric_pending"], AppState.metric_pending.to_string()),
            metric_tile(AppState.s["metric_reject_rate"], AppState.metric_reject_rate, AppState.s["metric_reject_hint"]),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-4",
        ),
        rx.el.div(
            card(AppState.s["chart_status"], status_donut()),
            card(AppState.s["chart_monthly"], monthly_outcomes()),
            card(AppState.s["chart_reject_rate"], reject_rate_line()),
            card(AppState.s["chart_reasons"], reasons_bar()),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-4",
        ),
        rx.el.div(
            card(
                AppState.s["outcomes"],
                table(
                    [AppState.s["status"], AppState.s["count"]],
                    rx.foreach(
                        AppState.outcomes,
                        lambda row: rx.el.tr(td(status_tag(row["status"])), td(row["count"].to_string())),
                    ),
                ),
            ),
            card(
                AppState.s["reasons"],
                table(
                    [AppState.s["code"], AppState.s["description"], AppState.s["count"]],
                    rx.foreach(
                        AppState.reasons,
                        lambda row: rx.el.tr(
                            td(row["code"]), td(row["description"]), td(row["count"].to_string())
                        ),
                    ),
                ),
                rx.cond(
                    AppState.unclassified_count > 0,
                    rx.el.div(
                        rx.el.div(
                            AppState.s["unclassified"], " (", AppState.unclassified_count.to_string(), ")",
                            class_name="mt-4 mb-2 text-xs text-muted",
                        ),
                        rx.foreach(
                            AppState.unclassified,
                            lambda row: rx.el.div(
                                rx.el.span(row["message"], class_name="text-sm"),
                                rx.el.span(row["count"].to_string(), class_name="ml-2 text-sm tabular-nums text-muted"),
                                class_name="flex justify-between border-t border-border py-2",
                            ),
                        ),
                    ),
                ),
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-4",
        ),
    )


def claims_page() -> rx.Component:
    return shell(
        rx.el.h1(AppState.s["nav_claims"], class_name="text-2xl font-semibold"),
        rx.el.div(
            rx.el.span(AppState.s["showing"], " ", AppState.claims.length().to_string(), " ", AppState.s["of"], " ", AppState.claims_total.to_string()),
            class_name="text-xs text-muted",
        ),
        table(
            [
                AppState.s["claim_no"],
                AppState.s["hospital"],
                AppState.s["payer"],
                AppState.s["status"],
                AppState.s["amount"],
                "",
            ],
            rx.foreach(
                AppState.claims,
                lambda row: rx.el.tr(
                    td(row["claim_no"]),
                    td(row["hospital_name"]),
                    td(row["payer_id"]),
                    td(status_tag(row["claim_status"])),
                    td(row["amount"], class_name="text-right tabular-nums"),
                    td(
                        rx.el.div(
                            rx.el.a(AppState.s["tab_normalization"], href=row["normalization_href"], class_name="text-accent hover:underline"),
                            rx.el.a(AppState.s["tab_validation"], href=row["validation_href"], class_name="text-accent hover:underline"),
                            rx.el.a(AppState.s["tab_rules"], href=row["rules_href"], class_name="text-accent hover:underline"),
                            class_name="flex flex-wrap gap-3",
                        ),
                    ),
                ),
            ),
        ),
    )


def normalization_page() -> rx.Component:
    return shell(
        claim_header(),
        card(
            rx.el.span(AppState.s["tab_normalization"], " · ", AppState.norm_hospital, " · ", AppState.norm_date_format),
            table(
                [AppState.s["field"], AppState.s["raw"], AppState.s["rule"], AppState.s["canonical"], AppState.s["error"]],
                rx.foreach(
                    AppState.norm_fields,
                    lambda f: rx.el.tr(
                        td(f["name"]),
                        td(f["raw"], class_name="font-mono text-xs"),
                        td(f["rule"], class_name="text-muted text-xs"),
                        td(f["canonical"], class_name="font-mono text-xs"),
                        td(f["error"], class_name="text-status-rejected text-xs"),
                    ),
                ),
            ),
        ),
    )


def validation_page() -> rx.Component:
    return shell(
        claim_header(),
        card(
            rx.el.div(
                status_tag(AppState.val_status),
                rx.el.span(AppState.s["rule_version"], ": ", AppState.val_rule_version, class_name="text-xs text-muted"),
                rx.el.span(AppState.s["elapsed"], ": ", AppState.val_elapsed_ms, class_name="text-xs text-muted tabular-nums"),
                class_name="flex flex-wrap items-center gap-3",
            ),
            rx.cond(
                AppState.failures.length() == 0,
                rx.el.div(AppState.s["passed"], class_name="mt-4 text-sm text-status-approved"),
                rx.el.div(
                    table(
                        [AppState.s["failure_rule"], AppState.s["field"], AppState.s["message"]],
                        rx.foreach(
                            AppState.failures,
                            lambda f: rx.el.tr(
                                td(f["rule_id"], class_name="font-mono text-xs"),
                                td(f["field"], class_name="text-xs"),
                                td(rx.cond(AppState.lang == "th", f["message_th"], f["message_en"]), class_name="text-sm"),
                            ),
                        ),
                    ),
                    class_name="mt-4",
                ),
            ),
        ),
    )


def rules_page() -> rx.Component:
    return shell(
        claim_header(),
        rx.cond(
            AppState.rule_version == "",
            card(AppState.s["no_rules"]),
            rx.el.div(
                card(
                    AppState.s["tab_rules"],
                    rx.el.div(
                        rx.el.div(
                            rx.el.span(AppState.s["rule_version"], ": ", class_name="text-muted text-xs"),
                            rx.el.span(AppState.rule_version, class_name="text-sm font-mono"),
                        ),
                        rx.el.div(
                            rx.el.span(AppState.s["effective_from"], ": ", class_name="text-muted text-xs"),
                            rx.el.span(AppState.rule_effective_from, class_name="text-sm"),
                        ),
                        rx.el.div(
                            rx.el.span(AppState.s["service_date"], ": ", class_name="text-muted text-xs"),
                            rx.el.span(AppState.rule_service_date, class_name="text-sm"),
                        ),
                        class_name="flex flex-col gap-1 mb-4",
                    ),
                    table(
                        [AppState.s["rule_type"], AppState.s["rule_value"], AppState.s["description"]],
                        rx.foreach(
                            AppState.rule_rows,
                            lambda r: rx.el.tr(
                                td(r["rule_type"], class_name="font-mono text-xs"),
                                td(r["rule_value"], class_name="font-mono text-xs"),
                                td(r["description"], class_name="text-xs"),
                            ),
                        ),
                    ),
                    rx.cond(
                        AppState.rule_history.length() > 0,
                        rx.el.div(AppState.s["history_note"], class_name="mt-3 text-xs text-status-partial"),
                    ),
                ),
                rx.cond(
                    AppState.rule_unrecognized.length() > 0,
                    card(
                        AppState.s["unrecognized"],
                        rx.foreach(AppState.rule_unrecognized, lambda t: rx.el.div(t, class_name="font-mono text-sm text-status-rejected")),
                    ),
                ),
                class_name="flex flex-col gap-4",
            ),
        ),
        notice(),
    )
