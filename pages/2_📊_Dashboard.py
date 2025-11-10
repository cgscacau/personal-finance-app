# pages/1_📊_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from app.auth import require_login, current_user_id
from app.db import supa
from app.charts import by_category_bar, cashflow_line, category_treemap

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar a aparência
st.markdown("""
    <style>
    /* Métricas com cards mais bonitos */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 14px;
        font-weight: 500;
    }
    
    /* Melhorar aparência dos containers */
    .stExpander {
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 8px;
    }
    
    /* Títulos de seção */
    .section-title {
        font-size: 20px;
        font-weight: 600;
        margin-top: 30px;
        margin-bottom: 15px;
        color: #1f77b4;
    }
    
    /* Cards personalizados */
    .custom-card {
        background-color: rgba(28, 131, 225, 0.1);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Verifica autenticação
require_login()
uid = current_user_id()

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def load_transactions(uid: str):
    """Carrega todas as transações do usuário."""
    try:
        res = supa().table("transactions")\
            .select("*")\
            .eq("user_id", uid)\
            .execute()
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao carregar transações: {e}")
        return []


def load_accounts(uid: str):
    """Carrega todas as contas do usuário."""
    try:
        res = supa().table("accounts")\
            .select("*")\
            .eq("user_id", uid)\
            .execute()
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao carregar contas: {e}")
        return []


def filter_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """
    Filtra o DataFrame por período.
    
    Args:
        df: DataFrame com coluna 'date'
        period: String do período selecionado
        
    Returns:
        DataFrame filtrado
    """
    if df.empty:
        return df
    
    today = pd.Timestamp.today(tz=None).normalize()
    
    if period == "Últimos 7 dias":
        return df[df["date"] >= (today - pd.Timedelta(days=7))]
    elif period == "Últimos 30 dias":
        return df[df["date"] >= (today - pd.Timedelta(days=30))]
    elif period == "Últimos 90 dias":
        return df[df["date"] >= (today - pd.Timedelta(days=90))]
    elif period == "Últimos 6 meses":
        return df[df["date"] >= (today - pd.Timedelta(days=180))]
    elif period == "Ano atual":
        return df[df["date"].dt.year == today.year]
    elif period == "Ano passado":
        return df[df["date"].dt.year == (today.year - 1)]
    else:  # "Tudo"
        return df


def calculate_metrics(df: pd.DataFrame):
    """
    Calcula métricas financeiras do DataFrame.
    
    Returns:
        Dicionário com métricas calculadas
    """
    if df.empty:
        return {
            "receitas": 0,
            "despesas": 0,
            "saldo": 0,
            "num_lancamentos": 0,
            "ticket_medio_receita": 0,
            "ticket_medio_despesa": 0,
            "maior_receita": 0,
            "maior_despesa": 0
        }
    
    receitas = df[df["amount"] > 0]["amount"].sum()
    despesas = abs(df[df["amount"] < 0]["amount"].sum())
    saldo = df["amount"].sum()
    num_lancamentos = len(df)
    
    # Tickets médios
    receitas_list = df[df["amount"] > 0]["amount"]
    despesas_list = df[df["amount"] < 0]["amount"].abs()
    
    ticket_medio_receita = receitas_list.mean() if len(receitas_list) > 0 else 0
    ticket_medio_despesa = despesas_list.mean() if len(despesas_list) > 0 else 0
    
    # Maiores valores
    maior_receita = receitas_list.max() if len(receitas_list) > 0 else 0
    maior_despesa = despesas_list.max() if len(despesas_list) > 0 else 0
    
    return {
        "receitas": receitas,
        "despesas": despesas,
        "saldo": saldo,
        "num_lancamentos": num_lancamentos,
        "ticket_medio_receita": ticket_medio_receita,
        "ticket_medio_despesa": ticket_medio_despesa,
        "maior_receita": maior_receita,
        "maior_despesa": maior_despesa
    }


def create_gauge_chart(value: float, max_value: float, title: str, color: str):
    """Cria um gráfico de gauge (medidor)."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        number={'prefix': "R$ ", 'valueformat': ",.2f"},
        gauge={
            'axis': {'range': [None, max_value], 'tickformat': ",.0f"},
            'bar': {'color': color},
            'steps': [
                {'range': [0, max_value * 0.5], 'color': "rgba(0,255,0,0.1)"},
                {'range': [max_value * 0.5, max_value * 0.8], 'color': "rgba(255,255,0,0.1)"},
                {'range': [max_value * 0.8, max_value], 'color': "rgba(255,0,0,0.1)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig


def create_comparison_chart(df: pd.DataFrame):
    """Cria gráfico de comparação mensal."""
    if df.empty:
        return None
    
    df_monthly = df.copy()
    df_monthly['month'] = df_monthly['date'].dt.to_period('M').astype(str)
    
    monthly_summary = df_monthly.groupby('month').agg({
        'amount': lambda x: (x[x > 0].sum(), abs(x[x < 0].sum()))
    }).reset_index()
    
    monthly_summary[['receitas', 'despesas']] = pd.DataFrame(
        monthly_summary['amount'].tolist(), 
        index=monthly_summary.index
    )
    
    monthly_summary = monthly_summary.drop('amount', axis=1)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Receitas',
        x=monthly_summary['month'],
        y=monthly_summary['receitas'],
        marker_color='#2ecc71'
    ))
    
    fig.add_trace(go.Bar(
        name='Despesas',
        x=monthly_summary['month'],
        y=monthly_summary['despesas'],
        marker_color='#e74c3c'
    ))
    
    fig.update_layout(
        title='Comparação Mensal: Receitas vs Despesas',
        xaxis_title='Mês',
        yaxis_title='Valor (R$)',
        barmode='group',
        height=400,
        hovermode='x unified'
    )
    
    return fig


def create_top_categories_chart(df: pd.DataFrame, tipo: str = "despesas"):
    """Cria gráfico de top categorias."""
    if df.empty:
        return None
    
    if tipo == "despesas":
        df_filtered = df[df["amount"] < 0].copy()
        df_filtered["amount"] = df_filtered["amount"].abs()
        color = '#e74c3c'
        title = 'Top 10 Categorias de Despesas'
    else:
        df_filtered = df[df["amount"] > 0].copy()
        color = '#2ecc71'
        title = 'Top 10 Categorias de Receitas'
    
    # Remove registros sem categoria
    df_filtered = df_filtered[df_filtered["category"].notna()]
    
    if df_filtered.empty:
        return None
    
    top_categories = df_filtered.groupby("category")["amount"].sum()\
        .sort_values(ascending=False).head(10)
    
    fig = px.bar(
        x=top_categories.values,
        y=top_categories.index,
        orientation='h',
        title=title,
        labels={'x': 'Valor (R$)', 'y': 'Categoria'},
        color_discrete_sequence=[color]
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig


def create_daily_balance_chart(df: pd.DataFrame):
    """Cria gráfico de saldo diário acumulado."""
    if df.empty:
        return None
    
    df_sorted = df.sort_values('date').copy()
    df_sorted['saldo_acumulado'] = df_sorted['amount'].cumsum()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_sorted['date'],
        y=df_sorted['saldo_acumulado'],
        mode='lines',
        name='Saldo Acumulado',
        line=dict(color='#3498db', width=2),
        fill='tonexty',
        fillcolor='rgba(52, 152, 219, 0.2)'
    ))
    
    # Adiciona linha zero
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title='Evolução do Saldo',
        xaxis_title='Data',
        yaxis_title='Saldo Acumulado (R$)',
        height=400,
        hovermode='x unified'
    )
    
    return fig


# =========================================================
# HEADER
# =========================================================
st.title("📊 Dashboard Financeiro")
st.markdown("---")

# =========================================================
# FILTROS NO SIDEBAR
# =========================================================
with st.sidebar:
    st.header("⚙️ Filtros")
    
    # Seletor de período
    period = st.selectbox(
        "📅 Período",
        [
            "Últimos 7 dias",
            "Últimos 30 dias",
            "Últimos 90 dias",
            "Últimos 6 meses",
            "Ano atual",
            "Ano passado",
            "Tudo"
        ],
        index=1
    )
    
    # Carrega contas
    accounts = load_accounts(uid)
    
    if accounts:
        account_options = ["Todas as contas"] + [acc["name"] for acc in accounts]
        selected_account = st.selectbox(
            "🏦 Conta",
            account_options
        )
    else:
        selected_account = "Todas as contas"
    
    st.markdown("---")
    
    # Opções de visualização
    st.subheader("👁️ Visualização")
    show_details = st.checkbox("Mostrar detalhes", value=True)
    show_advanced = st.checkbox("Gráficos avançados", value=True)

# =========================================================
# CARREGAMENTO DE DADOS
# =========================================================
with st.spinner("Carregando dados..."):
    data = load_transactions(uid)
    df = pd.DataFrame(data)

# Verifica se há dados
if df.empty:
    st.info("📭 Sem lançamentos ainda. Importe ou adicione lançamentos nas outras abas.")
    st.stop()

# Processa dados
df["date"] = pd.to_datetime(df["date"])
df["amount"] = pd.to_numeric(df["amount"], errors='coerce')

# Filtra por conta se necessário
if selected_account != "Todas as contas":
    account_id = next((acc["id"] for acc in accounts if acc["name"] == selected_account), None)
    if account_id:
        df = df[df["account_id"] == account_id]

# Filtra por período
df_filtered = filter_by_period(df, period)

if df_filtered.empty:
    st.warning(f"⚠️ Nenhum lançamento encontrado no período selecionado: **{period}**")
    st.stop()

# Calcula métricas
metrics = calculate_metrics(df_filtered)

# =========================================================
# MÉTRICAS PRINCIPAIS
# =========================================================
st.subheader("💰 Visão Geral")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💵 Receitas",
        value=f"R$ {metrics['receitas']:,.2f}",
        delta=f"{len(df_filtered[df_filtered['amount'] > 0])} lançamentos",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="💸 Despesas",
        value=f"R$ {metrics['despesas']:,.2f}",
        delta=f"{len(df_filtered[df_filtered['amount'] < 0])} lançamentos",
        delta_color="inverse"
    )

with col3:
    saldo_color = "normal" if metrics['saldo'] >= 0 else "inverse"
    st.metric(
        label="📊 Saldo",
        value=f"R$ {metrics['saldo']:,.2f}",
        delta=f"{(metrics['saldo']/metrics['receitas']*100) if metrics['receitas'] > 0 else 0:.1f}% das receitas",
        delta_color=saldo_color
    )

with col4:
    st.metric(
        label="📝 Lançamentos",
        value=f"{metrics['num_lancamentos']:,}",
        delta=f"Período: {period}"
    )

st.markdown("---")

# =========================================================
# MÉTRICAS SECUNDÁRIAS (SE ATIVADO)
# =========================================================
if show_details:
    st.subheader("📈 Análise Detalhada")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🎯 Ticket Médio (Receitas)",
            value=f"R$ {metrics['ticket_medio_receita']:,.2f}"
        )
    
    with col2:
        st.metric(
            label="🎯 Ticket Médio (Despesas)",
            value=f"R$ {metrics['ticket_medio_despesa']:,.2f}"
        )
    
    with col3:
        st.metric(
            label="⬆️ Maior Receita",
            value=f"R$ {metrics['maior_receita']:,.2f}"
        )
    
    with col4:
        st.metric(
            label="⬇️ Maior Despesa",
            value=f"R$ {metrics['maior_despesa']:,.2f}"
        )
    
    st.markdown("---")

# =========================================================
# GRÁFICOS PRINCIPAIS
# =========================================================
st.subheader("📊 Análise Visual")

# Tabs para organizar gráficos
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral",
    "📈 Evolução",
    "🏷️ Categorias",
    "📋 Dados"
])

with tab1:
    # Gráfico de fluxo de caixa
    st.plotly_chart(
        cashflow_line(df_filtered),
        use_container_width=True,
        key="cashflow_main"
    )
    
    # Comparação mensal
    comparison_chart = create_comparison_chart(df_filtered)
    if comparison_chart:
        st.plotly_chart(
            comparison_chart,
            use_container_width=True,
            key="comparison_main"
        )

with tab2:
    # Saldo acumulado
    balance_chart = create_daily_balance_chart(df_filtered)
    if balance_chart:
        st.plotly_chart(
            balance_chart,
            use_container_width=True,
            key="balance_main"
        )
    
    # Gauges de controle
    if show_advanced and metrics['receitas'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            gauge_despesas = create_gauge_chart(
                metrics['despesas'],
                metrics['receitas'],
                "Despesas vs Receitas",
                "#e74c3c"
            )
            st.plotly_chart(gauge_despesas, use_container_width=True)
        
        with col2:
            taxa_economia = ((metrics['receitas'] - metrics['despesas']) / metrics['receitas'] * 100) if metrics['receitas'] > 0 else 0
            st.metric(
                "💎 Taxa de Economia",
                f"{taxa_economia:.1f}%",
                delta="Meta: 20%",
                delta_color="normal" if taxa_economia >= 20 else "inverse"
            )
            
            # Barra de progresso
            st.progress(min(taxa_economia / 100, 1.0))

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        # Top categorias de despesas
        top_despesas = create_top_categories_chart(df_filtered, "despesas")
        if top_despesas:
            st.plotly_chart(top_despesas, use_container_width=True)
        else:
            st.info("Nenhuma despesa categorizada encontrada.")
    
    with col2:
        # Top categorias de receitas
        top_receitas = create_top_categories_chart(df_filtered, "receitas")
        if top_receitas:
            st.plotly_chart(top_receitas, use_container_width=True)
        else:
            st.info("Nenhuma receita categorizada encontrada.")
    
    # Treemap de categorias
    st.plotly_chart(
        category_treemap(df_filtered),
        use_container_width=True,
        key="treemap_main"
    )
    
    # Gráfico de barras por categoria
    st.plotly_chart(
        by_category_bar(df_filtered),
        use_container_width=True,
        key="category_bar_main"
    )

with tab4:
    st.subheader("📋 Tabela de Lançamentos")
    
    # Filtros adicionais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.multiselect(
            "Tipo",
            ["Receitas", "Despesas"],
            default=["Receitas", "Despesas"]
        )
    
    with col2:
        categories = df_filtered["category"].dropna().unique().tolist()
        if categories:
            filter_category = st.multiselect(
                "Categoria",
                ["Todas"] + sorted(categories),
                default=["Todas"]
            )
        else:
            filter_category = ["Todas"]
    
    with col3:
        sort_by = st.selectbox(
            "Ordenar por",
            ["Data (recente)", "Data (antigo)", "Valor (maior)", "Valor (menor)"]
        )
    
    # Aplica filtros
    df_table = df_filtered.copy()
    
    if "Receitas" not in filter_type:
        df_table = df_table[df_table["amount"] < 0]
    if "Despesas" not in filter_type:
        df_table = df_table[df_table["amount"] > 0]
    
    if "Todas" not in filter_category:
        df_table = df_table[df_table["category"].isin(filter_category)]
    
    # Ordena
    if sort_by == "Data (recente)":
        df_table = df_table.sort_values("date", ascending=False)
    elif sort_by == "Data (antigo)":
        df_table = df_table.sort_values("date", ascending=True)
    elif sort_by == "Valor (maior)":
        df_table = df_table.sort_values("amount", ascending=False)
    else:
        df_table = df_table.sort_values("amount", ascending=True)
    
    # Seleciona colunas para exibir
    display_cols = ["date", "description", "amount", "category", "subcategory", "tags"]
    df_display = df_table[[col for col in display_cols if col in df_table.columns]].copy()
    
    # Formata valores
    if "amount" in df_display.columns:
        df_display["amount"] = df_display["amount"].apply(lambda x: f"R$ {x:,.2f}")
    
    # Exibe tabela
    st.dataframe(
        df_display,
        use_container_width=True,
        height=500,
        column_config={
            "date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "description": st.column_config.TextColumn("Descrição", width="large"),
            "amount": st.column_config.TextColumn("Valor"),
            "category": st.column_config.TextColumn("Categoria"),
            "subcategory": st.column_config.TextColumn("Subcategoria"),
            "tags": st.column_config.ListColumn("Tags")
        }
    )
    
    # Botão de download
    csv = df_table.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar dados (CSV)",
        data=csv,
        file_name=f"transacoes_{period.lower().replace(' ', '_')}.csv",
        mime="text/csv"
    )

# =========================================================
# RODAPÉ COM INFORMAÇÕES
# =========================================================
st.markdown("---")
st.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | 📊 Total de {len(df_filtered)} lançamentos no período")
