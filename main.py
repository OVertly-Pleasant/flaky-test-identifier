import typer
from rich.table import Table
from rich.console import Console
from analyzer import generate_flakiness_report

app = typer.Typer()
console = Console()

@app.command()
def analyse(owner: str = typer.Argument(), repo: str = typer.Argument(), top: int = 5):
    database = f"{owner}_{repo}.db"
    report = generate_flakiness_report(top, database)
    
    if report.empty:
        console.print(f"[red]No data found in {database}. Run harvester first.[/red]")
        return

    table = Table(title=f"Flaky Test Analysis: {owner}/{repo}")
    table.add_column("Test Name", justify="left", style="cyan")
    table.add_column("Ultimate Score", justify="center", style="bold white")
    table.add_column("Flip Rate", justify="center")
    table.add_column("Duration Anomaly", justify="center")
    table.add_column("Time Anomaly", justify="center")
    table.add_column("Pass Rate", justify="center")

    for idx, row in report.iterrows():
        test_name = str(row['test_name'])
        
        ultimate = color_flakiness(row['ultimate_score'])
        flip = color_flakiness(row['flip_score'])
        duration = color_flakiness(row['duration_score'])
        time_score = color_flakiness(row['time_score'])
        pass_rate = f"{row['pass_rate']:.0%}"
        
        table.add_row(test_name, ultimate, flip, duration, time_score, pass_rate)

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