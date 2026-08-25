import subprocess
import json
from typing import Optional
from ..models import PodEvent


class EventCollector:
    def get_events(self, namespace: str, pod_name: str) -> list[PodEvent]:
        events = []
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "events",
                    "-n", namespace,
                    "--field-selector", f"involvedObject.name={pod_name}",
                    "-o", "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for item in data.get("items", []):
                    events.append(
                        PodEvent(
                            type=item.get("type", "Normal"),
                            reason=item.get("reason", "Unknown"),
                            message=item.get("message", ""),
                            age=self._calculate_age(item.get("lastTimestamp", "")),
                            field_path=item.get("involvedObject", {}).get("fieldPath"),
                        )
                    )
        except FileNotFoundError:
            events.append(
                PodEvent(
                    type="Warning",
                    reason="KubectlNotFound",
                    message="kubectl is not installed or not in PATH",
                    age="0s",
                )
            )
        except subprocess.TimeoutExpired:
            events.append(
                PodEvent(
                    type="Warning",
                    reason="Timeout",
                    message="kubectl command timed out",
                    age="0s",
                )
            )
        except Exception as e:
            events.append(
                PodEvent(
                    type="Warning",
                    reason="Error",
                    message=f"Failed to get events: {str(e)}",
                    age="0s",
                )
            )
        return events

    def _calculate_age(self, timestamp: str) -> str:
        if not timestamp:
            return "unknown"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            delta = datetime.now(dt.tzinfo) - dt
            seconds = int(delta.total_seconds())
            if seconds < 60:
                return f"{seconds}s"
            elif seconds < 3600:
                return f"{seconds // 60}m"
            elif seconds < 86400:
                return f"{seconds // 3600}h"
            else:
                return f"{seconds // 86400}d"
        except Exception:
            return "unknown"
