"""Configuration generation form for TUI."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static


class ConfigGenerationForm(ModalScreen[bool]):
    """Modal form for configuration generation."""

    CSS_PATH = "tui.tcss"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_generated = False

    def compose(self) -> ComposeResult:
        """Compose the form."""
        # Get current export settings from state
        app_state = self.app.state
        export_settings = app_state.get_export_settings()

        with Container(id="config-form-container"):
            yield Static("Generate Configuration", classes="form-title")

            with Vertical(classes="form-fields"):
                yield Label("Output File:")
                yield Input(
                    value=export_settings.get("output_file", "config.json"),
                    placeholder="config.json",
                    id="output-file",
                )

                yield Label("Export Format:")
                yield Select(
                    [
                        ("sing-box", "sing-box"),
                        ("clash", "clash"),
                    ],
                    value=export_settings.get("format", "sing-box"),
                    id="export-format",
                )

                yield Label("Inbound Profile:")
                yield Select(
                    [
                        ("tun", "TUN Interface"),
                        ("socks", "SOCKS Proxy"),
                        ("http", "HTTP Proxy"),
                    ],
                    value=export_settings.get("inbound_profile", "tun"),
                    id="inbound-profile",
                )

                # Show current profile info
                profile_name = app_state.get_active_profile_name()
                yield Static(f"Active Profile: {profile_name}", classes="profile-info")

            with Horizontal(classes="form-buttons"):
                yield Button("Generate", variant="primary", id="generate-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    @on(Button.Pressed, "#generate-btn")
    def handle_generate(self) -> None:
        """Handle generate button press."""
        output_file = self.query_one("#output-file", Input).value.strip()
        export_format = self.query_one("#export-format", Select).value
        inbound_profile = self.query_one("#inbound-profile", Select).value

        if not output_file:
            self.notify("Please enter an output file path", severity="error")
            return

        # Update active config with new settings
        app_state = self.app.state
        if app_state.active_config and app_state.active_config.export:
            app_state.active_config.export.output_file = output_file
            app_state.active_config.export.format = export_format
            app_state.active_config.export.inbound_profile = inbound_profile
            app_state._save_active_config()

        # Generate configuration using TUIState method
        success = app_state.generate_config(output_file)

        if success:
            self.notify(
                f"Configuration generated successfully: {output_file}",
                severity="information",
            )
            self.config_generated = True
            self.dismiss(True)
        else:
            self.notify("Failed to generate configuration", severity="error")

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.dismiss(False)
