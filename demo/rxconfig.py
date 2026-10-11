import reflex as rx

from claims_hub_demo.theme import PLUGINS

config = rx.Config(
    app_name="claims_hub_demo",
    plugins=PLUGINS,
    disable_plugins=[rx.plugins.SitemapPlugin],
)
