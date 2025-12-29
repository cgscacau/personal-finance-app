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
    if st.button("🗑️ DELETAR TUDO", help="DELETA todas as suas categorias", type="secondary"):
        with st.spinner("Deletando todas as categorias..."):
            try:
                # Busca todas
                all_cats = supa().table("categories").select("id").eq("user_id", uid).execute()
                
                if all_cats.data:
                    count = len(all_cats.data)
                    st.write(f"Encontradas {count} categorias. Deletando...")
                    
                    # Deleta uma por uma
                    deleted = 0
                    for cat in all_cats.data:
                        try:
                            supa().table("categories").delete().eq("id", cat['id']).execute()
                            deleted += 1
                        except:
                            pass
                    
                    st.success(f"✅ {deleted} de {count} categorias deletadas!")
                else:
                    st.info("Nenhuma categoria encontrada.")
                
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro: {e}")

with col3:
    if st.button("🌱 Criar Base Limpa", type="primary", help="DELETA TUDO e cria 14 categorias organizadas do zero"):
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
                # Busca TODAS as categorias do usuário
                old_cats = supa().table("categories").select("id").eq("user_id", uid).execute()
                
                if old_cats.data:
                    st.write(f"Encontradas {len(old_cats.data)} categorias antigas. Deletando...")
                    
                    # Deleta uma por uma para garantir
                    for cat in old_cats.data:
                        try:
                            supa().table("categories").delete().eq("id", cat['id']).execute()
                        except:
                            pass
                    
                    st.write("✅ Categorias antigas deletadas!")
                else:
                    st.write("Nenhuma categoria antiga encontrada.")
            except Exception as e:
                st.warning(f"Aviso durante limpeza: {e}")
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
        
        # Verifica o que foi realmente criado
        try:
            verify = supa().table("categories").select("*").eq("user_id", uid).execute()
            verify_data = verify.data or []
            
            principals = [c for c in verify_data if not c.get('parent_name')]
            subs_created = [c for c in verify_data if c.get('parent_name')]
            
            st.success(f"✅ Base criada!")
            st.info(f"📊 Verificação: {len(principals)} categorias principais e {len(subs_created)} subcategorias no banco")
            
            if len(principals) != 14:
                st.warning(f"⚠️ Esperado 14 categorias, mas encontrado {len(principals)}!")
            
            st.balloons()
        except Exception as e:
            st.error(f"Erro na verificação: {e}")
        
        st.rerun()

st.divider()

# --- Mostrar categorias atuais (DEBUG) ---
with st.expander("🔍 Debug: Ver categorias no banco"):
    try:
        cats_res = supa().table("categories").select("*").eq("user_id", uid).execute()
        cats_data = cats_res.data or []
        
        if cats_data:
            df_cats = pd.DataFrame(cats_data)
            st.write(f"**Total de registros:** {len(cats_data)}")
            
            # Separa principais e subcategorias
            principais = [c for c in cats_data if not c.get('parent_name')]
            subs = [c for c in cats_data if c.get('parent_name')]
            
            st.write(f"**Categorias principais:** {len(principais)}")
            st.write(f"**Subcategorias:** {len(subs)}")
            
            # Mostra estrutura
            st.dataframe(df_cats[["name", "parent_name", "kind"]], use_container_width=True)
            
            # Mostra hierarquia
            st.write("**Hierarquia:**")
            for cat in principais:
                cat_name = cat['name']
                st.write(f"**{cat_name}**")
                cat_subs = [s['name'] for s in subs if s.get('parent_name') == cat_name]
                for sub in cat_subs:
                    st.write(f"  └─ {sub}")
        else:
            st.info("Nenhuma categoria no banco.")
    
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")

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
