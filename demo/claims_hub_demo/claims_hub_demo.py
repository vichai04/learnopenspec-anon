import reflex as rx

from .pages import claims_page, dashboard_page, normalization_page, rules_page, validation_page
from .state import AppState, load_repository

# Read claims_hub.sqlite once at startup. A missing file is shown on every page.
load_repository()

app = rx.App()
app.add_page(dashboard_page, route="/", title="Claims Hub Demo", on_load=AppState.on_load_dashboard)
app.add_page(claims_page, route="/claims", title="Claims · Claims Hub Demo", on_load=AppState.on_load_claims)
app.add_page(
    normalization_page,
    route="/claims/[claim_no]/normalization",
    title="Normalization · Claims Hub Demo",
    on_load=AppState.on_load_normalization,
)
app.add_page(
    validation_page,
    route="/claims/[claim_no]/validation",
    title="Validation · Claims Hub Demo",
    on_load=AppState.on_load_validation,
)
app.add_page(
    rules_page,
    route="/claims/[claim_no]/rules",
    title="Payer rules · Claims Hub Demo",
    on_load=AppState.on_load_rules,
)
