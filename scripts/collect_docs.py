#!/usr/bin/env python3
"""
Скрипт для сбора всех планов и документации в один файл.
Аналогично collect_code.py, но для документации.
"""

from pathlib import Path


def get_file_content(file_path: Path) -> str:
    """Читает содержимое файла."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"# ОШИБКА ЧТЕНИЯ ФАЙЛА: {e}\n\n"


def collect_plans() -> list[tuple[str, str]]:
    """Собирает все файлы из папки plans."""
    plans_dir = Path("plans")
    if not plans_dir.exists():
        return []

    files = []

    # Рекурсивно обходим все файлы в plans
    for file_path in plans_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in [".md", ".txt", ".json"]:
            relative_path = file_path.relative_to(plans_dir)
            content = get_file_content(file_path)
            files.append((str(relative_path), content))

    return sorted(files)


def collect_docs() -> list[tuple[str, str]]:
    """Собирает все файлы из папки docs."""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        return []

    files = []

    # Рекурсивно обходим все файлы в docs
    for file_path in docs_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in [".md", ".txt", ".json"]:
            relative_path = file_path.relative_to(docs_dir)
            content = get_file_content(file_path)
            files.append((str(relative_path), content))

    return sorted(files)


def collect_readme_files() -> list[tuple[str, str]]:
    """Собирает README файлы из корня проекта."""
    root_dir = Path(".")
    files = []

    for file_path in root_dir.glob("README*"):
        if file_path.is_file() and file_path.suffix in [".md", ".txt"]:
            content = get_file_content(file_path)
            files.append((file_path.name, content))

    return sorted(files)


def collect_schemas() -> list[tuple[str, str]]:
    """Собирает JSON схемы."""
    schemas_dir = Path("schemas")
    if not schemas_dir.exists():
        return []

    files = []

    for file_path in schemas_dir.glob("*.json"):
        content = get_file_content(file_path)
        files.append((file_path.name, content))

    return sorted(files)


def main():
    """Основная функция."""
    output_file = "ALL_DOCUMENTATION.md"

    print("Собираю всю документацию...")

    # Собираем все разделы
    sections = []

    # README файлы
    readme_files = collect_readme_files()
    if readme_files:
        sections.append(("# README ФАЙЛЫ\n", readme_files))

    # Планы
    plans_files = collect_plans()
    if plans_files:
        sections.append(("# ПЛАНЫ (plans/)\n", plans_files))

    # Документация
    docs_files = collect_docs()
    if docs_files:
        sections.append(("# ДОКУМЕНТАЦИЯ (docs/)\n", docs_files))

    # Схемы
    schemas_files = collect_schemas()
    if schemas_files:
        sections.append(("# JSON СХЕМЫ (schemas/)\n", schemas_files))

    # Генерируем итоговый файл
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# ВСЯ ДОКУМЕНТАЦИЯ ПРОЕКТА SBOXMGR\n\n")
        f.write(
            "Этот файл содержит всю документацию проекта, собранную автоматически.\n\n"
        )
        f.write("---\n\n")

        for section_title, files in sections:
            f.write(section_title)
            f.write("\n")

            for file_name, content in files:
                f.write(f"## {file_name}\n\n")
                f.write("```\n")
                f.write(content)
                f.write("```\n\n")
                f.write("---\n\n")

    print(f"Документация собрана в файл: {output_file}")
    print(f"Всего разделов: {len(sections)}")

    total_files = sum(len(files) for _, files in sections)
    print(f"Всего файлов: {total_files}")


if __name__ == "__main__":
    main()
