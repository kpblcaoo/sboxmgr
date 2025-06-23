import typer
import textwrap
import os

def plugin_template(
    type: str = typer.Argument(..., help="Type of plugin: fetcher, parser, validator, exporter, postprocessor"),
    name: str = typer.Argument(..., help="Name of the plugin class (CamelCase)"),
    output_dir: str = typer.Option("./", help="Directory to write the template files")
):
    """Generate a plugin template (fetcher/parser/validator/exporter/postprocessor) with test and Google-style docstring."""
    type = type.lower()
    supported_types = {"fetcher", "parser", "validator", "exporter", "postprocessor"}
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
    }[type]
    # Если имя уже заканчивается на нужный суффикс, не добавлять его повторно
    class_name = name if name.endswith(type_suffix) else name + type_suffix
    file_name = class_name.lower() + ".py"
    test_file_name = f"test_{class_name.lower()}.py"
    # Base class and import
    if type == "fetcher":
        base = "BaseFetcher"
        base_import = "from ..base_fetcher import BaseFetcher"
        register_import = "from ..registry import register"
        decorator = f"@register(\"custom_{type}\")"
        doc = f"""{class_name} fetches subscription data.\n\n    Example:\n        fetcher = {class_name}(source)\n        data = fetcher.fetch()\n    """.strip()
        body = """\n    def fetch(self, force_reload: bool = False) -> bytes:\n        \n        \"\"\"Fetch subscription data.\n\n        Args:\n            force_reload (bool, optional): Force reload and ignore cache.\n\n        Returns:\n            bytes: Raw data.\n        \"\"\"\n        raise NotImplementedError()\n"""
    elif type == "parser":
        base = "BaseParser"
        base_import = "from ..base_parser import BaseParser"
        register_import = "from ..registry import register"
        decorator = f"@register(\"custom_{type}\")"
        doc = f"""{class_name} parses subscription data.\n\n    Example:\n        parser = {class_name}()\n        servers = parser.parse(raw)\n    """.strip()
        body = """\n    def parse(self, raw: bytes):\n        \n        \"\"\"Parse subscription data.\n\n        Args:\n            raw (bytes): Raw data.\n\n        Returns:\n            list[ParsedServer]: Servers.\n        \"\"\"\n        raise NotImplementedError()\n"""
    elif type == "validator":
        base = "BaseValidator"
        base_import = "from ..validators.base import BaseValidator"
        register_import = ""
        decorator = ""
        doc = f"""{class_name} validates subscription data.\n\n    Example:\n        validator = {class_name}()\n        result = validator.validate(raw)\n    """.strip()
        body = """\n    def validate(self, raw: bytes):\n        \n        \"\"\"Validate subscription data.\n\n        Args:\n            raw (bytes): Raw data.\n\n        Returns:\n            ValidationResult: Result.\n        \"\"\"\n        raise NotImplementedError()\n"""
    elif type == "exporter":
        base = "BaseExporter"
        base_import = "from ..base_exporter import BaseExporter"
        register_import = "from ..registry import register"
        decorator = f"@register(\"custom_{type}\")"
        doc = f"""{class_name} exports parsed servers to config.\n\n    Example:\n        exporter = {class_name}()\n        config = exporter.export(servers)\n    """.strip()
        body = """\n    def export(self, servers):\n        \n        \"\"\"Export parsed servers to config.\n\n        Args:\n            servers (list[ParsedServer]): List of servers.\n\n        Returns:\n            dict: Exported config.\n        \"\"\"\n        raise NotImplementedError()\n"""
    else:  # postprocessor
        base = "BasePostProcessor"
        base_import = "from ..postprocessor_base import BasePostProcessor"
        register_import = "from ..registry import register"
        decorator = f"@register(\"custom_{type}\")"
        doc = f"""{class_name} post-processes parsed servers.\n\n    Example:\n        pp = {class_name}()\n        servers = pp.process(servers, context)\n    """.strip()
        body = """\n    def process(self, servers, context):\n        \n        \"\"\"Post-process parsed servers.\n\n        Args:\n            servers (list[ParsedServer]): List of servers.\n            context (PipelineContext): Pipeline context.\n\n        Returns:\n            list[ParsedServer]: Processed servers.\n        \"\"\"\n        raise NotImplementedError()\n"""
    imports = f"{base_import}\nfrom ..models import SubscriptionSource, ParsedServer"
    if register_import:
        imports = f"{register_import}\n" + imports
    class_block = textwrap.dedent(f"""
    {decorator}
    class {class_name}({base}):
        \"\"\"{doc}\"\"\"
        {body}
    """) if decorator else textwrap.dedent(f"""
    class {class_name}({base}):
        \"\"\"{doc}\"\"\"
        {body}
    """)
    template = f"{imports}\n\n{class_block}"
    test_template = textwrap.dedent(f"""
    import pytest
    from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
    from sboxmgr.subscription.{type}s.{class_name.lower()} import {class_name}

    def test_{class_name.lower()}_basic():
        # Example: instantiate and check NotImplementedError
        plugin = {class_name}()
        with pytest.raises(NotImplementedError):
            {'plugin.fetch(None)' if type == 'fetcher' else 'plugin.parse(b"test")' if type == 'parser' else 'plugin.validate(b"test")' if type == 'validator' else 'plugin.export([])' if type == 'exporter' else 'plugin.process([], None)'}
    """)
    out_path = os.path.join(output_dir, file_name)
    test_out_path = os.path.join(output_dir, test_file_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(template)
    with open(test_out_path, "w", encoding="utf-8") as f:
        f.write(test_template)
    typer.echo(f"Created {out_path} and {test_out_path}")
    if decorator:
        typer.echo(f"[DX] Don't forget to register your plugin in the registry and add tests!") 