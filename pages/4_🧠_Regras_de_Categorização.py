import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import supa

st.title("🧠 Regras de Categorização")
require_login()
uid = current_user_id()

# --- Botão para popular categorias padrão ---
st.warning("⚠️ **Categorias desorganizadas?** Use o botão abaixo para LIMPAR TUDO e criar uma base organizada!")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.write("")

with col2:
    if st.button("🗑️ Limpar Categorias", help="DELETA todas as suas categorias"):
        try:
            supa().table("categories").delete().eq("user_id", uid).execute()
            st.success("✅ Categorias deletadas!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro: {e}")

with col3:
    if st.button("🌱 Criar Base Limpa", type="primary", help="Deleta tudo e cria 14 categorias organizadas"):
        # Categorias padrão CORRIGIDAS
        DEFAULT_CATEGORIES = {
            # DESPESAS
            "Alimentação": ["Supermercado", "Restaurante", "Delivery", "Padaria", "Lanchonete"],
            "Transporte": ["Combustível", "Uber/99", "Ônibus", "Estacionamento", "Manutenção", "IPVA"],
            "Moradia": ["Aluguel", "Condomínio", "IPTU", "Água", "Luz", "Gás", "Internet"],
            "Saúde": ["Plano de Saúde", "Farmácia", "Médico", "Dentista", "Exames", "Academia"],
            "Educação": ["Mensalidade", "Material", "Livros", "Cursos"],
            "Lazer": ["Cinema", "Shows", "Viagens", "Streaming", "Jogos"],
            "Vestuário": ["Roupas", "Calçados", "Acessórios"],
            "Beleza": ["Salão", "Produtos", "Cosméticos"],
            "Pets": ["Ração", "Veterinário", "Produtos"],
            # RECEITAS
            "Salário": ["Salário Mensal", "13º", "Férias", "Bônus"],
            "Freelance": ["Projetos", "Consultorias", "Serviços"],
            "Rendimentos": ["Dividendos", "Juros", "Aluguel"],
            # OUTROS
            "Transferências": ["Entre Contas", "Pix", "TED", "DOC"],
            "Doações": ["Caridade", "Presentes", "Ajuda Família"],
        }
        
        total_cats = 0
        total_subs = 0
        
        with st.spinner("🗑️ Limpando categorias antigas..."):
            try:
                supa().table("categories").delete().eq("user_id", uid).execute()
            except:
                pass
        
        with st.spinner("🌱 Criando categorias organizadas..."):
            for category, subcategories in DEFAULT_CATEGORIES.items():
                try:
                    # Cria categoria principal
                    supa().table("categories").insert({
                        "user_id": uid,
                        "name": category,
                        "parent_name": None,
                        "kind": "both"
                    }).execute()
                    total_cats += 1
                    
                    # Cria subcategorias
                    for sub in subcategories:
                        supa().table("categories").insert({
                            "user_id": uid,
                            "name": sub,
                            "parent_name": category,
                            "kind": "both"
                        }).execute()
                        total_subs += 1
                
                except Exception as e:
                    st.error(f"Erro ao criar {category}: {e}")
                    continue
        
        st.success(f"✅ Base criada! {total_cats} categorias e {total_subs} subcategorias!")
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
