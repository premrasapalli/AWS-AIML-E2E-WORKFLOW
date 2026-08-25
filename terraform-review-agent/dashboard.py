import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import requests

st.set_page_config(page_title="AI Terraform Review Agent", page_icon="🔍", layout="wide")

st.title("🔍 AI Terraform Review Agent")
st.markdown("Automated Terraform code review with AI-powered security analysis")

col1, col2 = st.columns([2, 1])

with col1:
    repo_path = st.text_input("Repository Path", placeholder="/path/to/terraform/repo")
    model_alias = st.selectbox("AI Model", ["ollama", "ollama-llama3", "ollama-mistral", "ollama-qwen", "nova-lite", "nova-pro"])

with col2:
    st.markdown("### Quick Actions")
    if st.button("Run Full Review", type="primary"):
        if repo_path:
            with st.spinner("Analyzing Terraform code..."):
                try:
                    response = requests.post(
                        "http://localhost:8001/review",
                        json={
                            "repo_path": repo_path,
                            "model_alias": model_alias,
                        },
                        timeout=120,
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state["review_result"] = result
                    else:
                        st.error(f"API Error: {response.status_code}")
                except requests.ConnectionError:
                    st.error("Cannot connect to API. Start the server with: uvicorn app.main:app --port 8001")
        else:
            st.warning("Please enter a repository path")

if "review_result" in st.session_state:
    result = st.session_state["review_result"]

    tab1, tab2, tab3 = st.tabs(["📊 Resources", "🔒 Security", "🤖 AI Analysis"])

    with tab1:
        st.subheader("Terraform Resources")
        if result["changes"]:
            st.dataframe(result["changes"], use_container_width=True)
        else:
            st.info("No Terraform resources found")

    with tab2:
        st.subheader("Security Findings")
        if result["terrascan_results"]:
            for finding in result["terrascan_results"]:
                severity = finding["severity"]
                color = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}
                st.markdown(f"{color.get(severity, '⚪')} **{finding['rule_id']}** ({severity})")
                st.markdown(f"  {finding['message']}")
                if finding.get("remediation"):
                    st.markdown(f"  _Remediation: {finding['remediation']}_")
                st.divider()
        else:
            st.success("No security issues found!")

    with tab3:
        st.subheader("AI Analysis")
        analysis = result["ai_analysis"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Risk Score", f"{analysis['risk_score']}/100")
        col2.metric("Risk Level", analysis["risk_level"].upper())
        col3.metric("Model Used", result["model_used"])

        st.markdown("### Summary")
        st.markdown(analysis["summary"])

        if analysis["recommendations"]:
            st.markdown("### Recommendations")
            for rec in analysis["recommendations"]:
                st.markdown(f"- {rec}")

st.divider()
st.caption("Powered by AWS Bedrock (Amazon Titan) | Terrascan | FastAPI")
