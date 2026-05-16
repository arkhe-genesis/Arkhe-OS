import streamlit as st
from prometheus_client import REGISTRY

def render_dashboard():
    st.title("Arkhe OS Substrato 207 - Dashboard")
    st.subheader("Métricas Prometheus em Tempo Real")

    st.write("Visualização das métricas coletadas pelo Prometheus")

    federated_iocs = 0
    tickets = 0
    correlations = REGISTRY.get_sample_value('cross_org_correlations_total') or 0

    for metric in REGISTRY.collect():
        if metric.name == 'federated_iocs_total':
            federated_iocs = sum(sample.value for sample in metric.samples)
        elif metric.name == 'tickets_created_by_partner_total':
            tickets = sum(sample.value for sample in metric.samples)

    col1, col2, col3 = st.columns(3)
    col1.metric("IOCs Federados Ingeridos", federated_iocs)
    col2.metric("Correlações Cross-Org", correlations)
    col3.metric("Tickets Criados", tickets)

if __name__ == "__main__":
    render_dashboard()
