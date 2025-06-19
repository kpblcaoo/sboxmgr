import typer

app = typer.Typer(help="sboxctl: Sing-box config manager (exclusions, dry-run, selection, etc.)")

# Команды будут добавляться по мере декомпозиции

if __name__ == "__main__":
    app() 