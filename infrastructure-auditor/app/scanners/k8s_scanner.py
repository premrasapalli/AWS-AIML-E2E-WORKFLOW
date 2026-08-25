import yaml
import os
from ..models import SecurityIssue, RiskLevel


class K8sScanner:
    UNSAFE_CONFIGS = {
        "privileged": {"severity": RiskLevel.CRITICAL, "message": "Container running in privileged mode"},
        "hostNetwork": {"severity": RiskLevel.HIGH, "message": "Container uses host network namespace"},
        "hostPID": {"severity": RiskLevel.HIGH, "message": "Container uses host PID namespace"},
        "hostIPC": {"severity": RiskLevel.HIGH, "message": "Container uses host IPC namespace"},
        "runAsRoot": {"severity": RiskLevel.MEDIUM, "message": "Container runs as root user"},
        "allowPrivilegeEscalation": {"severity": RiskLevel.HIGH, "message": "Container allows privilege escalation"},
    }

    MISSING_SECURITY_CONTEXT = {
        "severity": RiskLevel.MEDIUM,
        "message": "No securityContext defined for container",
    }

    MISSING_RESOURCE_LIMITS = {
        "severity": RiskLevel.LOW,
        "message": "No resource limits defined for container",
    }

    def scan_file(self, file_path: str) -> list[SecurityIssue]:
        issues = []
        try:
            with open(file_path, "r") as f:
                docs = list(yaml.safe_load_all(f))
                for doc in docs:
                    if doc and doc.get("kind") in ["Deployment", "StatefulSet", "DaemonSet", "Pod"]:
                        issues.extend(self._scan_workload(doc, file_path))
        except yaml.YAMLError as e:
            issues.append(
                SecurityIssue(
                    rule_id="YAML_PARSE_ERROR",
                    severity=RiskLevel.MEDIUM,
                    file_path=file_path,
                    resource_type="unknown",
                    resource_name="unknown",
                    message=f"YAML parse error: {str(e)}",
                )
            )
        except Exception as e:
            issues.append(
                SecurityIssue(
                    rule_id="SCAN_ERROR",
                    severity=RiskLevel.HIGH,
                    file_path=file_path,
                    resource_type="unknown",
                    resource_name="unknown",
                    message=f"Scan error: {str(e)}",
                )
            )
        return issues

    def _scan_workload(self, doc: dict, file_path: str) -> list[SecurityIssue]:
        issues = []
        kind = doc.get("kind", "Unknown")
        name = doc.get("metadata", {}).get("name", "unknown")

        spec = doc.get("spec", {})
        if kind == "Pod":
            containers = spec.get("containers", []) + spec.get("initContainers", [])
        else:
            pod_spec = spec.get("template", {}).get("spec", {})
            containers = pod_spec.get("containers", []) + pod_spec.get("initContainers", [])

        for container in containers:
            container_name = container.get("name", "unknown")
            security_context = container.get("securityContext", {})

            if not security_context:
                issues.append(
                    SecurityIssue(
                        rule_id="K8S_NO_SECURITY_CONTEXT",
                        severity=self.MISSING_SECURITY_CONTEXT["severity"],
                        file_path=file_path,
                        resource_type=f"{kind}/{container_name}",
                        resource_name=name,
                        message=self.MISSING_SECURITY_CONTEXT["message"],
                    )
                )

            if security_context.get("privileged"):
                issues.append(
                    SecurityIssue(
                        rule_id="K8S_PRIVILEGED_CONTAINER",
                        severity=self.UNSAFE_CONFIGS["privileged"]["severity"],
                        file_path=file_path,
                        resource_type=f"{kind}/{container_name}",
                        resource_name=name,
                        message=self.UNSAFE_CONFIGS["privileged"]["message"],
                        remediation="Remove 'privileged: true' from securityContext",
                    )
                )

            if security_context.get("allowPrivilegeEscalation"):
                issues.append(
                    SecurityIssue(
                        rule_id="K8S_PRIVILEGE_ESCALATION",
                        severity=self.UNSAFE_CONFIGS["allowPrivilegeEscalation"]["severity"],
                        file_path=file_path,
                        resource_type=f"{kind}/{container_name}",
                        resource_name=name,
                        message=self.UNSAFE_CONFIGS["allowPrivilegeEscalation"]["message"],
                        remediation="Set 'allowPrivilegeEscalation: false' in securityContext",
                    )
                )

            resources = container.get("resources", {})
            if not resources.get("limits"):
                issues.append(
                    SecurityIssue(
                        rule_id="K8S_NO_RESOURCE_LIMITS",
                        severity=self.MISSING_RESOURCE_LIMITS["severity"],
                        file_path=file_path,
                        resource_type=f"{kind}/{container_name}",
                        resource_name=name,
                        message=self.MISSING_RESOURCE_LIMITS["message"],
                        remediation="Add resource limits to prevent resource exhaustion",
                    )
                )

        pod_security_context = spec.get("securityContext") or (
            spec.get("template", {}).get("spec", {}).get("securityContext", {})
        )
        if pod_security_context:
            if pod_security_context.get("hostNetwork"):
                issues.append(
                    SecurityIssue(
                        rule_id="K8S_HOST_NETWORK",
                        severity=self.UNSAFE_CONFIGS["hostNetwork"]["severity"],
                        file_path=file_path,
                        resource_type=kind,
                        resource_name=name,
                        message=self.UNSAFE_CONFIGS["hostNetwork"]["message"],
                        remediation="Remove 'hostNetwork: true' from pod spec",
                    )
                )
            if pod_security_context.get("hostPID"):
                issues.append(
                    SecurityIssue(
                        rule_id="K8S_HOST_PID",
                        severity=self.UNSAFE_CONFIGS["hostPID"]["severity"],
                        file_path=file_path,
                        resource_type=kind,
                        resource_name=name,
                        message=self.UNSAFE_CONFIGS["hostPID"]["message"],
                    )
                )

        return issues

    def scan_directory(self, path: str) -> list[SecurityIssue]:
        issues = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    file_path = os.path.join(root, file)
                    issues.extend(self.scan_file(file_path))
        return issues
