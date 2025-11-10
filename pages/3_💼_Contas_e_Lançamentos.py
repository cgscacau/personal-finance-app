# pages/3_💳_Contas_e_Lançamentos.py
import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import supa

st.set_page_config(page_title="Contas & Lançamentos", page_icon="💳", layout="wide")
st.title("💳 Contas & Lançamentos")
require_login()
uid = current_user_id()

# =========================================================
# Utils
# =========================================================
def load_accounts(uid: str):
    res = supa().table("accounts").select("*").eq("user_id", uid).order("created_at").execute()
    return res.data or []

def load_categories(uid: str):
    """Retorna (cat_names, sub_by_cat={cat:[subs...]}) para o usuário."""
    try:
        res = supa().table("categories").select("name,parent_name,kind").eq("user_id", uid).order("name").execute()
        cats = res.data or []
    except Exception:
        cats = []
    cat_names = sorted({(c.get("name") or "").strip() for c in cats if c.get("name")})
    sub_by_cat: dict[str, list[str]] = {}
    for c in cats:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        sub = (c.get("parent_name") or "").strip()
        sub_by_cat.setdefault(name, [])
        if sub:
            sub_by_cat[name].append(sub)
    for k in list(sub_by_cat.keys()):
        sub_by_cat[k] = sorted(set(sub_by_cat[k]))
    return cat_names, sub_by_cat

def load_transactions(uid: str, account_id: str | None = None):
    q = supa().table("transactions").select("*").eq("user_id", uid)
    if account_id:
        q = q.eq("account_id", account_id)
    res = q.order("date", desc=True).execute()
    return res.data or []

# =========================================================
# Seleção de Conta
# =========================================================
accounts = load_accounts(uid)
if not accounts:
    st.warning("Você ainda não tem contas. Crie uma em **Importar & Higienizar → ➕ Criar nova conta**.")
    st.stop()

name_to_id = {a["name"]: a["id"] for a in accounts}
account_name = st.selectbox("Conta", list(name_to_id.keys()))
aid = name_to_id.get(account_name)

# =========================================================
# Catálogo de categorias (cadastro rápido)
# =========================================================
with st.expander("➕ Cadastrar categorias/subcategorias"):
    st.caption("Mantenha um catálogo próprio para facilitar o lançamento e relatórios.")
    colc1, colc2, colc3 = st.columns([2,2,1])
    with colc1:
        new_cat = st.text_input("Categoria", placeholder="Ex.: Alimentação")
    with colc2:
        new_sub = st.text_input("Subcategoria (opcional)", placeholder="Ex.: Delivery")
    with colc3:
        kind = st.selectbox("Tipo", ["both", "expense", "income"])
    if st.button("Adicionar categoria"):
        if not new_cat:
            st.warning("Informe ao menos a categoria.")
        else:
            try:
                supa().table("categories").insert({
                    "user_id": uid,
                    "name": new_cat.strip(),
                    "parent_name": (new_sub.strip() or None),
                    "kind": kind
                }).execute()
                st.success("Categoria registrada!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao cadastrar categoria: {e}")

# Carrega catálogo
cat_names, sub_by_cat = load_categories(uid)

# Estado global para seleção (sem callbacks em form)
if "cat_selected" not in st.session_state:
    st.session_state.cat_selected = None
if "sub_selected" not in st.session_state:
    st.session_state.sub_selected = None

# =========================================================
# Formulário de novo lançamento
# =========================================================
st.subheader("📝 Novo lançamento")

with st.form("novo_lancamento", clear_on_submit=True):
    c1, c2 = st.columns([1,3])
    with c1:
        date = st.date_input("Data")
    with c2:
        description = st.text_input("Descrição", placeholder="Ex.: Almoço, Uber, Pagamento de conta...")

    c3, c4 = st.columns([1,2])
    with c3:
        amount = st.number_input("Valor (negativo = despesa, positivo = receita)", step=0.01, format="%.2f")
    with c4:
        use_catalog = st.toggle("Usar catálogo de categorias", value=bool(cat_names))

        if use_catalog and cat_names:
            # Categoria (sem on_change; controlamos via session_state)
            options_cat = cat_names + ["(digitar manualmente)"]
            idx_cat = options_cat.index(st.session_state.cat_selected) if st.session_state.cat_selected in options_cat else 0
            category = st.selectbox("Categoria", options_cat, index=idx_cat, key="category_select")

            # Detecta mudança de categoria e reseta subcategoria
            if category != st.session_state.cat_selected:
                st.session_state.cat_selected = category
                st.session_state.sub_selected = None
                # também zera key dinâmica anterior se existir
                for k in list(st.session_state.keys()):
                    if k.startswith("subcategory_select__"):
                        st.session_state.pop(k)

            if category == "(digitar manualmente)":
                category = st.text_input("Categoria (manual)")
                subcategory = st.text_input("Subcategoria (manual)")
            else:
                # Subcategorias válidas dessa categoria
                subs = sorted({s for s in sub_by_cat.get(category, []) if s})
                if not subs:
                    subs = ["—"]

                # 🔑 key dinâmica dependente da categoria para recriar o widget
                sub_key = f"subcategory_select__{category}"

                # índice padrão coerente com estado salvo
                default_idx = subs.index(st.session_state.sub_selected) if st.session_state.sub_selected in subs else 0

                subcategory = st.selectbox("Subcategoria", subs, index=default_idx, key=sub_key)
                st.session_state.sub_selected = subcategory
                if subcategory == "—":
                    subcategory = None
        else:
            category = st.text_input("Categoria (manual)")
            subcategory = st.text_input("Subcategoria (manual)")

    tags = st.text_input("Tags (opcional, separadas por vírgula)", placeholder="ex.: nubank, ifood")

    submitted = st.form_submit_button("Adicionar")
    if submitted:
        if not description or amount is None:
            st.warning("Preencha ao menos **descrição** e **valor**.")
        else:
            try:
                payload = {
                    "user_id": uid,
                    "account_id": aid,
                    "date": str(date),
                    "description": description.strip(),
                    "amount": float(amount),
                    "category": (category.strip() if category else None) or None,
                    "subcategory": (subcategory.strip() if subcategory else None) or None,
                    "tags": None if not tags else [t.strip() for t in tags.split(",") if t.strip()],
                    "source_file": "manual",
                }
                supa().table("transactions").insert(payload).execute()
                st.success("Lançamento inserido com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao inserir lançamento: {e}")

# =========================================================
# Listagem de lançamentos
# =========================================================
st.subheader("📜 Lançamentos registrados")

data = load_transactions(uid, aid)
df = pd.DataFrame(data)

if df.empty:
    st.info("Nenhum lançamento encontrado para esta conta.")
else:
    view_cols = ["date", "description", "amount", "category", "subcategory", "tags"]
    for col in view_cols:
        if col not in df.columns:
            df[col] = None
    st.dataframe(df[view_cols], use_container_width=True, height=460)

    # Exclusão
    with st.expander("🗑 Excluir lançamento"):
        df_small = df[["id", "date", "description", "amount"]].copy()
        df_small["label"] = df_small.apply(
            lambda r: f'{str(r["id"])[:8]}... | {r["date"]} | {str(r["description"])[:30]} | R$ {float(r["amount"]):.2f}',
            axis=1
        )
        to_delete_label = st.selectbox("Selecione o lançamento", df_small["label"])
        if st.button("Excluir lançamento"):
            try:
                row = df_small[df_small["label"] == to_delete_label].iloc[0]
                supa().table("transactions").delete().eq("id", row["id"]).execute()
                st.success("Lançamento excluído.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
