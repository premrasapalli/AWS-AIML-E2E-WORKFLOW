import yaml
import os
from ..models import SecurityIssue, RiskLevel


class DockerScanner:
    UNSAFE_PRACTICES = {
        "privileged": {"severity": RiskLevel.CRITICAL, "message": "Container runs in privileged mode"},
        "host_network": {"severity": RiskLevel.HIGH, "message": "Container uses host network"},
        "host_pid": {"severity": RiskLevel.HIGH, "message": "Container shares host PID namespace"},
        "root_user": {"severity": RiskLevel.MEDIUM, "message": "Container runs as root"},
        "cap_add": {"severity": RiskLevel.MEDIUM, "message": "Container adds Linux capabilities"},
        "host_path": {"severity": RiskLevel.HIGH, "message": "Container mounts host filesystem path"},
        "no_read_only": {"severity": RiskLevel.LOW, "message": "Container filesystem is not read-only"},
    }

    def scan_file(self, file_path: str) -> list[SecurityIssue]:
        issues = []
        try:
            with open(file_path, "r") as f:
                compose = yaml.safe_load(f)
                if not compose or "services" not in compose:
                    return issues

                for service_name, service_config in compose["services"].items():
                    issues.extend(self._scan_service(service_name, service_config, file_path))
        except yaml.YAMLError as e:
            issues.append(
                SecurityIssue(
                    rule_id="YAML_PARSE_ERROR",
                    severity=RiskLevel.MEDIUM,
                    file_path=file_path,
                    resource_type="docker_compose",
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
                    resource_type="docker_compose",
                    resource_name="unknown",
                    message=f"Scan error: {str(e)}",
                )
            )
        return issues

    def _scan_service(self, service_name: str, config: dict, file_path: str) -> list[SecurityIssue]:
        issues = []

        if config.get("privileged"):
            issues.append(self._create_issue(
                "DOCKER_PRIVILEGED", service_name, file_path,
                self.UNSAFE_PRACTICES["privileged"],
                remediation="Remove 'privileged: true' from service",
            ))

        if config.get("network_mode") == "host":
            issues.append(self._create_issue(
                "DOCKER_HOST_NETWORK", service_name, file_path,
                self.UNSAFE_PRACTICES["host_network"],
                remediation="Remove 'network_mode: host'",
            ))

        if config.get("pid") == "host":
            issues.append(self._create_issue(
                "DOCKER_HOST_PID", service_name, file_path,
                self.UNSAFE_PRACTICES["host_pid"],
            ))

        user = config.get("user", "")
        if user in ["root", "0", ""]:
            issues.append(self._create_issue(
                "DOCKER_ROOT_USER", service_name, file_path,
                self.UNSAFE_PRACTICES["root_user"],
                remediation="Add 'user: non-root' to service",
            ))

        cap_add = config.get("cap_add", [])
        if cap_add:
            issues.append(self._create_issue(
                "DOCKER_CAP_ADD", service_name, file_path,
                self.UNSAFE_PRACTICES["cap_add"],
                remediation=f"Review added capabilities: {', '.join(cap_add)}",
            ))

        volumes = config.get("volumes", [])
        for volume in volumes:
            if isinstance(volume, str) and volume.startswith("/"):
                issues.append(self._create_issue(
                    "DOCKER_HOST_PATH", service_name, file_path,
                    self.UNSAFE_PRACTICES["host_path"],
                    remediation=f"Review volume mount: {volume}",
                ))

        if not config.get("read_only"):
            issues.append(self._create_issue(
                "DOCKER_WRITABLE_FS", service_name, file_path,
                self.UNSAFE_PRACTICES["no_read_only"],
                remediation="Add 'read_only: true' to service",
            ))

        return issues

    def _create_issue(self, rule_id: str, service_name: str, file_path: str, config: dict, remediation: str = None) -> SecurityIssue:
        return SecurityIssue(
            rule_id=rule_id,
            severity=config["severity"],
            file_path=file_path,
            resource_type="docker_service",
            resource_name=service_name,
            message=config["message"],
            remediation=remediation,
        )

    def scan_directory(self, path: str) -> list[SecurityIssue]:
        issues = []
        compose_files = ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]
        for root, _, files in os.walk(path):
            for file in files:
                if file in compose_files:
                    file_path = os.path.join(root, file)
                    issues.extend(self.scan_file(file_path))
        return issues
