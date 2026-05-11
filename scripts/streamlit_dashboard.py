#!/usr/bin/env python3
"""
streamlit_dashboard.py
A basic Streamlit dashboard for real-time visualization of geometric evidence.
"""
import streamlit as st
import pandas as pd
import json
import os
import glob
from pathlib import Path

st.set_page_config(page_title="Arkhe OS v∞.327.3 - Geometric Evidence", layout="wide")
st.title("🔬 Arkhe OS v∞.327.3 - Living Interpretability Dashboard")

evidence_dir = Path("publish/interpretability")
if not evidence_dir.exists():
    st.warning("No evidence directory found. Run the pipeline first.")
    st.stop()

index_path = evidence_dir / "index.json"
if not index_path.exists():
    st.warning("No index.json found. Publish evidence using the pipeline.")
    st.stop()

with open(index_path) as f:
    index_data = json.load(f)

st.subheader("Published Evidences")

publications = index_data.get("publications", [])
if not publications:
    st.info("No publications recorded.")
    st.stop()

df = pd.DataFrame(publications)
st.dataframe(df)

latest_pub = publications[-1]
st.write(f"### Latest Evidence: Epoch {latest_pub['epoch']}")

latest_file = evidence_dir / latest_pub["filename"]
if latest_file.exists():
    with open(latest_file) as f:
        evidence = json.load(f)

    col1, col2 = st.columns(2)
    with col1:
        st.write("#### Parameters")
        st.json(evidence.get("parameters", {}))
    with col2:
        st.write("#### Geometric State")
        st.json(evidence.get("geometric_state", {}))

    st.write("#### ZK Proofs Generated")
    st.json(evidence.get("verifiable_proofs", []))
else:
    st.error(f"File {latest_file} missing.")
