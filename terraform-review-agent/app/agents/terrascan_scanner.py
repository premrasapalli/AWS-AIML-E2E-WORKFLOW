import subprocess
import json
from typing import Optional
from ..models import SecurityFinding, RiskLevel


class TerrascanScanner:
    def __init__(self):
        self.scanner = "terrascan"

    def scan(self, path: str, scan_type: str = "tf") -> list[SecurityFinding]:
        findings = []
        try:
            result = subprocess.run(
                [
                    self.scanner, "scan",
                    "-d", path,
                    "-t", scan_type,
                    "-o", "json",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            findings = self._parse_output(result.stdout)
        except FileNotFoundError:
            findings = [
                SecurityFinding(
                    rule_id="TERRASCAN_NOT_INSTALLED",
                    severity=RiskLevel.HIGH,
                    resource="system",
                    message="Terrascan is not installed. Install with: brew install terrascan",
                    remediation="Install terrascan: https://terrascan.io/docs/installation/",
                )
            ]
        except subprocess.TimeoutExpired:
            findings = [
                SecurityFinding(
                    rule_id="SCAN_TIMEOUT",
                    severity=RiskLevel.MEDIUM,
                    resource="system",
                    message="Terrascan scan timed out after 120 seconds",
                )
            ]
        except Exception as e:
            findings = [
                SecurityFinding(
                    rule_id="SCAN_ERROR",
                    severity=RiskLevel.HIGH,
                    resource="system",
                    message=f"Terrascan scan failed: {str(e)}",
                )
            ]
        return findings

    def _parse_output(self, stdout: str) -> list[SecurityFinding]:
        findings = []
        try:
            data = json.loads(stdout)
            for violation in data.get("results", {}).get("violations", []):
                severity_map = {
                    "HIGH": RiskLevel.HIGH,
                    "MEDIUM": RiskLevel.MEDIUM,
                    "LOW": RiskLevel.LOW,
                    "CRITICAL": RiskLevel.CRITICAL,
                }
                findings.append(
                    SecurityFinding(
                        rule_id=violation.get("rule_id", "UNKNOWN"),
                        severity=severity_map.get(
                            violation.get("severity", "MEDIUM"), RiskLevel.MEDIUM
                        ),
                        resource=violation.get("resource_name", "unknown"),
                        message=violation.get("description", "No description"),
                        remediation=violation.get("remediation"),
                    )
                )
        except json.JSONDecodeError:
            pass
        return findings
