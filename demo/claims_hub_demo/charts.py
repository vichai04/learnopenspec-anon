"""Dashboard charts (Recharts) in the dark theme palette.

Every chart reads its numbers from AppState and shows an empty-state message
when the current filter leaves nothing to plot.
"""

import reflex as rx

from .state import AppState

AXIS = "#8b9ab0"
GRID = "#243142"
TOOLTIP_STYLE = {
    "backgroundColor": "#1a2532",
    "border": "1px solid #243142",
    "borderRadius": "8px",
    "color": "#e6edf5",
    "fontSize": "12px",
}
OUTCOME_FILLS = {
    "approved": "#34d399",
    "partial": "#fbbf24",
    "rejected": "#f87171",
    "pended": "#94a3b8",
}
HEIGHT = 260


def _empty(items: rx.Var) -> rx.Component:
    return rx.el.div(
        AppState.s["chart_empty"],
        class_name="flex h-[260px] items-center justify-center text-sm text-muted",
    )


def _chart_or_empty(items: rx.Var, chart: rx.Component, height: int = HEIGHT) -> rx.Component:
    return rx.cond(
        items.length() == 0,
        _empty(items),
        rx.recharts.responsive_container(chart, width="100%", height=height),
    )


def status_donut() -> rx.Component:
    chart = rx.recharts.pie_chart(
        rx.recharts.pie(
            data=AppState.chart_status,
            data_key="value",
            name_key="name",
            inner_radius=62,
            outer_radius=96,
            padding_angle=3,
            stroke="#121a24",
        ),
        rx.recharts.tooltip(content_style=TOOLTIP_STYLE),
        rx.recharts.legend(vertical_align="bottom", icon_type="circle"),
        data=AppState.chart_status,
    )
    return _chart_or_empty(AppState.chart_status, chart)


def monthly_outcomes() -> rx.Component:
    chart = rx.recharts.bar_chart(
        rx.recharts.bar(data_key="approved", stack_id="outcome", fill=OUTCOME_FILLS["approved"], name="approved"),
        rx.recharts.bar(data_key="partial", stack_id="outcome", fill=OUTCOME_FILLS["partial"], name="partial"),
        rx.recharts.bar(data_key="rejected", stack_id="outcome", fill=OUTCOME_FILLS["rejected"], name="rejected"),
        rx.recharts.bar(data_key="pended", stack_id="outcome", fill=OUTCOME_FILLS["pended"], name="pended", radius=[4, 4, 0, 0]),
        rx.recharts.cartesian_grid(stroke=GRID, stroke_dasharray="3 3", vertical=False),
        rx.recharts.x_axis(data_key="month", stroke=AXIS, tick_line=False),
        rx.recharts.y_axis(stroke=AXIS, tick_line=False, axis_line=False),
        rx.recharts.tooltip(content_style=TOOLTIP_STYLE, cursor={"fill": "#1a2532"}),
        rx.recharts.legend(icon_type="circle"),
        data=AppState.chart_monthly,
    )
    return _chart_or_empty(AppState.chart_monthly, chart)


def reject_rate_line() -> rx.Component:
    chart = rx.recharts.line_chart(
        rx.recharts.cartesian_grid(stroke=GRID, stroke_dasharray="3 3", vertical=False),
        rx.recharts.x_axis(data_key="month", stroke=AXIS, tick_line=False),
        rx.recharts.y_axis(stroke=AXIS, tick_line=False, axis_line=False, unit="%", domain=[0, 100]),
        rx.recharts.tooltip(content_style=TOOLTIP_STYLE),
        rx.recharts.line(
            data_key="reject_rate",
            stroke="#4f8cff",
            stroke_width=3,
            type_="monotone",
            dot={"r": 4, "fill": "#4f8cff", "strokeWidth": 0},
            active_dot={"r": 6},
            name="reject rate %",
            connect_nulls=False,
        ),
        data=AppState.chart_monthly,
    )
    return _chart_or_empty(AppState.chart_monthly, chart)


def reasons_bar() -> rx.Component:
    chart = rx.recharts.bar_chart(
        rx.recharts.cartesian_grid(stroke=GRID, stroke_dasharray="3 3", horizontal=False),
        rx.recharts.x_axis(type_="number", stroke=AXIS, tick_line=False, axis_line=False),
        rx.recharts.y_axis(data_key="code", type_="category", stroke=AXIS, tick_line=False, axis_line=False, width=48, interval=0),
        rx.recharts.tooltip(content_style=TOOLTIP_STYLE, cursor={"fill": "#1a2532"}),
        rx.recharts.bar(data_key="count", fill="#4f8cff", radius=[0, 4, 4, 0], name="claims"),
        layout="vertical",
        data=AppState.chart_reasons,
    )
    return _chart_or_empty(AppState.chart_reasons, chart, height=320)
