import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from app.scanners.k8s_scanner import K8sScanner
from app.scanners.docker_scanner import DockerScanner
from app.scanners.terraform_scanner import TerraformScanner
from app.ai.bedrock_explainer import BedrockExplainer

console = Console()


@click.group()
def cli():
    """AI Infrastructure Auditor - Scan K8s, Docker, and Terraform for security issues."""
    pass


@cli.command()
@click.option("--path", required=True, help="Path to scan")
@click.option("--type", "scan_type", type=click.Choice(["k8s", "docker", "terraform", "all"]), default="all")
@click.option("--model", default="titan-express", help="Bedrock model alias")
@click.option("--no-ai", is_flag=True, help="Disable AI explanations")
@click.option("--output", type=click.Choice(["table", "json"]), default="table")
def scan(path: str, scan_type: str, model: str, no_ai: bool, output: str):
    """Scan infrastructure files for security issues."""
    console.print(f"\n[bold blue]Scanning: {path}[/bold blue]\n")

    all_issues = []

    if scan_type in ["k8s", "all"]:
        console.print("[yellow]Scanning Kubernetes manifests...[/yellow]")
        k8s = K8sScanner()
        all_issues.extend(k8s.scan_directory(path))

    if scan_type in ["docker", "all"]:
        console.print("[yellow]Scanning Docker Compose files...[/yellow]")
        docker = DockerScanner()
        all_issues.extend(docker.scan_directory(path))

    if scan_type in ["terraform", "all"]:
        console.print("[yellow]Scanning Terraform files...[/yellow]")
        terraform = TerraformScanner()
        all_issues.extend(terraform.scan_directory(path))

    ai_explanations = []
    if not no_ai and all_issues:
        console.print("[yellow]Generating AI explanations...[/yellow]")
        try:
            explainer = BedrockExplainer(model_alias=model)
            for issue in all_issues[:10]:
                ai_explanations.append(explainer.explain_issue(issue))
        except Exception as e:
            console.print(f"[red]AI explanations unavailable: {e}[/red]")

    if output == "json":
        result = {
            "issues": [i.model_dump() for i in all_issues],
            "ai_explanations": [e.model_dump() for e in ai_explanations],
            "summary": {
                "total": len(all_issues),
                "critical": sum(1 for i in all_issues if i.severity.value == "critical"),
                "high": sum(1 for i in all_issues if i.severity.value == "high"),
                "medium": sum(1 for i in all_issues if i.severity.value == "medium"),
                "low": sum(1 for i in all_issues if i.severity.value == "low"),
            },
        }
        click.echo(json.dumps(result, indent=2))
    else:
        display_results(all_issues, ai_explanations, model)


def display_results(issues, ai_explanations, model):
    if not issues:
        console.print("[green]No security issues found![/green]")
        return

    table = Table(title="Security Findings")
    table.add_column("Rule", style="red")
    table.add_column("Severity", style="yellow")
    table.add_column("Resource")
    table.add_column("Message")

    for issue in issues:
        table.add_row(issue.rule_id, issue.severity.value, f"{issue.resource_type}/{issue.resource_name}", issue.message[:50])
    console.print(table)

    summary = {
        "critical": sum(1 for i in issues if i.severity.value == "critical"),
        "high": sum(1 for i in issues if i.severity.value == "high"),
        "medium": sum(1 for i in issues if i.severity.value == "medium"),
        "low": sum(1 for i in issues if i.severity.value == "low"),
    }
    console.print(Panel(
        f"🔴 Critical: {summary['critical']}  🟠 High: {summary['high']}  🟡 Medium: {summary['medium']}  🟢 Low: {summary['low']}",
        title="Summary",
    ))

    if ai_explanations:
        console.print(f"\n[bold]AI Explanations (Model: {model}):[/bold]\n")
        for exp in ai_explanations:
            console.print(f"[cyan]{exp.issue_id}:[/cyan]")
            console.print(f"  Explanation: {exp.explanation[:100]}")
            console.print(f"  Impact: {exp.impact[:100]}")
            console.print(f"  Fix: {exp.fix_suggestion[:100]}")
            if exp.compliance_references:
                console.print(f"  Compliance: {', '.join(exp.compliance_references)}")
            console.print()


if __name__ == "__main__":
    cli()
