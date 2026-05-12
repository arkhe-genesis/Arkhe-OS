#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology/dashboard.py — Dashboard Streamlit para Análise de Sobrevivência
Dashboard interativo para visualização em tempo real de:
- Resultados de validação do modelo de Cox
- Plots Kaplan-Meier, forest, Schoenfeld interativos
- Métricas de cache e performance
- Histórico de análises com filtros temporais

Execução:
    streamlit run conrag/domains/sociology/dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import time
from typing import Optional, Dict, List
from pathlib import Path

# Imports do ConRAG
from conrag.domains.sociology.cox_validator import CoxModelValidator, CoxModelReport
from conrag.domains.sociology.visualizations import CanonicalPlot, CanonicalVisualizer

# Configuração da página
st.set_page_config(
    page_title="ARKHE Sociology Dashboard",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

@st.cache_data(ttl=3600)
def load_cached_analysis(report_path: str) -> Optional[Dict]:
    """Carrega relatório de análise do cache ou arquivo."""
    try:
        if report_path.endswith('.json'):
            with open(report_path, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar análise: {e}")
        return None

def plot_kaplan_meier_interactive(km_data: Dict) -> go.Figure:
    """Cria plot Kaplan-Meier interativo com Plotly."""
    fig = go.Figure()

    for curve in km_data.get('curves', []):
        fig.add_trace(go.Scatter(
            x=curve['times'],
            y=curve['survival'],
            mode='lines',
            name=curve['group'],
            fill='tozeroy',
            opacity=0.7,
            hovertemplate='<b>%{fullData.name}</b><br>Tempo: %{x:.1f}<br>Sobrevivência: %{y:.3f}<extra></extra>',
        ))

    fig.update_layout(
        title='Kaplan-Meier: Probabilidade de Sobrevivência até Adoção',
        xaxis_title='Tempo (anos)',
        yaxis_title='Probabilidade de Sobrevivência',
        hovermode='x unified',
        legend_title='Grupo',
        template='plotly_white',
    )

    return fig

def plot_forest_interactive(forest_data: Dict) -> go.Figure:
    """Cria forest plot interativo com Plotly."""
    effects = forest_data.get('effects', [])
    if not effects:
        return go.Figure().add_annotation(text="Nenhum dado para plot", showarrow=False)

    y_labels = [e['variable'] for e in effects]
    x_values = [e['hr'] for e in effects]
    x_lower = [e['ci_low'] for e in effects]
    x_upper = [e['ci_high'] for e in effects]
    significant = [e['significant'] for e in effects]

    colors = ['#2ca02c' if s else '#7f7f7f' for s in significant]

    fig = go.Figure()

    # Intervalos de confiança
    fig.add_trace(go.Scatter(
        x=x_lower + x_upper[::-1],
        y=y_labels + y_labels[::-1],
        fill='toself',
        fillcolor='rgba(0,100,80,0.15)',
        line_color='rgba(0,0,0,0)',
        showlegend=False,
        name='IC 95%',
    ))

    # Pontos de hazard ratio
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_labels,
        mode='markers+text',
        marker=dict(size=10, color=colors, line=dict(width=2, color='white')),
        text=[f"{hr:.2f}" for hr in x_values],
        textposition='top center',
        name='Hazard Ratio',
        hovertemplate='<b>%{y}</b><br>HR: %{x:.3f}<br>IC 95%: %{customdata[0]:.3f}–%{customdata[1]:.3f}<br>p: %{customdata[2]:.4f}<extra></extra>',
        customdata=[[l, u, e['p_value']] for e, l, u in zip(effects, x_lower, x_upper)],
    ))

    # Linha de referência HR=1
    fig.add_vline(x=1.0, line_dash='dash', line_color='red', annotation_text='HR=1.0 (sem efeito)')

    fig.update_layout(
        title='Forest Plot: Hazard Ratios e Intervalos de Confiança',
        xaxis_title='Hazard Ratio (escala log)',
        yaxis_title='Covariável',
        xaxis_type='log',
        hovermode='y unified',
        template='plotly_white',
        height=max(400, len(effects) * 40),
    )

    return fig

# ============================================================================
# SIDEBAR — CONTROLES
# ============================================================================

st.sidebar.title("🏛️ ARKHE Sociology")
st.sidebar.markdown("---")

# Seleção de política
policy_options = [
    "Planos Diretores Municipais",
    "Política de Transparência",
    "Programa Bolsa Família",
    "Lei de Acesso à Informação",
    "Personalizado...",
]
selected_policy = st.sidebar.selectbox("📋 Política para análise", policy_options)

if selected_policy == "Personalizado...":
    selected_policy = st.sidebar.text_input("Nome da política", "Minha Política")

# Fonte de dados
data_source = st.sidebar.radio("🗄️ Fonte de dados", ["IBGE", "OSF", "Híbrido", "Simulado"])

# Configurações do modelo
with st.sidebar.expander("⚙️ Configurações do Modelo", expanded=True):
    covariates = st.multiselect(
        "Covariáveis",
        ["pib_per_capita", "populacao", "regiao", "idh", "governanca", "educacao"],
        default=["pib_per_capita", "populacao"],
    )
    use_frailty = st.checkbox("✅ Usar frailty para dados agrupados", value=True)
    cluster_var = st.selectbox("Variável de agrupamento", ["uf", "regiao", "None"], index=2)
    cluster_var = None if cluster_var == "None" else cluster_var
    use_r = st.checkbox("🔄 Usar R para análise (coxme)", value=True)

# Botão de análise
if st.sidebar.button("🔍 Executar Análise", type="primary"):
    with st.spinner("Executando validação do modelo de Cox..."):
        # Instanciar validator com configurações
        validator = CoxModelValidator(
            use_frailty=use_frailty,
            generate_plots=True,
        )

        # Executar validação
        report = validator.validate_policy_diffusion(
            policy_name=selected_policy,
            covariates=covariates,
            data_source=data_source.lower(),
            cluster_var=cluster_var if use_frailty else None,
            use_r=use_r,
        )

        # Salvar relatório na sessão
        st.session_state['current_report'] = report
        st.session_state['report_timestamp'] = time.time()

        st.sidebar.success("✅ Análise concluída!")

# ============================================================================
# ÁREA PRINCIPAL — RESULTADOS
# ============================================================================

st.title(f"📊 Análise de Difusão: {selected_policy}")

# Verificar se há relatório na sessão
if 'current_report' not in st.session_state:
    st.info("👈 Selecione uma política e clique em 'Executar Análise' para começar.")
    st.markdown("""
    ### Funcionalidades do Dashboard:
    - 🔍 Validação automática dos 6 pressupostos do modelo de Cox
    - 📈 Plots interativos: Kaplan-Meier, Forest Plot, Schoenfeld residuals
    - 🗄️ Cache inteligente com Redis para consultas IBGE
    - 📄 Geração de relatórios PDF canônicos auditáveis
    - 🔄 Integração com R para frailty complexo (coxme)
    """)
    st.stop()

report = st.session_state['current_report']

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Observações", f"{report.n_observations:,}")
with col2:
    st.metric("✅ Eventos (Adoções)", f"{report.n_events:,}")
with col3:
    st.metric("⏸️ Censurados", f"{report.n_censored:,}")
with col4:
    status_icon = "✅" if report.overall_valid else "❌"
    st.metric("🎯 Modelo", f"{status_icon} {'VÁLIDO' if report.overall_valid else 'INVÁLIDO'}")

# Abas para diferentes visualizações
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Resumo",
    "📈 Plots",
    "📊 Coeficientes",
    "🔍 Pressupostos",
    "⚡ Performance",
])

with tab1:
    st.subheader("📋 Resumo da Análise")

    # Informações básicas
    st.markdown(f"""
    - **Política**: {report.dataset_name}
    - **Fonte de dados**: {report.data_source}
    - **Covariáveis**: {', '.join(report.covariates)}
    - **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}
    - **Selo canônico**: `{report.canonical_seal[:32]}...`
    """)

    # Resumo dos pressupostos
    st.markdown("#### Validação dos Pressupostos")
    for assumption, result in report.results.items():
        if hasattr(result, 'passed') and hasattr(result, 'severity') and hasattr(result, 'message'):
            icon = "✅" if result.passed else ("⚠️" if result.severity == "warning" else "❌")
            st.markdown(f"{icon} **{getattr(assumption, 'value', assumption)}**: {result.message}")
            if hasattr(result, 'recommendation') and result.recommendation:
                st.markdown(f"   > 💡 {result.recommendation}")
        elif isinstance(result, dict):
            icon = "✅" if result.get('passed', True) else ("⚠️" if result.get('severity') == "warning" else "❌")
            st.markdown(f"{icon} **{assumption}**: {result.get('message', '')}")

    # Botão para gerar PDF
    if st.button("📄 Gerar Relatório PDF", type="secondary"):
        with st.spinner("Gerando PDF canônico..."):
            pdf_path = report.generate_pdf_report()
            st.success(f"✅ Relatório gerado: `{Path(pdf_path).name}`")
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF",
                    data=f,
                    file_name=f"cox_report_{report.dataset_name}.pdf",
                    mime="application/pdf",
                )

with tab2:
    st.subheader("📈 Visualizações Interativas")

    # Plot Kaplan-Meier se disponível
    if any('kaplan_meier' in v for v in report.visualizations):
        km_viz = next((CanonicalPlot.from_json(v) for v in report.visualizations if 'kaplan_meier' in v), None)
        if km_viz:
            st.plotly_chart(plot_kaplan_meier_interactive(json.loads(km_viz.to_json())['data']), use_container_width=True)

    # Forest plot se disponível
    if any('forest' in v for v in report.visualizations):
        forest_viz = next((CanonicalPlot.from_json(v) for v in report.visualizations if 'forest' in v), None)
        if forest_viz:
            st.plotly_chart(plot_forest_interactive(json.loads(forest_viz.to_json())['data']), use_container_width=True)

    # Schoenfeld residuals se disponível
    if any('schoenfeld' in v for v in report.visualizations):
        schoenfeld_viz = next((CanonicalPlot.from_json(v) for v in report.visualizations if 'schoenfeld' in v), None)
        if schoenfeld_viz:
            st.info("📊 Gráfico de resíduos de Schoenfeld para teste de proporcionalidade")
            st.json(json.loads(schoenfeld_viz.to_json())['data'])

with tab3:
    st.subheader("📊 Coeficientes do Modelo")

    if 'cox_results' in report.results and 'fixed_effects' in report.results['cox_results']:
        coefs = report.results['cox_results']['fixed_effects']
        df_coefs = pd.DataFrame([
            {
                'Variável': var,
                'Coeficiente (β)': f"{vals['coef']:.4f}" if vals.get('coef') else 'N/A',
                'Hazard Ratio (HR)': f"{vals['hr']:.3f}" if vals.get('hr') else 'N/A',
                'IC 95% (HR)': f"{vals['ci_low']:.3f}–{vals['ci_high']:.3f}" if vals.get('ci_low') and vals.get('ci_high') else 'N/A',
                'p-valor': f"{vals['p']:.4f}" if vals.get('p') else 'N/A',
                'Significativo (α=0.05)': '✅ Sim' if vals.get('p', 1) < 0.05 else '❌ Não',
            }
            for var, vals in coefs.items()
        ])
        st.dataframe(df_coefs, use_container_width=True, hide_index=True)

        # Interpretação
        st.markdown("#### Interpretação dos Hazard Ratios")
        st.markdown("""
        - **HR > 1**: A covariável está associada a **maior risco** de adoção da política (adoção mais rápida)
        - **HR < 1**: A covariável está associada a **menor risco** de adoção (adoção mais lenta)
        - **HR = 1**: Sem efeito na taxa de adoção
        - **p < 0.05**: Efeito estatisticamente significativo
        """)
    else:
        st.info("Nenhum coeficiente disponível. Execute uma análise com resultados de Cox.")

with tab4:
    st.subheader("🔍 Detalhamento dos Pressupostos")

    for assumption, result in report.results.items():
        if hasattr(result, 'passed') and hasattr(result, 'severity'):
            with st.expander(f"{getattr(assumption, 'value', assumption)} — {'✅' if result.passed else '❌'} {result.message}", expanded=result.severity in ['error', 'critical']):
                st.markdown(f"**Severidade**: {result.severity.upper()}")
                st.markdown(f"**Mensagem**: {result.message}")
                if hasattr(result, 'p_value') and result.p_value is not None:
                    st.markdown(f"**p-valor**: `{result.p_value:.4f}`")
                if hasattr(result, 'statistic') and result.statistic is not None:
                    st.markdown(f"**Estatística**: `{result.statistic:.4f}`")
                if hasattr(result, 'recommendation') and result.recommendation:
                    st.markdown(f"> 💡 **Recomendação**: {result.recommendation}")
        elif isinstance(result, dict):
            with st.expander(f"{assumption} — {'✅' if result.get('passed', True) else '❌'} {result.get('message', '')}", expanded=result.get('severity') in ['error', 'critical']):
                if 'severity' in result: st.markdown(f"**Severidade**: {result['severity'].upper()}")
                if 'message' in result: st.markdown(f"**Mensagem**: {result['message']}")

with tab5:
    st.subheader("⚡ Métricas de Performance")

    if report.cache_stats:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🎯 Taxa de Acerto (Hit Rate)", f"{report.cache_stats.get('hit_rate', 0):.1%}")
            st.metric("💾 Consultas em Cache", f"{report.cache_stats.get('hits', 0):,}")
        with col2:
            st.metric("🌐 Consultas no IBGE", f"{report.cache_stats.get('misses', 0):,}")
            st.metric("⚠️ Erros", f"{report.cache_stats.get('errors', 0):,}")

        # Gráfico de barras simples
        if report.cache_stats.get('hits', 0) + report.cache_stats.get('misses', 0) > 0:
            cache_df = pd.DataFrame({
                'Tipo': ['Cache HIT', 'IBGE MISS'],
                'Contagem': [report.cache_stats.get('hits', 0), report.cache_stats.get('misses', 0)],
            })
            fig = px.bar(cache_df, x='Tipo', y='Contagem', color='Tipo', title='Distribuição de Consultas')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Estatísticas de cache não disponíveis para esta análise.")

# ============================================================================
# RODAPÉ — INFORMAÇÕES DE AUDITORIA
# ============================================================================

st.markdown("---")
st.markdown(f"""
<div style="text-align: center; font-size: 10pt; color: #666;">
    <strong>🔐 Auditoria Canônica ARKHE</strong><br>
    Hash do Relatório: <code>{report.canonical_seal}</code><br>
    Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(report.timestamp))}<br>
    Verificável em: <a href="https://arkhe-os.github.io/verify/{report.canonical_seal}" target="_blank">arkhe-os.github.io/verify</a>
</div>
""", unsafe_allow_html=True)
