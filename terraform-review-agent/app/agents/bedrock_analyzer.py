import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.bedrock_client import BedrockClient
from shared.config import settings
from ..models import TerraformChange, SecurityFinding, AIAnalysis, RiskLevel


class BedrockAnalyzer:
    def __init__(self, model_alias: str = "titan-express"):
        self.client = BedrockClient(model_alias=model_alias)

    def analyze_changes(
        self,
        changes: list[TerraformChange],
        terrascan_findings: list[SecurityFinding],
    ) -> AIAnalysis:
        prompt = self._build_analysis_prompt(changes, terrascan_findings)
        system_prompt = self._get_system_prompt()

        response = self.client.invoke(prompt, system_prompt=system_prompt)
        return self._parse_analysis(response, terrascan_findings)

    def _get_system_prompt(self) -> str:
        return """You are an expert Terraform code reviewer and cloud security specialist.
Analyze the provided Terraform changes and security findings to provide:
1. A concise summary of the changes
2. A risk score from 0-100
3. Risk level (critical, high, medium, low, info)
4. Key security findings
5. Actionable recommendations

Be specific about security implications, compliance issues, and best practice violations.
Format your response as JSON with the structure:
{
  "summary": "string",
  "risk_score": number,
  "risk_level": "string",
  "findings": [{"rule_id": "string", "severity": "string", "resource": "string", "message": "string", "remediation": "string"}],
  "recommendations": ["string"]
}"""

    def _build_analysis_prompt(
        self,
        changes: list[TerraformChange],
        terrascan_findings: list[SecurityFinding],
    ) -> str:
        changes_text = ""
        for c in changes:
            changes_text += f"- File: {c.file}, Resource: {c.resource_type}.{c.resource_name}, Change: {c.change_type}\n"

        findings_text = ""
        for f in terrascan_findings:
            findings_text += f"- [{f.severity}] {f.rule_id}: {f.message} (Resource: {f.resource})\n"

        return f"""Analyze these Terraform changes and security findings:

Terraform Changes:
{changes_text}

Terrascan Security Findings:
{findings_text}

Provide your analysis as JSON."""

    def _parse_analysis(self, response: str, existing_findings: list[SecurityFinding]) -> AIAnalysis:
        import json
        import re

        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                findings = existing_findings + [
                    SecurityFinding(
                        rule_id=f.get("rule_id", "AI_FINDING"),
                        severity=RiskLevel(f.get("severity", "info")),
                        resource=f.get("resource", "unknown"),
                        message=f.get("message", ""),
                        remediation=f.get("remediation"),
                    )
                    for f in data.get("findings", [])
                ]
                return AIAnalysis(
                    summary=data.get("summary", "Analysis complete"),
                    risk_score=min(100, max(0, data.get("risk_score", 50))),
                    risk_level=RiskLevel(data.get("risk_level", "medium")),
                    findings=findings,
                    recommendations=data.get("recommendations", []),
                )
        except (json.JSONDecodeError, ValueError):
            pass

        return AIAnalysis(
            summary=response[:500] if response else "Unable to generate analysis",
            risk_score=50,
            risk_level=RiskLevel.MEDIUM,
            findings=existing_findings,
            recommendations=["Review the Terraform changes manually"],
        )
