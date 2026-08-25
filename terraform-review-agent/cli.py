import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from app.agents.terraform_parser import TerraformParser
from app.agents.terrascan_scanner import TerrascanScanner
from app.agents.bedrock_analyzer import BedrockAnalyzer

console = Console()


@click.group()
def cli():
    """AI Terraform Review Agent - Automated Terraform code review with AI analysis."""
    pass


@cli.command()
@click.option("--repo", required=True, help="Path to Terraform repository")
@click.option("--model", default="ollama", help="Model alias (ollama, ollama-llama3, nova-lite, etc)")
@click.option("--output", type=click.Choice(["table", "json"]), default="table")
def review(repo: str, model: str, output: str):
    """Review Terraform code for security issues and best practices."""
    console.print(f"\n[bold blue]Analyzing Terraform in: {repo}[/bold blue]\n")

    parser = TerraformParser()
    scanner = TerrascanScanner()
    analyzer = BedrockAnalyzer(model_alias=model)

    tf_files = parser.get_terraform_files(repo)
    console.print(f"[green]Found {len(tf_files)} Terraform files[/green]")

    changes = []
    for tf_file in tf_files:
        resources = parser.parse_hcl(tf_file)
        for key, resource in resources.items():
            from app.models import TerraformChange
            changes.append(
                TerraformChange(
                    file=tf_file,
                    resource_type=resource["type"],
                    resource_name=resource["name"],
                    change_type="existing",
                )
            )

    console.print("[yellow]Running Terrascan security scan...[/yellow]")
    terrascan_findings = scanner.scan(repo)

    console.print("[yellow]Running AI analysis...[/yellow]")
    try:
        ai_analysis = analyzer.analyze_changes(changes, terrascan_findings)
    except Exception as e:
        console.print(f"[red]AI analysis unavailable: {e}[/red]")
        from app.models import AIAnalysis, RiskLevel
        ai_analysis = AIAnalysis(
            summary="AI analysis unavailable - configure AWS credentials for Bedrock access",
            risk_score=50,
            risk_level=RiskLevel.MEDIUM,
            findings=terrascan_findings,
            recommendations=["Configure AWS credentials: aws configure", "Enable Amazon Titan in Bedrock console"],
        )

    if output == "json":
        result = {
            "changes": [c.model_dump() for c in changes],
            "terrascan_findings": [f.model_dump() for f in terrascan_findings],
            "ai_analysis": ai_analysis.model_dump(),
            "model_used": model,
        }
        click.echo(json.dumps(result, indent=2))
    else:
        display_results(changes, terrascan_findings, ai_analysis, model)


def display_results(changes, terrascan_findings, ai_analysis, model):
    table = Table(title="Terraform Resources")
    table.add_column("File", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Name", style="magenta")
    for c in changes[:20]:
        table.add_row(c.file, c.resource_type, c.resource_name)
    console.print(table)

    if terrascan_findings:
        findings_table = Table(title="Security Findings")
        findings_table.add_column("Rule", style="red")
        findings_table.add_column("Severity", style="yellow")
        findings_table.add_column("Resource")
        findings_table.add_column("Message")
        for f in terrascan_findings:
            findings_table.add_row(f.rule_id, f.severity.value, f.resource, f.message[:60])
        console.print(findings_table)

    risk_color = {"critical": "red", "high": "red", "medium": "yellow", "low": "green", "info": "blue"}
    color = risk_color.get(ai_analysis.risk_level.value, "white")
    console.print(Panel(
        f"[bold {color}]Risk Score: {ai_analysis.risk_score}/100 ({ai_analysis.risk_level.value.upper()})[/bold {color}]\n\n"
        f"{ai_analysis.summary}\n\n"
        f"[bold]Recommendations:[/bold]\n" +
        "\n".join(f"  • {r}" for r in ai_analysis.recommendations),
        title=f"AI Analysis (Model: {model})",
    ))


if __name__ == "__main__":
    cli()
