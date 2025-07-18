"""Interactive forms for TUI application.

This module contains form implementations for various user interactions,
including subscription management and configuration generation.
"""

import logging
import subprocess
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from sboxmgr.tui.utils.validation import (
    validate_output_path,
    validate_subscription_url,
    validate_tags,
)


# Setup logging
def setup_form_logging():
    """Set up logging for forms."""
    log_file = Path.home() / ".sboxmgr" / "tui_debug.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger specifically for forms
    logger = logging.getLogger("tui_forms")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add file handler only (no console output)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_form_logging()


class SubscriptionForm(ModalScreen[bool | str]):
    """Form for adding new subscriptions.

    This modal form allows users to add new subscription sources
    with URL and optional tags. It includes real-time validation
    and user-friendly error handling.

    Returns:
        bool: True if subscription was added successfully, False if cancelled
        str: Error message if an error occurred

    """

    BINDINGS = [
        ("ctrl+v", "paste_clipboard", "Paste from clipboard"),
        ("escape", "cancel", "Cancel"),
    ]

    CSS = """
    SubscriptionForm {
        align: center middle;
    }

    .form-container {
        width: 60;
        height: auto;
        border: thick $primary;
        padding: 2;
        background: $surface;
    }

    .form-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .form-field {
        margin-bottom: 1;
    }

    .form-field Label {
        margin-bottom: 0;
    }

    .form-field Input {
        width: 1fr;
    }

    .form-field Button {
        width: auto;
        margin-left: 1;
    }

    .form-buttons {
        align: center middle;
        height: auto;
        margin-top: 1;
    }

    .form-buttons Button {
        margin: 0 1;
    }

    .error-message {
        color: $error;
        text-style: italic;
        margin-top: 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the subscription form layout.

        Returns:
            The composed result containing the form widgets

        """
        with Center():
            with Vertical(classes="form-container"):
                yield Static("Add Subscription", classes="form-title")

                with Vertical(classes="form-field"):
                    yield Label("Subscription URL:")
                    with Horizontal():
                        yield Input(
                            placeholder="https://example.com/subscription or vmess://...",
                            id="url_input",
                        )
                        yield Button("📋 Paste", id="paste_btn", variant="default")
                    yield Static("", id="url_error", classes="error-message")

                with Vertical(classes="form-field"):
                    yield Label("Tags (optional, comma-separated):")
                    yield Input(placeholder="RU, low-latency, premium", id="tags_input")
                    yield Static("", id="tags_error", classes="error-message")

                with Horizontal(classes="form-buttons"):
                    yield Button("Add", id="add_btn", variant="primary")
                    yield Button("Cancel", id="cancel_btn", variant="default")

    @on(Input.Changed, "#url_input")
    def on_url_changed(self, event: Input.Changed) -> None:
        """Validate URL input in real-time.

        Args:
            event: The input changed event

        """
        url = event.value.strip()
        error_widget = self.query_one("#url_error", Static)

        if url:
            is_valid, error_msg = validate_subscription_url(url)
            if not is_valid:
                error_widget.update(error_msg)
            else:
                error_widget.update("")
        else:
            error_widget.update("")

    @on(Input.Changed, "#tags_input")
    def on_tags_changed(self, event: Input.Changed) -> None:
        """Validate tags input in real-time.

        Args:
            event: The input changed event

        """
        tags_text = event.value.strip()
        error_widget = self.query_one("#tags_error", Static)

        if tags_text:
            is_valid, error_msg, _ = validate_tags(tags_text)
            if not is_valid:
                error_widget.update(error_msg)
            else:
                error_widget.update("")
        else:
            error_widget.update("")

    @on(Button.Pressed, "#paste_btn")
    def on_paste_pressed(self) -> None:
        """Handle paste button press."""
        try:
            # Try different clipboard commands based on available tools
            clipboard_content = None

            # Try xclip first (most common on Linux)
            try:
                result = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0:
                    clipboard_content = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            # Try xsel as fallback
            if not clipboard_content:
                try:
                    result = subprocess.run(
                        ["xsel", "--clipboard", "--output"],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if result.returncode == 0:
                        clipboard_content = result.stdout.strip()
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

            # Try wl-paste for Wayland
            if not clipboard_content:
                try:
                    result = subprocess.run(
                        ["wl-paste"],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if result.returncode == 0:
                        clipboard_content = result.stdout.strip()
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

            if clipboard_content:
                url_input = self.query_one("#url_input", Input)
                url_input.value = clipboard_content
                url_input.focus()
                # Clear any previous error
                self.query_one("#url_error", Static).update("")
            else:
                self.app.notify("Could not access clipboard", severity="warning")

        except Exception as e:
            self.app.notify(f"Paste failed: {str(e)}", severity="error")

    @on(Button.Pressed, "#add_btn")
    def on_add_pressed(self) -> None:
        """Handle add button press."""
        logger.debug("SubscriptionForm.on_add_pressed called")

        url_input = self.query_one("#url_input", Input)
        tags_input = self.query_one("#tags_input", Input)

        url = url_input.value.strip()
        tags_text = tags_input.value.strip()

        logger.debug(f"Form input - URL: {url}")
        logger.debug(f"Form input - Tags: {tags_text}")

        # Validate URL
        if not url:
            logger.debug("URL validation failed - empty URL")
            self.query_one("#url_error", Static).update("URL is required")
            url_input.focus()
            return

        is_valid, error_msg = validate_subscription_url(url)
        logger.debug(f"URL validation result: {is_valid}, error: {error_msg}")

        if not is_valid:
            self.query_one("#url_error", Static).update(error_msg)
            url_input.focus()
            return

        # Validate tags if provided
        if tags_text:
            is_valid, error_msg, _ = validate_tags(tags_text)
            logger.debug(f"Tags validation result: {is_valid}, error: {error_msg}")

            if not is_valid:
                self.query_one("#tags_error", Static).update(error_msg)
                tags_input.focus()
                return

        # Try to add subscription
        logger.debug("Calling app_state.add_subscription...")
        app_state = self.app.state
        success = app_state.add_subscription(
            url, enabled=True
        )  # Fixed: removed tags parameter
        logger.debug(f"add_subscription result: {success}")

        if success:
            logger.debug("Subscription added successfully, dismissing with True")
            self.dismiss(True)
        else:
            logger.debug("Subscription failed, dismissing with error message")
            self.dismiss(
                "Failed to add subscription. Please check the URL and try again."
            )

    @on(Button.Pressed, "#cancel_btn")
    def on_cancel_pressed(self) -> None:
        """Handle cancel button press."""
        self.dismiss(False)

    def action_paste_clipboard(self) -> None:
        """Paste from clipboard using hotkey."""
        self.on_paste_pressed()

    def action_cancel(self) -> None:
        """Cancel the form using hotkey."""
        self.dismiss(False)


class ConfigGenerationForm(ModalScreen[bool | str]):
    """Form for generating configuration files.

    This modal form allows users to configure and generate
    proxy client configurations with various options and formats.

    Returns:
        bool: True if config was generated successfully, False if cancelled
        str: Error message if an error occurred

    """

    CSS = """
    ConfigGenerationForm {
        align: center middle;
    }

    .form-container {
        width: 70;
        height: auto;
        border: thick $primary;
        padding: 2;
        background: $surface;
    }

    .form-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .form-field {
        margin-bottom: 1;
    }

    .form-field Label {
        margin-bottom: 0;
    }

    .form-field Input {
        width: 100%;
    }

    .form-buttons {
        align: center middle;
        height: auto;
        margin-top: 1;
    }

    .form-buttons Button {
        margin: 0 1;
    }

    .error-message {
        color: $error;
        text-style: italic;
        margin-top: 0;
    }

    .info-message {
        color: $text-muted;
        text-style: italic;
        margin-top: 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the config generation form layout.

        Returns:
            The composed result containing the form widgets

        """
        # Get default path from profile settings
        app_state = self.app.state
        default_path = "./config.json"
        if app_state.active_config and app_state.active_config.export:
            default_path = app_state.active_config.export.output_file or "./config.json"

        with Center():
            with Vertical(classes="form-container"):
                yield Static("Generate Configuration", classes="form-title")

                with Vertical(classes="form-field"):
                    yield Label("Client Format:")
                    yield Static("sing-box (default)", classes="info-message")

                with Vertical(classes="form-field"):
                    yield Label("Export Path:")
                    yield Input(
                        value=default_path,
                        placeholder=default_path,
                        id="path_input",
                    )
                    yield Static("", id="path_error", classes="error-message")

                with Vertical(classes="form-field"):
                    yield Static(
                        "✅ Auto-select best server per protocol\n"
                        "✅ Enable url-test for multiple servers\n"
                        "✅ Profile-based configuration\n"
                        "✅ Exclusion rules support",
                        classes="info-message",
                    )

                with Horizontal(classes="form-buttons"):
                    yield Button("Generate", id="generate_btn", variant="primary")
                    yield Button("Preview", id="preview_btn", variant="default")
                    yield Button("Cancel", id="cancel_btn", variant="default")

    @on(Input.Changed, "#path_input")
    def on_path_changed(self, event: Input.Changed) -> None:
        """Validate output path in real-time.

        Args:
            event: The input changed event

        """
        path = event.value.strip()
        error_widget = self.query_one("#path_error", Static)

        if path:
            is_valid, error_msg = validate_output_path(path)
            if not is_valid:
                error_widget.update(error_msg)
            else:
                error_widget.update("")
        else:
            error_widget.update("")

    @on(Button.Pressed, "#generate_btn")
    def on_generate_pressed(self) -> None:
        """Handle generate button press."""
        path_input = self.query_one("#path_input", Input)
        path = path_input.value.strip()

        # Validate path
        if not path:
            self.query_one("#path_error", Static).update("Output path is required")
            path_input.focus()
            return

        is_valid, error_msg = validate_output_path(path)
        if not is_valid:
            self.query_one("#path_error", Static).update(error_msg)
            path_input.focus()
            return

        # Generate configuration using TUIState.generate_config
        try:
            app_state = self.app.state

            # Use the improved generate_config method that respects profile settings
            success = app_state.generate_config(output_path=path)

            if success:
                self.dismiss(True)
            else:
                self.dismiss(
                    "Failed to generate configuration. Check logs for details."
                )

        except Exception as e:
            logger.error(f"Exception in config generation: {e}")
            import traceback

            traceback.print_exc()
            self.dismiss(f"Failed to generate config: {str(e)}")

    @on(Button.Pressed, "#preview_btn")
    def on_preview_pressed(self) -> None:
        """Handle preview button press."""
        # TODO: Implement config preview in Phase 3
        self.app.notify("Config preview coming in Phase 3!", severity="info")

    @on(Button.Pressed, "#cancel_btn")
    def on_cancel_pressed(self) -> None:
        """Handle cancel button press."""
        self.dismiss(False)
