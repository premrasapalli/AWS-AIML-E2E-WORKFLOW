import subprocess
from typing import Optional
from ..models import PodLog


class LogCollector:
    def get_logs(
        self, namespace: str, pod_name: str, container: Optional[str] = None, tail_lines: int = 100
    ) -> list[PodLog]:
        logs = []
        containers = self._get_containers(namespace, pod_name)

        if container:
            containers = [c for c in containers if c == container] or containers[:1]

        for cont in containers:
            log_output = self._fetch_container_logs(namespace, pod_name, cont, tail_lines)
            logs.append(
                PodLog(
                    container=cont,
                    logs=log_output,
                    truncated=len(log_output.split("\n")) >= tail_lines,
                )
            )
        return logs

    def _get_containers(self, namespace: str, pod_name: str) -> list[str]:
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "pod", pod_name,
                    "-n", namespace,
                    "-o", "jsonpath={.spec.containers[*].name}",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split()
        except Exception:
            pass
        return ["container-0"]

    def _fetch_container_logs(
        self, namespace: str, pod_name: str, container: str, tail_lines: int
    ) -> str:
        try:
            result = subprocess.run(
                [
                    "kubectl", "logs", pod_name,
                    "-n", namespace,
                    "-c", container,
                    f"--tail={tail_lines}",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error fetching logs: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: kubectl logs command timed out"
        except Exception as e:
            return f"Error: {str(e)}"
