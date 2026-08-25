import subprocess
import json
import os
from ..models import SecurityIssue, RiskLevel


class TerraformScanner:
    def scan_file(self, file_path: str) -> list[SecurityIssue]:
        issues = []
        try:
            result = subprocess.run(
                ["tfsec", "--format=json", file_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            issues = self._parse_output(result.stdout, file_path)
        except FileNotFoundError:
            issues.append(
                SecurityIssue(
                    rule_id="TFSEC_NOT_INSTALLED",
                    severity=RiskLevel.HIGH,
                    file_path=file_path,
                    resource_type="system",
                    resource_name="tfsec",
                    message="tfsec is not installed. Install with: brew install tfsec",
                    remediation="Install tfsec: https://aquasecurity.github.io/tfsec/latest/getting-started/install/",
                )
            )
        except subprocess.TimeoutExpired:
            issues.append(
                SecurityIssue(
                    rule_id="SCAN_TIMEOUT",
                    severity=RiskLevel.MEDIUM,
                    file_path=file_path,
                    resource_type="system",
                    resource_name="tfsec",
                    message="tfsec scan timed out after 60 seconds",
                )
            )
        except Exception as e:
            issues.append(
                SecurityIssue(
                    rule_id="SCAN_ERROR",
                    severity=RiskLevel.HIGH,
                    file_path=file_path,
                    resource_type="system",
                    resource_name="tfsec",
                    message=f"tfsec scan failed: {str(e)}",
                )
            )
        return issues

    def _parse_output(self, stdout: str, file_path: str) -> list[SecurityIssue]:
        issues = []
        try:
            data = json.loads(stdout)
            for result in data.get("results", {}).get("failures", []):
                severity_map = {
                    "CRITICAL": RiskLevel.CRITICAL,
                    "HIGH": RiskLevel.HIGH,
                    "MEDIUM": RiskLevel.MEDIUM,
                    "LOW": RiskLevel.LOW,
                }
                issues.append(
                    SecurityIssue(
                        rule_id=result.get("rule_id", "UNKNOWN"),
                        severity=severity_map.get(
                            result.get("severity", "MEDIUM"), RiskLevel.MEDIUM
                        ),
                        file_path=file_path,
                        resource_type=result.get("resource_type", "unknown"),
                        resource_name=result.get("resource_name", "unknown"),
                        message=result.get("description", "No description"),
                        line_number=result.get("location", {}).get("start_line"),
                        remediation=result.get("resolution"),
                    )
                )
        except json.JSONDecodeError:
            pass
        return issues

    def scan_directory(self, path: str) -> list[SecurityIssue]:
        issues = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".tf"):
                    file_path = os.path.join(root, file)
                    issues.extend(self.scan_file(file_path))
        return issues
