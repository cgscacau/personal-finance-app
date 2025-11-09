import pandas as pd
import plotly.express as px

def by_category_bar(df: pd.DataFrame, period_label: str = ""):
    d = df.copy()
    d["value"] = -d["amount"]  # despesas negativas -> barras positivas
    d = d[d["value"]>0]
    g = d.groupby("category", dropna=False)["value"].sum().sort_values(ascending=False).reset_index()
    fig = px.bar(g, x="category", y="value", title=f"Despesas por Categoria {period_label}")
    fig.update_layout(xaxis_title=None, yaxis_title="R$"); return fig

def cashflow_line(df: pd.DataFrame):
    d = df.copy()
    d["month"] = pd.to_datetime(d["date"]).dt.to_period("M").dt.to_timestamp()
    g = d.groupby("month")["amount"].sum().cumsum().reset_index()
    fig = px.line(g, x="month", y="amount", title="Evolução do Saldo Acumulado")
    fig.update_layout(xaxis_title=None, yaxis_title="R$"); return fig

def category_treemap(df: pd.DataFrame):
    d = df.copy()
    d["value"] = -d["amount"]
    d = d[d["value"]>0]
    if d.empty: return px.scatter(title="Sem dados de despesa")
    fig = px.treemap(d, path=["category","subcategory"], values="value", title="Distribuição de Despesas")
    return fig
