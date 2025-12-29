import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import supa

st.title("🧠 Regras de Categorização")
require_login()
uid = current_user_id()

# --- Botão para popular categorias padrão ---
st.info("💡 **Primeira vez aqui?** Clique no botão abaixo para criar uma base completa de categorias brasileiras!")

col1, col2 = st.columns([3, 1])

with col1:
    st.write("")

with col2:
    if st.button("🌱 Criar Base de Categorias", type="primary", help="Cria 18 categorias com 60+ subcategorias"):
        # Importar e executar o seed
        from scripts.seed_categories import DEFAULT_CATEGORIES
        
        total_cats = 0
        total_subs = 0
        
        with st.spinner("Criando categorias..."):
            for category, data in DEFAULT_CATEGORIES.items():
                subcategories = data["subcategories"]
                kind = data["kind"]
                
                try:
                    # Verifica se já existe
                    check = supa().table("categories")\
                        .select("*")\
                        .eq("user_id", uid)\
                        .eq("name", category)\
                        .is_("parent_name", "null")\
                        .execute()
                    
                    if not check.data:
                        supa().table("categories").insert({
                            "user_id": uid,
                            "name": category,
                            "parent_name": None,
                            "kind": kind
                        }).execute()
                        total_cats += 1
                    
                    # Cria subcategorias
                    for sub in subcategories:
                        sub_check = supa().table("categories")\
                            .select("*")\
                            .eq("user_id", uid)\
                            .eq("name", sub)\
                            .eq("parent_name", category)\
                            .execute()
                        
                        if not sub_check.data:
                            supa().table("categories").insert({
                                "user_id": uid,
                                "name": sub,
                                "parent_name": category,
                                "kind": kind
                            }).execute()
                            total_subs += 1
                
                except Exception as e:
                    st.error(f"Erro ao criar {category}: {e}")
                    continue
        
        st.success(f"✅ Base criada! {total_cats} categorias e {total_subs} subcategorias adicionadas!")
        st.balloons()
        st.rerun()

st.divider()

# --- Carregar regras do usuário com colunas garantidas ---
res = supa().table("categorization_rules").select("*").eq("user_id", uid).order("priority").execute()
rules = res.data or []
df_rules = pd.DataFrame(rules, columns=["id","user_id","pattern","category","subcategory","priority","created_at"])

if df_rules.empty:
    st.info("Você ainda não tem regras. Use o formulário abaixo ou clique em **Popular regras sugeridas**.")
else:
    st.dataframe(df_rules[["pattern","category","subcategory","priority"]], use_container_width=True)

# --- Botão para popular regras sugeridas (seed) ---
with st.expander("📦 Regras sugeridas (popular com 1 clique)"):
    default_rules = [
        {"pattern": r"IFOOD|RAPPI|UBER EATS", "category": "Alimentação", "subcategory": "Delivery", "priority": 10},
        {"pattern": r"SUPERMERCAD(O|OS)?|CARREFOUR|ASSA[IÍ]|EXTRA|ATACAD", "category": "Alimentação", "subcategory": "Mercado", "priority": 20},
        {"pattern": r"IFood|Rappi", "category": "Alimentação", "subcategory": "Delivery", "priority": 30},
        {"pattern": r"UBER|99 ?(POP|TAXI)?", "category": "Transporte", "subcategory": "App", "priority": 40},
        {"pattern": r"POSTO|SHELL|IPIRANGA|ETANOL|GASOLINA", "category": "Transporte", "subcategory": "Combustível", "priority": 50},
        {"pattern": r"ENERGIA|EQUATORIAL|ENEL|CEMIG|COELBA", "category": "Moradia", "subcategory": "Energia", "priority": 60},
        {"pattern": r"SANEAGO|SABESP|COPASA|ÁGUA|AGUA", "category": "Moradia", "subcategory": "Água", "priority": 70},
        {"pattern": r"VIVO|CLARO|TIM|OI|NET|GVT|FIBRA", "category": "Comunicações", "subcategory": "Telefonia/Internet", "priority": 80},
        {"pattern": r"FARM[ÁA]CIA|DROGARIA|RAIADROGASIL|PAGUE MENOS", "category": "Saúde", "subcategory": "Farmácia", "priority": 90},
        {"pattern": r"ACADEMIA|SMART FIT|G[ÊE]NIO FIT", "category": "Saúde", "subcategory": "Academia", "priority": 100},
        {"pattern": r"ALUGUEL|IMOBILI[ÁA]RIA|PJBank", "category": "Moradia", "subcategory": "Aluguel", "priority": 110},
        {"pattern": r"AMAZON|MAGALU|MERCADO LIVRE|SHEIN", "category": "Compras", "subcategory": "E-commerce", "priority": 120},
        {"pattern": r"IFIX|B3|DIVIDENDO|FII|ETF", "category": "Investimentos", "subcategory": "Proventos", "priority": 200},
        {"pattern": r"SAL[ÁA]RIO|HOLERITE|PROVENTO|RENDIMENTO", "category": "Receitas", "subcategory": "Salário", "priority": 300},
    ]
    if st.button("Popular regras sugeridas"):
        payload = [{**r, "user_id": uid} for r in default_rules]
        supa().table("categorization_rules").insert(payload).execute()
        st.success("Regras sugeridas criadas! Atualizando…")
        st.rerun()

# --- Formulário para nova regra ---
with st.form("new_rule"):
    pattern = st.text_input("Regex (ex: IFOOD|RAPPI|UBER)")
    category = st.text_input("Categoria", "Alimentação")
    subcat = st.text_input("Subcategoria", "Delivery")
    prio = st.number_input("Prioridade (menor aplica primeiro)", 1, 999, 100)
    s = st.form_submit_button("Adicionar")
    if s and pattern and category:
        supa().table("categorization_rules").insert({
            "user_id": uid, "pattern": pattern,
            "category": category, "subcategory": subcat or None,
            "priority": int(prio)
        }).execute()
        st.success("Regra criada."); st.rerun()
