import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.bedrock_client import BedrockClient
from ..models import SecurityIssue, AIExplanation


class BedrockExplainer:
    def __init__(self, model_alias: str = "titan-express"):
        self.client = BedrockClient(model_alias=model_alias)

    def explain_issue(self, issue: SecurityIssue) -> AIExplanation:
        prompt = self._build_explanation_prompt(issue)
        system_prompt = self._get_system_prompt()

        response = self.client.invoke(prompt, system_prompt=system_prompt)
        return self._parse_response(response, issue)

    def _get_system_prompt(self) -> str:
        return """You are a cloud security expert explaining infrastructure security issues.
For each security issue, provide:
1. A clear explanation of the vulnerability
2. The potential impact if exploited
3. A specific fix suggestion
4. Relevant compliance framework references (CIS, NIST, SOC2, PCI-DSS, etc.)

Format your response as JSON:
{
  "explanation": "string",
  "impact": "string",
  "fix_suggestion": "string",
  "compliance_references": ["string"]
}"""

    def _build_explanation_prompt(self, issue: SecurityIssue) -> str:
        return f"""Explain this security issue found in infrastructure code:

Rule ID: {issue.rule_id}
Severity: {issue.severity.value}
File: {issue.file_path}
Resource: {issue.resource_type}/{issue.resource_name}
Message: {issue.message}
{f'Line: {issue.line_number}' if issue.line_number else ''}
{f'Remediation: {issue.remediation}' if issue.remediation else ''}

Provide your explanation as JSON."""

    def _parse_response(self, response: str, issue: SecurityIssue) -> AIExplanation:
        import json
        import re

        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return AIExplanation(
                    issue_id=issue.rule_id,
                    explanation=data.get("explanation", issue.message),
                    impact=data.get("impact", "Unknown impact"),
                    fix_suggestion=data.get("fix_suggestion", issue.remediation or "Review configuration"),
                    compliance_references=data.get("compliance_references", []),
                )
        except (json.JSONDecodeError, ValueError):
            pass

        return AIExplanation(
            issue_id=issue.rule_id,
            explanation=issue.message,
            impact="Requires manual review",
            fix_suggestion=issue.remediation or "Review the configuration",
            compliance_references=[],
        )
