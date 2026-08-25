import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import subprocess
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import DebugRequest, DebugResponse, PodPhase, ContainerStatus
from .collectors.log_collector import LogCollector
from .collectors.event_collector import EventCollector
from .ai.bedrock_diagnoser import BedrockDiagnoser

app = FastAPI(title="AI-Powered K8s Pod Debugger", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

log_collector = LogCollector()
event_collector = EventCollector()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "k8s-debugger"}


@app.post("/debug", response_model=DebugResponse)
async def debug_pod(request: DebugRequest):
    pod_name = request.pod_name
    if not pod_name and request.label_selector:
        pod_name = _get_pod_by_label(request.namespace, request.label_selector)
        if not pod_name:
            raise HTTPException(status_code=404, detail="No pod found matching label selector")

    if not pod_name:
        raise HTTPException(status_code=400, detail="Either pod_name or label_selector is required")

    pod_info = _get_pod_info(request.namespace, pod_name)
    if not pod_info:
        raise HTTPException(status_code=404, detail=f"Pod {pod_name} not found in namespace {request.namespace}")

    events = event_collector.get_events(request.namespace, pod_name)
    logs = log_collector.get_logs(request.namespace, pod_name, request.container, request.tail_lines)

    analysis = None
    if request.model_alias:
        try:
            diagnoser = BedrockDiagnoser(model_alias=request.model_alias)
            analysis = diagnoser.diagnose(
                pod_name=pod_name,
                namespace=request.namespace,
                phase=pod_info["phase"],
                container_statuses=pod_info["container_statuses"],
                events=events,
                logs=logs,
            )
        except Exception as e:
            pass

    return DebugResponse(
        namespace=request.namespace,
        pod_name=pod_name,
        phase=PodPhase(pod_info["phase"]),
        container_statuses=pod_info["container_statuses"],
        events=events,
        logs=logs,
        root_cause_analysis=analysis,
        model_used=request.model_alias,
    )


def _get_pod_by_label(namespace: str, label_selector: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [
                "kubectl", "get", "pods",
                "-n", namespace,
                "-l", label_selector,
                "-o", "jsonpath={.items[0].metadata.name}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _get_pod_info(namespace: str, pod_name: str) -> Optional[dict]:
    try:
        result = subprocess.run(
            [
                "kubectl", "get", "pod", pod_name,
                "-n", namespace,
                "-o", "json",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            status = data.get("status", {})
            container_statuses = []
            for cs in status.get("containerStatuses", []):
                state = cs.get("state", {})
                state_key = list(state.keys())[0] if state else "unknown"
                state_info = state.get(state_key, {})
                container_statuses.append(
                    ContainerStatus(
                        name=cs.get("name", "unknown"),
                        ready=cs.get("ready", False),
                        restart_count=cs.get("restartCount", 0),
                        image=cs.get("image", "unknown"),
                        state=state_key,
                        reason=state_info.get("reason"),
                        message=state_info.get("message"),
                    )
                )
            return {
                "phase": status.get("phase", "Unknown"),
                "container_statuses": container_statuses,
            }
    except Exception:
        pass
    return None


@app.get("/namespaces")
async def list_namespaces():
    try:
        result = subprocess.run(
            ["kubectl", "get", "namespaces", "-o", "jsonpath={.items[*].metadata.name}"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return {"namespaces": result.stdout.strip().split()}
    except Exception:
        pass
    return {"namespaces": [], "error": "Could not fetch namespaces"}


@app.get("/pods/{namespace}")
async def list_pods(namespace: str, label: Optional[str] = None):
    cmd = ["kubectl", "get", "pods", "-n", namespace, "-o", "json"]
    if label:
        cmd.extend(["-l", label])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            pods = []
            for item in data.get("items", []):
                pods.append({
                    "name": item["metadata"]["name"],
                    "phase": item["status"].get("phase", "Unknown"),
                    "restarts": sum(
                        cs.get("restartCount", 0)
                        for cs in item["status"].get("containerStatuses", [])
                    ),
                })
            return {"pods": pods}
    except Exception:
        pass
    return {"pods": [], "error": "Could not fetch pods"}
