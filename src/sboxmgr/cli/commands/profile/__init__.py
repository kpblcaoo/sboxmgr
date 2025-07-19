"""Profile management commands for sboxmgr (ADR-0020).

This package provides CLI commands for managing FullProfile configurations,
including listing, creating, editing, validating, and managing active profiles.
"""

import typer

from . import delete, edit, export, import_cmd, list, new, set_active, show, validate

# Create the main profile app
app = typer.Typer(
    name="profile",
    help="Manage FullProfile configurations",
    add_completion=False,
)

# Register subcommands
app.command("list")(list.list_profiles)
app.command("show")(show.show_profile)
app.command("new")(new.new_profile)
app.command("edit")(edit.edit_profile)
app.command("validate")(validate.validate_profile)
app.command("set-active")(set_active.set_active_profile)
app.command("delete")(delete.delete_profile)
app.command("import")(import_cmd.import_profile)
app.command("export")(export.export_profile)
