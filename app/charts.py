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
    """
    Treemap robusto:
    - Garante colunas category/subcategory
    - Converte despesas (amount<0) em valores positivos para o gráfico
    - Trata NaN / ausência total de categorias
    - Evita ValueError do plotly quando não há folhas válidas
    """
    d = df.copy()

    # garante colunas
    if "category" not in d.columns:
        d["category"] = None
    if "subcategory" not in d.columns:
        d["subcategory"] = None

    # apenas despesas (amount negativo) -> valor positivo
    d["value"] = (-d["amount"]).astype(float)
    d = d[d["value"] > 0]

    if d.empty:
        # volta um gráfico “placeholder” informativo
        fig = px.scatter(title="Sem dados de despesa para o período")
        return fig

    # preenche NaN com rótulos padrão
    d["category"] = d["category"].fillna("Sem categoria")
    d["subcategory"] = d["subcategory"].fillna("Outros")

    # agrega (evita duplicatas e linhas com mesmo path)
    g = (
        d.groupby(["category", "subcategory"], dropna=False)["value"]
        .sum()
        .reset_index()
    )

    # se depois da agregação ainda ficar vazio (hipótese rara), devolve placeholder
    if g.empty or g["value"].le(0).all():
        fig = px.scatter(title="Sem dados suficientes para o treemap")
        return fig

    # agora sim o treemap tem hierarquia válida
    fig = px.treemap(
        g,
        path=["category", "subcategory"],
        values="value",
        title="Distribuição de Despesas"
    )
    return fig
