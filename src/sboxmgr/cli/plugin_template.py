"""Plugin template generator for sboxmgr extensions.

This module provides utilities for generating boilerplate code for custom
sboxmgr plugins such as parsers, exporters, validators, and middleware. It
helps developers create properly structured plugin classes that integrate
with the sboxmgr plugin registry system.
"""

import typer
import os

# Создаем app для тестирования
app = typer.Typer()

@app.command()
def plugin_template(
    type: str = typer.Argument(..., help="Type of plugin: fetcher, parser, validator, exporter, postprocessor, parsed_validator"),
    name: str = typer.Argument(..., help="Name of the plugin class (CamelCase)"),
    output_dir: str = typer.Option("plugin_templates", help="Directory to write the template files (will be created if not exists)")
):
    """Generate a plugin template (fetcher/parser/validator/exporter/postprocessor/parsed_validator) with test and Google-style docstring.

    By default, templates are written to the 'plugin_templates' directory in the current working directory.
    """
    type = type.lower()
    supported_types = {"fetcher", "parser", "validator", "exporter", "postprocessor", "parsed_validator"}
    if type not in supported_types:
        typer.echo(f"Type must be one of: {', '.join(supported_types)}", err=True)
        raise typer.Exit(1)
    
    # Определяем правильный суффикс для каждого типа
    type_suffix = {
        "fetcher": "Fetcher",
        "parser": "Parser", 
        "validator": "Validator",
        "exporter": "Exporter",
        "postprocessor": "PostProcessor",
        "parsed_validator": "ParsedValidator",
    }[type]
    
    # Если имя уже заканчивается на нужный суффикс, не добавлять его повторно
    class_name = name if name.endswith(type_suffix) else name + type_suffix
    file_name = f"{name.lower()}.py"
    test_file_name = f"template_test_{name.lower()}.py"
    
    # Base class and import
    if type == "fetcher":
        base = "BaseFetcher"
        base_import = "from ..base_fetcher import BaseFetcher"
        register_import = "from ..registry import register"
        decorator = f"@register(\"custom_{type}\")"
        doc = f"""{class_name} fetches subscription data from custom source.

    This fetcher implements the BaseFetcher interface to retrieve subscription
    data from a custom source. Customize the fetch method to implement your
    specific data retrieval logic.

    Example:
        source = SubscriptionSource(url="custom://example", source_type="custom_fetcher")
        fetcher = {class_name}(source)
        data = fetcher.fetch()
    """
        body = """    def fetch(self, force_reload: bool = False) -> bytes:
        \"\"\"Fetch subscription data from the configured source.

        Args:
            force_reload: Whether to bypass cache and force fresh data retrieval.

        Returns:
            Raw subscription data as bytes.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        \"\"\"
        raise NotImplementedError("Implement your custom fetch logic here")"""
    elif type == "parser":
        base = "BaseParser"
        base_import = "from ..base_parser import BaseParser"
        register_import = "from ..registry import register"
        decorator = f"@register(\"custom_{type}\")"
        doc = f"""{class_name} parses subscription data from custom format.

    This parser implements the BaseParser interface to convert raw subscription
    data into ParsedServer objects. Customize the parse method to handle your
    specific data format.

    Example:
        parser = {class_name}()
        servers = parser.parse(raw_data)
    """
        body = """    def parse(self, raw: bytes) -> list[ParsedServer]:
        \"\"\"Parse raw subscription data into server configurations.

        Args:
            raw: Raw subscription data as bytes.

        Returns:
            List of ParsedServer objects representing the server configurations.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        \"\"\"
        raise NotImplementedError("Implement your custom parsing logic here")"""
    elif type == "validator":
        base = "BaseValidator"
        base_import = "from ..validators.base import BaseValidator"
        register_import = ""
        decorator = ""
        doc = f"""{class_name} validates raw subscription data.

    This validator implements the BaseValidator interface to validate raw
    subscription data before parsing. Customize the validate method to
    implement your specific validation rules.

    Example:
        validator = {class_name}()
        result = validator.validate(raw_data)
    """
        body = """    def validate(self, raw: bytes, context=None):
        \"\"\"Validate raw subscription data.

        Args:
            raw: Raw subscription data as bytes.
            context: Optional validation context.

        Returns:
            ValidationResult indicating whether the data is valid.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        \"\"\"
        raise NotImplementedError("Implement your custom validation logic here")"""
    elif type == "parsed_validator":
        base = "BaseParsedValidator"
        base_import = "from ..validators.base import BaseParsedValidator"
        register_import = "from ..validators.base import register_parsed_validator"
        decorator = f"@register_parsed_validator(\"custom_{type}\")"
        doc = f"""{class_name} validates parsed server configurations.

    This validator implements the BaseParsedValidator interface to validate
    parsed server configurations. Customize the validate method to implement
    your specific validation rules for parsed servers.

    Example:
        validator = {class_name}()
        result = validator.validate(servers, context)
    """
        body = """    def validate(self, servers: list[ParsedServer], context):
        \"\"\"Validate parsed server configurations.

        Args:
            servers: List of parsed server configurations to validate.
            context: Pipeline context containing validation settings.

        Returns:
            ValidationResult indicating validation status and any errors.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        \"\"\"
        raise NotImplementedError("Implement your custom parsed validation logic here")"""
    elif type == "exporter":
        base = "BaseExporter"
        base_import = "from ..base_exporter import BaseExporter"
        register_import = "from ..registry import register"
        decorator = f"@register(\"custom_{type}\")"
        doc = f"""{class_name} exports parsed servers to custom configuration format.

    This exporter implements the BaseExporter interface to convert parsed
    server configurations into a specific configuration format. Customize
    the export method to generate your target configuration format.

    Example:
        exporter = {class_name}()
        config = exporter.export(servers)
    """
        body = """    def export(self, servers: list[ParsedServer]) -> dict:
        \"\"\"Export parsed servers to configuration format.

        Args:
            servers: List of parsed server configurations to export.

        Returns:
            Dictionary containing the exported configuration.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        \"\"\"
        raise NotImplementedError("Implement your custom export logic here")"""
    else:  # postprocessor
        base = "BasePostProcessor"
        base_import = "from ..postprocessor_base import BasePostProcessor"
        register_import = "from ..registry import register"
        decorator = f"@register(\"custom_{type}\")"
        doc = f"""{class_name} post-processes parsed server configurations.

    This post-processor implements the BasePostProcessor interface to modify
    or filter parsed server configurations. Customize the process method to
    implement your specific post-processing logic.

    Example:
        processor = {class_name}()
        processed_servers = processor.process(servers, context=context)
    """
        body = """    def process(self, servers: list[ParsedServer], context) -> list[ParsedServer]:
        \"\"\"Post-process parsed server configurations.

        Args:
            servers: List of parsed server configurations to process.
            context: Pipeline context containing processing settings.

        Returns:
            List of processed server configurations.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        \"\"\"
        raise NotImplementedError("Implement your custom post-processing logic here")"""

    # Build imports
    imports = f"{base_import}\nfrom ..models import SubscriptionSource, ParsedServer"
    if register_import:
        imports = f"{register_import}\n" + imports

    # Build class template
    if decorator:
        class_template = f"""{decorator}
class {class_name}({base}):
    \"\"\"{doc}\"\"\"

{body}
"""
    else:
        class_template = f"""class {class_name}({base}):
    \"\"\"{doc}\"\"\"

{body}
"""

    template = f"{imports}\n\n\n{class_template}"

    # Build test template with correct import path
    if type == "validator":
        test_import_path = f"from sboxmgr.subscription.validators.{class_name.lower()} import {class_name}"
    elif type == "parsed_validator":
        test_import_path = f"from sboxmgr.subscription.validators.{class_name.lower()} import {class_name}"
    else:
        test_import_path = f"from sboxmgr.subscription.{type}s.{class_name.lower()} import {class_name}"

    test_template = f"""# This is a template file - copy to your test directory and modify as needed
import pytest
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
{test_import_path}


def test_{class_name.lower()}_basic():
    \"\"\"Test basic {class_name} functionality.\"\"\"
    # Example: instantiate and check NotImplementedError
    plugin = {class_name}()
    with pytest.raises(NotImplementedError):
        {'plugin.fetch(None)' if type == 'fetcher' else 'plugin.parse(b"test")' if type == 'parser' else 'plugin.validate(b"test", None)' if type == 'parsed_validator' else 'plugin.validate(b"test")' if type == 'validator' else 'plugin.export([])' if type == 'exporter' else 'plugin.process([], None)'}
"""

    # Ensure output_dir exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        typer.echo(f"[ERROR] Failed to create output directory '{output_dir}': {e}", err=True)
        raise typer.Exit(1)

    out_path = os.path.join(output_dir, file_name)
    test_out_path = os.path.join(output_dir, test_file_name)

    typer.echo(f"[DEBUG] Attempting to write template to {out_path}")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(template)
        typer.echo(f"[DEBUG] Successfully wrote {out_path}")
        
        with open(test_out_path, "w", encoding="utf-8") as f:
            f.write(test_template)
        typer.echo(f"[DEBUG] Successfully wrote {test_out_path}")
        
        typer.echo(f"Created {out_path} and {test_out_path}")
        if decorator:
            typer.echo("[DX] Don't forget to register your plugin in the registry and add tests!")
    except Exception as e:
        typer.echo(f"[ERROR] Failed to write template files: {e}", err=True)
        raise typer.Exit(1) 