import os
import shutil
import pytest
from typer.testing import CliRunner
from sboxmgr.cli import plugin_template

runner = CliRunner()

ALL_TYPES = [
    "fetcher",
    "parser",
    "validator",
    "exporter",
    "postprocessor",
    "parsed_validator",
]

def clean_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def test_plugin_template_generates_all_types(tmp_path):
    output_dir = tmp_path / "plugin_templates"
    clean_dir(output_dir)
    for t in ALL_TYPES:
        name = f"Test{t.title().replace('_', '')}"
        result = runner.invoke(plugin_template.app, [t, name, "--output-dir", str(output_dir)])
        assert result.exit_code == 0, f"Failed for type {t}: {result.output}"
        py_file = output_dir / f"{name.lower()}.py"
        test_file = output_dir / f"test_{name.lower()}.py"
        assert py_file.exists(), f"{py_file} not created"
        assert test_file.exists(), f"{test_file} not created"
        # Проверяем docstring и импорты
        content = py_file.read_text(encoding="utf-8")
        assert '"""' in content, f"No docstring in {py_file}"
        assert "from" in content, f"No import in {py_file}"

def test_plugin_template_invalid_type(tmp_path):
    output_dir = tmp_path / "plugin_templates"
    clean_dir(output_dir)
    result = runner.invoke(plugin_template.app, ["invalidtype", "TestInvalid", "--output-dir", str(output_dir)])
    assert result.exit_code != 0
    assert "Type must be one of" in result.output

def test_plugin_template_output_dir_error(monkeypatch, tmp_path):
    # Симулируем ошибку создания директории
    def fail_makedirs(*a, **kw):
        raise OSError("fail")
    monkeypatch.setattr(os, "makedirs", fail_makedirs)
    result = runner.invoke(plugin_template.app, ["fetcher", "TestFetcher", "--output-dir", str(tmp_path / "fail_dir")])
    assert result.exit_code != 0
    assert "Failed to create output directory" in result.output 