import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.bedrock_client import BedrockClient
from ..models import PodEvent, PodLog, ContainerStatus, RootCauseAnalysis


class BedrockDiagnoser:
    def __init__(self, model_alias: str = "ollama"):
        self.client = BedrockClient(model_alias=model_alias)

    def diagnose(
        self,
        pod_name: str,
        namespace: str,
        phase: str,
        container_statuses: list[ContainerStatus],
        events: list[PodEvent],
        logs: list[PodLog],
    ) -> RootCauseAnalysis:
        prompt = self._build_diagnosis_prompt(
            pod_name, namespace, phase, container_statuses, events, logs
        )
        system_prompt = self._get_system_prompt()

        response = self.client.invoke(prompt, system_prompt=system_prompt)
        return self._parse_response(response, events)

    def _get_system_prompt(self) -> str:
        return """You are an expert Kubernetes troubleshooter analyzing a failing pod.
Based on the provided pod status, events, and logs, identify:
1. The root cause of the failure
2. A category for the issue (e.g., CrashLoopBackOff, ImagePullError, ResourceLimit, etc.)
3. Your confidence level (0-100)
4. A clear explanation of what's happening
5. Specific steps to fix the issue
6. Which events are most relevant to the failure

Format your response as JSON:
{
  "root_cause": "string",
  "category": "string",
  "confidence": number,
  "explanation": "string",
  "suggested_fixes": ["string"],
  "related_events": ["string"]
}"""

    def _build_diagnosis_prompt(
        self,
        pod_name: str,
        namespace: str,
        phase: str,
        container_statuses: list[ContainerStatus],
        events: list[PodEvent],
        logs: list[PodLog],
    ) -> str:
        status_text = ""
        for cs in container_statuses:
            status_text += f"- Container {cs.name}: ready={cs.ready}, restarts={cs.restart_count}, state={cs.state or 'unknown'}\n"
            if cs.reason:
                status_text += f"  Reason: {cs.reason}\n"
            if cs.message:
                status_text += f"  Message: {cs.message[:200]}\n"

        events_text = ""
        for e in events[-10:]:
            events_text += f"- [{e.type}] {e.reason}: {e.message[:150]}\n"

        logs_text = ""
        for log_entry in logs[:3]:
            log_lines = log_entry.logs.strip().split("\n")[-20:]
            logs_text += f"\nContainer {log_entry.container} logs (last 20 lines):\n"
            logs_text += "\n".join(log_lines) + "\n"

        return f"""Analyze this failing Kubernetes pod:

Pod: {pod_name}
Namespace: {namespace}
Phase: {phase}

Container Statuses:
{status_text}

Recent Events:
{events_text}

Logs:
{logs_text}

Identify the root cause and provide your diagnosis as JSON."""

    def _parse_response(self, response: str, events: list[PodEvent]) -> RootCauseAnalysis:
        import json
        import re

        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return RootCauseAnalysis(
                    root_cause=data.get("root_cause", "Unknown root cause"),
                    category=data.get("category", "Unknown"),
                    confidence=min(100, max(0, data.get("confidence", 50))),
                    explanation=data.get("explanation", "Unable to determine root cause"),
                    suggested_fixes=data.get("suggested_fixes", ["Review pod configuration"]),
                    related_events=data.get("related_events", []),
                )
        except (json.JSONDecodeError, ValueError):
            pass

        return RootCauseAnalysis(
            root_cause="Unable to determine root cause from AI analysis",
            category="Unknown",
            confidence=0,
            explanation=response[:500] if response else "No analysis available",
            suggested_fixes=["Check pod logs manually", "Review recent events"],
            related_events=[e.reason for e in events[:5]],
        )
