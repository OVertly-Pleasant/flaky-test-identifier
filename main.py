import typer
from rich.table import Table
from rich.console import Console
from analyzer import generate_flakiness_report

app = typer.Typer()
console = Console()

@app.command()
def analyse(owner: str = typer.Argument(),repo: str = typer.Argument(), top: int = 5, show_passrate: bool = False):
    database = f"{owner}_{repo}.db"
    pass_rate = generate_flakiness_report(top,database)
    header = f"Flaky Test Analysis of {database}"
    table = Table(title=header)
    table.add_column("Test",justify="center",no_wrap=True)
    table.add_column("Flakiness",justify="center",no_wrap=True)
    if show_passrate:
        table.add_column("Pass Rate",justify="center",no_wrap=True)
    for idx,row in pass_rate.iterrows():
        test_name = str(row['test_name'])
        flaky_val = color_flakiness(row["flakiness"])
        if show_passrate:
            pass_val = f"{row['pass_rate']:.0%}" 
            table.add_row(test_name, flaky_val, pass_val)
        else:
            table.add_row(test_name, flaky_val)
    console.print(table)

def color_flakiness(val: float):
    '''
    Colorises the flakiness based on severity (0.0 to 1.0 scale)
    Score > 0.40 = Red (Highly Flaky, flips almost every other run)
    Score > 0.15 = Yellow (Warning, occasional flips)
    Score <= 0.15 = Green (Stable)
    '''
    if val > 0.40:
        return f"[red]{val:.2f}[/red]"
    elif val > 0.15:
        return f"[yellow]{val:.2f}[/yellow]"
    else:
        return f"[green]{val:.2f}[/green]"

if __name__ == "__main__":
    app()