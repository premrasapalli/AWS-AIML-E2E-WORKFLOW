import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import requests

st.set_page_config(page_title="AI K8s Pod Debugger", page_icon="🐛", layout="wide")

st.title("🐛 AI-Powered K8s Pod Debugger")
st.markdown("Automatically diagnose failing Kubernetes pods with AI-powered root cause analysis")

col1, col2 = st.columns([2, 1])

with col1:
    namespace = st.text_input("Namespace", placeholder="default")
    pod_name = st.text_input("Pod Name", placeholder="my-failing-pod")
    label_selector = st.text_input("Or Label Selector", placeholder="app=nginx")
    container = st.text_input("Container (optional)", placeholder="")
    tail_lines = st.slider("Log Lines to Fetch", 50, 500, 100)

with col2:
    model_alias = st.selectbox("AI Model", ["titan-express", "titan-lite", "titan-premier"])
    if st.button("Debug Pod", type="primary"):
        if namespace and (pod_name or label_selector):
            with st.spinner("Fetching pod data and running AI diagnosis..."):
                try:
                    response = requests.post(
                        "http://localhost:8003/debug",
                        json={
                            "namespace": namespace,
                            "pod_name": pod_name or None,
                            "label_selector": label_selector or None,
                            "container": container or None,
                            "tail_lines": tail_lines,
                            "model_alias": model_alias,
                        },
                        timeout=120,
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state["debug_result"] = result
                    else:
                        st.error(f"API Error: {response.status_code} - {response.text}")
                except requests.ConnectionError:
                    st.error("Cannot connect to API. Start the server with: uvicorn app.main:app --port 8003")
        else:
            st.warning("Please enter namespace and pod name or label selector")

if "debug_result" in st.session_state:
    result = st.session_state["debug_result"]

    st.subheader(f"Pod: {result['pod_name']} ({result['phase']})")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Events", "📝 Logs", "🤖 AI Diagnosis", "🔍 Details"])

    with tab1:
        st.markdown("### Pod Events")
        if result["events"]:
            for event in result["events"]:
                icon = "🔴" if event["type"] == "Warning" else "🟢"
                st.markdown(f"{icon} **{event['reason']}** ({event['age']})")
                st.markdown(f"  {event['message']}")
                st.divider()
        else:
            st.info("No events found")

    with tab2:
        st.markdown("### Container Logs")
        for log in result["logs"]:
            with st.expander(f"Container: {log['container']}", expanded=True):
                st.code(log["logs"][-3000:] if len(log["logs"]) > 3000 else log["logs"], language=None)
                if log["truncated"]:
                    st.warning("Logs were truncated. Increase tail lines for more output.")

    with tab3:
        st.markdown("### AI Root Cause Analysis")
        if result.get("root_cause_analysis"):
            analysis = result["root_cause_analysis"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Confidence", f"{analysis['confidence']}%")
            col2.metric("Category", analysis["category"])
            col3.metric("Model", result["model_used"])

            st.markdown("#### Root Cause")
            st.markdown(analysis["root_cause"])

            st.markdown("#### Explanation")
            st.markdown(analysis["explanation"])

            st.markdown("#### Suggested Fixes")
            for fix in analysis["suggested_fixes"]:
                st.markdown(f"- {fix}")

            if analysis.get("related_events"):
                st.markdown("#### Related Events")
                for event in analysis["related_events"]:
                    st.markdown(f"- {event}")
        else:
            st.info("No AI analysis available")

    with tab4:
        st.markdown("### Container Statuses")
        if result["container_statuses"]:
            for cs in result["container_statuses"]:
                status_icon = "✅" if cs["ready"] else "❌"
                st.markdown(f"{status_icon} **{cs['name']}** - Restarts: {cs['restart_count']}")
                st.markdown(f"  Image: {cs['image']}")
                if cs.get("state"):
                    st.markdown(f"  State: {cs['state']}")
                if cs.get("reason"):
                    st.markdown(f"  Reason: {cs['reason']}")
                st.divider()

st.divider()
st.caption("Powered by AWS Bedrock (Amazon Titan) | kubectl | FastAPI")
