import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import requests

st.set_page_config(page_title="AI Infrastructure Auditor", page_icon="🛡️", layout="wide")

st.title("🛡️ AI Infrastructure Auditor")
st.markdown("DevSecOps platform for scanning Kubernetes, Docker, and Terraform configurations")

col1, col2 = st.columns([2, 1])

with col1:
    scan_path = st.text_input("Path to Scan", placeholder="/path/to/infrastructure/code")
    scan_type = st.selectbox("Scan Type", ["all", "kubernetes", "docker_compose", "terraform"])
    model_alias = st.selectbox("AI Model", ["ollama", "ollama-llama3", "ollama-mistral", "ollama-qwen", "nova-lite", "nova-pro"])

with col2:
    include_ai = st.checkbox("Include AI Explanations", value=True)
    if st.button("Run Security Audit", type="primary"):
        if scan_path:
            with st.spinner("Scanning infrastructure..."):
                try:
                    response = requests.post(
                        "http://localhost:8002/audit",
                        json={
                            "path": scan_path,
                            "file_type": scan_type if scan_type != "all" else None,
                            "model_alias": model_alias,
                            "include_ai_explanations": include_ai,
                        },
                        timeout=180,
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state["audit_result"] = result
                    else:
                        st.error(f"API Error: {response.status_code}")
                except requests.ConnectionError:
                    st.error("Cannot connect to API. Start the server with: uvicorn app.main:app --port 8002")
        else:
            st.warning("Please enter a path to scan")

if "audit_result" in st.session_state:
    result = st.session_state["audit_result"]

    st.subheader("Scan Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Issues", result["summary"]["total_issues"])
    col2.metric("Critical", result["summary"]["critical"])
    col3.metric("High", result["summary"]["high"])
    col4.metric("Medium", result["summary"]["medium"])
    col5.metric("Low", result["summary"]["low"])

    tab1, tab2 = st.tabs(["🔍 Findings", "🤖 AI Explanations"])

    with tab1:
        for res in result["results"]:
            st.markdown(f"### {res['file_type'].upper()} - {res['file_path']}")
            st.markdown(f"**Risk Score:** {res['risk_score']}/100 ({res['risk_level'].upper()})")

            if res["issues"]:
                for issue in res["issues"]:
                    severity = issue["severity"]
                    color = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}
                    st.markdown(f"{color.get(severity, '⚪')} **{issue['rule_id']}** ({severity})")
                    st.markdown(f"  {issue['message']}")
                    if issue.get("remediation"):
                        st.markdown(f"  _Fix: {issue['remediation']}_")
                    st.divider()
            else:
                st.success("No issues found in this category")

    with tab2:
        if result.get("ai_explanations"):
            for exp in result["ai_explanations"]:
                with st.expander(f"🤖 {exp['issue_id']}"):
                    st.markdown(f"**Explanation:** {exp['explanation']}")
                    st.markdown(f"**Impact:** {exp['impact']}")
                    st.markdown(f"**Fix:** {exp['fix_suggestion']}")
                    if exp.get("compliance_references"):
                        st.markdown(f"**Compliance:** {', '.join(exp['compliance_references'])}")
        else:
            st.info("Enable AI explanations to see detailed analysis")

st.divider()
st.caption("Powered by AWS Bedrock (Amazon Titan) | Terrascan | tfsec | FastAPI")
