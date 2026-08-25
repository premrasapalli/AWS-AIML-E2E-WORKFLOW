import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from app.collectors.log_collector import LogCollector
from app.collectors.event_collector import EventCollector
from app.ai.bedrock_diagnoser import BedrockDiagnoser

console = Console()


@click.group()
def cli():
    """AI-Powered K8s Pod Debugger - Diagnose failing Kubernetes pods with AI."""
    pass


@cli.command()
@click.option("--namespace", "-n", required=True, help="Kubernetes namespace")
@click.option("--pod", "-p", help="Pod name")
@click.option("--label", "-l", help="Label selector (e.g., app=nginx)")
@click.option("--container", "-c", help="Container name")
@click.option("--tail", default=100, help="Number of log lines to fetch")
@click.option("--model", default="titan-express", help="Bedrock model alias")
@click.option("--output", type=click.Choice(["table", "json"]), default="table")
def debug(namespace: str, pod: str, label: str, container: str, tail: int, model: str, output: str):
    """Debug a failing Kubernetes pod."""
    if not pod and not label:
        console.print("[red]Error: Either --pod or --label is required[/red]")
        return

    if label and not pod:
        pod = _get_pod_by_label(namespace, label)
        if not pod:
            console.print(f"[red]No pod found with label: {label}[/red]")
            return

    console.print(f"\n[bold blue]Debugging pod: {pod} in namespace: {namespace}[/bold blue]\n")

    log_collector = LogCollector()
    event_collector = EventCollector()

    console.print("[yellow]Fetching events...[/yellow]")
    events = event_collector.get_events(namespace, pod)

    console.print("[yellow]Fetching logs...[/yellow]")
    logs = log_collector.get_logs(namespace, pod, container, tail)

    console.print("[yellow]Running AI diagnosis...[/yellow]")
    diagnoser = BedrockDiagnoser(model_alias=model)
    from app.models import ContainerStatus
    analysis = diagnoser.diagnose(
        pod_name=pod,
        namespace=namespace,
        phase="Failed",
        container_statuses=[],
        events=events,
        logs=logs,
    )

    if output == "json":
        result = {
            "pod": pod,
            "namespace": namespace,
            "events": [e.model_dump() for e in events],
            "logs": [l.model_dump() for l in logs],
            "analysis": analysis.model_dump(),
            "model_used": model,
        }
        click.echo(json.dumps(result, indent=2))
    else:
        display_results(pod, namespace, events, logs, analysis, model)


def _get_pod_by_label(namespace: str, label: str) -> str:
    import subprocess
    try:
        result = subprocess.run(
            [
                "kubectl", "get", "pods",
                "-n", namespace,
                "-l", label,
                "-o", "jsonpath={.items[0].metadata.name}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def display_results(pod, namespace, events, logs, analysis, model):
    console.print(Panel(f"Pod: {pod}\nNamespace: {namespace}", title="Pod Info"))

    if events:
        events_table = Table(title="Events")
        events_table.add_column("Type", style="yellow")
        events_table.add_column("Reason", style="cyan")
        events_table.add_column("Message")
        events_table.add_column("Age", style="green")
        for e in events:
            events_table.add_row(e.type, e.reason, e.message[:60], e.age)
        console.print(events_table)

    for l in logs:
        console.print(Panel(l.logs[-2000:] if len(l.logs) > 2000 else l.logs, title=f"Logs ({l.container})"))

    if analysis:
        confidence_color = "green" if analysis.confidence >= 70 else "yellow" if analysis.confidence >= 40 else "red"
        console.print(Panel(
            f"[bold {confidence_color}]Root Cause ({analysis.confidence}% confidence):[/bold {confidence_color}] {analysis.root_cause}\n\n"
            f"[bold]Category:[/bold] {analysis.category}\n"
            f"[bold]Explanation:[/bold] {analysis.explanation}\n\n"
            f"[bold]Suggested Fixes:[/bold]\n" +
            "\n".join(f"  • {f}" for f in analysis.suggested_fixes),
            title=f"AI Diagnosis (Model: {model})",
        ))


if __name__ == "__main__":
    cli()
