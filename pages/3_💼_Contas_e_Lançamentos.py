# pages/3_💳_Contas_e_Lançamentos.py
import streamlit as st
import pandas as pd
from datetime import date as date_type
from app.auth import require_login, current_user_id
from app.db import supa

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Contas & Lançamentos", 
    page_icon="💳", 
    layout="wide"
)
st.title("💳 Contas & Lançamentos")

# Verifica autenticação
require_login()
uid = current_user_id()

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def load_accounts(uid: str):
    """
    Carrega todas as contas do usuário autenticado.
    
    Args:
        uid: ID do usuário
        
    Returns:
        Lista de dicionários com dados das contas
    """
    try:
        res = supa().table("accounts")\
            .select("*")\
            .eq("user_id", uid)\
            .order("created_at")\
            .execute()
        
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao carregar contas: {e}")
        return []


def load_categories(uid: str):
    """
    Carrega o catálogo de categorias e subcategorias do usuário.
    
    Estrutura no banco:
    - Categoria principal: {name: "Alimentação", parent_name: null}
    - Subcategoria: {name: "Delivery", parent_name: "Alimentação"}
    
    Args:
        uid: ID do usuário
        
    Returns:
        Tupla contendo:
        - cat_names: lista ordenada de nomes de categorias principais
        - sub_by_cat: dicionário {categoria: [subcategorias]}
    """
    try:
        res = supa().table("categories")\
            .select("name, parent_name, kind")\
            .eq("user_id", uid)\
            .order("name")\
            .execute()
        
        cats = res.data or []
        
        # Debug: mostra o que veio do banco
        if st.session_state.get("debug_mode", False):
            st.write("**DEBUG - Dados do banco:**", cats)
        
    except Exception as e:
        st.error(f"Erro ao carregar categorias: {e}")
        cats = []
    
    # Conjuntos e dicionários para organizar dados
    all_categories = set()  # Todas as categorias principais
    sub_by_cat = {}  # Mapeamento categoria -> [subcategorias]
    
    # Primeira passagem: identifica todas as categorias principais
    for c in cats:
        name = (c.get("name") or "").strip()
        parent = (c.get("parent_name") or "").strip()
        
        if not name:
            continue
        
        # Se não tem parent_name, é uma categoria principal
        if not parent:
            all_categories.add(name)
            if name not in sub_by_cat:
                sub_by_cat[name] = []
    
    # Segunda passagem: mapeia subcategorias para suas categorias
    for c in cats:
        name = (c.get("name") or "").strip()
        parent = (c.get("parent_name") or "").strip()
        
        if not name:
            continue
        
        # Se tem parent_name, é uma subcategoria
        if parent:
            # Garante que a categoria pai existe no dicionário
            if parent not in sub_by_cat:
                sub_by_cat[parent] = []
            
            # Adiciona a subcategoria à lista da categoria pai
            if name not in sub_by_cat[parent]:
                sub_by_cat[parent].append(name)
            
            # Adiciona a categoria pai ao conjunto (caso não tenha sido adicionada antes)
            all_categories.add(parent)
    
    # Ordena as subcategorias de cada categoria
    for cat in sub_by_cat:
        sub_by_cat[cat] = sorted(sub_by_cat[cat])
    
    # Debug: mostra estrutura processada
    if st.session_state.get("debug_mode", False):
        st.write("**DEBUG - Categorias processadas:**", sorted(all_categories))
        st.write("**DEBUG - Subcategorias por categoria:**", sub_by_cat)
    
    # Retorna categorias ordenadas e o mapeamento de subcategorias
    cat_names = sorted(all_categories)
    
    return cat_names, sub_by_cat


def load_transactions(uid: str, account_id: str = None):
    """
    Carrega os lançamentos do usuário, opcionalmente filtrados por conta.
    
    Args:
        uid: ID do usuário
        account_id: ID da conta (opcional, filtra por conta específica)
        
    Returns:
        Lista de dicionários com dados dos lançamentos
    """
    try:
        q = supa().table("transactions")\
            .select("*")\
            .eq("user_id", uid)
        
        # Filtra por conta se especificado
        if account_id:
            q = q.eq("account_id", account_id)
        
        res = q.order("date", desc=True).execute()
        
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao carregar transações: {e}")
        return []


def insert_category(uid: str, category: str, subcategory: str = None, kind: str = "both"):
    """
    Insere uma categoria e opcionalmente uma subcategoria no banco.
    
    Args:
        uid: ID do usuário
        category: Nome da categoria principal
        subcategory: Nome da subcategoria (opcional)
        kind: Tipo (expense, income, both)
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        category = category.strip()
        
        # Verifica se a categoria principal já existe
        cat_check = supa().table("categories")\
            .select("*")\
            .eq("user_id", uid)\
            .eq("name", category)\
            .is_("parent_name", "null")\
            .execute()
        
        # Se não existe, cria a categoria principal
        if not cat_check.data:
            supa().table("categories").insert({
                "user_id": uid,
                "name": category,
                "parent_name": None,
                "kind": kind
            }).execute()
        
        # Se há subcategoria, cria o registro da subcategoria
        if subcategory and subcategory.strip():
            subcategory = subcategory.strip()
            
            # Verifica se a subcategoria já existe
            sub_check = supa().table("categories")\
                .select("*")\
                .eq("user_id", uid)\
                .eq("name", subcategory)\
                .eq("parent_name", category)\
                .execute()
            
            # Se não existe, cria
            if not sub_check.data:
                supa().table("categories").insert({
                    "user_id": uid,
                    "name": subcategory,
                    "parent_name": category,
                    "kind": kind
                }).execute()
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao cadastrar categoria: {e}")
        return False


def insert_transaction(uid: str, account_id: str, trans_date, description: str, 
                       amount: float, category: str = None, subcategory: str = None, 
                       tags: str = None):
    """
    Insere um novo lançamento no banco de dados.
    
    Args:
        uid: ID do usuário
        account_id: ID da conta
        trans_date: Data do lançamento
        description: Descrição do lançamento
        amount: Valor (negativo para despesa, positivo para receita)
        category: Categoria (opcional)
        subcategory: Subcategoria (opcional)
        tags: Tags separadas por vírgula (opcional)
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        # Processa tags
        tags_list = None
        if tags:
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Processa categoria e subcategoria
        final_category = category.strip() if category and category.strip() else None
        final_subcategory = subcategory.strip() if subcategory and subcategory.strip() else None
        
        # Monta payload
        payload = {
            "user_id": uid,
            "account_id": account_id,
            "date": str(trans_date),
            "description": description.strip(),
            "amount": float(amount),
            "category": final_category,
            "subcategory": final_subcategory,
            "tags": tags_list,
            "source_file": "manual",
        }
        
        # Insere no banco
        supa().table("transactions").insert(payload).execute()
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao inserir lançamento: {e}")
        return False


def delete_transaction(transaction_id: str):
    """
    Exclui um lançamento do banco de dados.
    
    Args:
        transaction_id: ID do lançamento a ser excluído
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        supa().table("transactions")\
            .delete()\
            .eq("id", transaction_id)\
            .execute()
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao excluir lançamento: {e}")
        return False


# =========================================================
# MODO DEBUG (OPCIONAL)
# =========================================================
if st.sidebar.checkbox("🐛 Modo Debug", value=False):
    st.session_state.debug_mode = True
else:
    st.session_state.debug_mode = False

# =========================================================
# SELEÇÃO DE CONTA
# =========================================================
st.subheader("🏦 Selecione a conta")

accounts = load_accounts(uid)

# Verifica se usuário tem contas cadastradas
if not accounts:
    st.warning("⚠️ Você ainda não tem contas cadastradas.")
    st.info("💡 Crie uma conta em **Importar & Higienizar → ➕ Criar nova conta**.")
    st.stop()

# Cria mapeamento nome -> id
name_to_id = {a["name"]: a["id"] for a in accounts}

# Selectbox para escolher a conta
account_name = st.selectbox(
    "Conta", 
    list(name_to_id.keys()),
    help="Selecione a conta para visualizar e adicionar lançamentos"
)

aid = name_to_id.get(account_name)

st.divider()

# =========================================================
# CADASTRO DE CATEGORIAS
# =========================================================
st.subheader("📋 Catálogo de Categorias")

# Carrega categorias ANTES do expander para poder mostrar resumo
cat_names, sub_by_cat = load_categories(uid)

# Mostra resumo das categorias cadastradas
if cat_names:
    total_cats = len(cat_names)
    total_subs = sum(len(subs) for subs in sub_by_cat.values())
    st.caption(f"📊 Você tem **{total_cats} categorias** e **{total_subs} subcategorias** cadastradas.")

with st.expander("➕ Cadastrar nova categoria/subcategoria"):
    st.caption(
        "Mantenha um catálogo organizado de categorias para facilitar "
        "o lançamento manual e a geração de relatórios."
    )
    
    # Formulário de cadastro
    with st.form("form_categoria", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            new_cat = st.text_input(
                "Categoria *", 
                placeholder="Ex.: Alimentação, Transporte, Lazer",
                help="Nome da categoria principal"
            )
        
        with col2:
            new_sub = st.text_input(
                "Subcategoria", 
                placeholder="Ex.: Delivery, Restaurante, Supermercado",
                help="Nome da subcategoria (opcional)"
            )
        
        with col3:
            kind = st.selectbox(
                "Tipo", 
                ["both", "expense", "income"],
                help="Define se a categoria é para despesas, receitas ou ambos"
            )
        
        submitted_cat = st.form_submit_button("✅ Adicionar categoria")
        
        if submitted_cat:
            if not new_cat or not new_cat.strip():
                st.warning("⚠️ Informe ao menos o nome da categoria.")
            else:
                success = insert_category(uid, new_cat, new_sub, kind)
                
                if success:
                    st.success("✅ Categoria cadastrada com sucesso!")
                    st.rerun()

# Mostra lista de categorias existentes
if cat_names:
    with st.expander("📋 Ver todas as categorias cadastradas"):
        for cat in cat_names:
            subs = sub_by_cat.get(cat, [])
            if subs:
                st.write(f"**{cat}**")
                for sub in subs:
                    st.write(f"  └─ {sub}")
            else:
                st.write(f"**{cat}** _(sem subcategorias)_")

st.divider()

# =========================================================
# FORMULÁRIO DE NOVO LANÇAMENTO
# =========================================================
st.subheader("📝 Novo Lançamento")

# Recarrega categorias para garantir dados atualizados
cat_names, sub_by_cat = load_categories(uid)

with st.form("form_lancamento", clear_on_submit=True):
    
    # -------------------- LINHA 1: Data e Descrição --------------------
    col1, col2 = st.columns([1, 3])
    
    with col1:
        date_input = st.date_input(
            "Data *",
            help="Data do lançamento",
            value=date_type.today()
        )
    
    with col2:
        description_input = st.text_input(
            "Descrição *", 
            placeholder="Ex.: Almoço no restaurante, Uber para o trabalho, Salário",
            help="Descrição detalhada do lançamento"
        )
    
    # -------------------- LINHA 2: Valor e Categorização --------------------
    col3, col4 = st.columns([1, 2])
    
    with col3:
        amount_input = st.number_input(
            "Valor *", 
            step=0.01, 
            format="%.2f",
            help="Valor negativo para despesa, positivo para receita"
        )
    
    with col4:
        # Toggle para usar catálogo ou entrada manual
        use_catalog = st.toggle(
            "📚 Usar catálogo de categorias", 
            value=bool(cat_names),
            help="Ative para selecionar categorias do seu catálogo"
        )
        
        # Inicializa variáveis
        category_input = None
        subcategory_input = None
        
        if use_catalog and cat_names:
            # ========== MODO CATÁLOGO ==========
            
            # Opções de categoria (inclui opção manual)
            options_cat = [""] + cat_names + ["✏️ (digitar manualmente)"]
            
            category_input = st.selectbox(
                "Categoria", 
                options_cat,
                help="Selecione uma categoria do catálogo ou digite manualmente"
            )
            
            # Se escolheu digitar manualmente
            if category_input == "✏️ (digitar manualmente)":
                category_input = st.text_input(
                    "Digite a categoria",
                    placeholder="Ex.: Nova Categoria"
                )
                subcategory_input = st.text_input(
                    "Digite a subcategoria (opcional)",
                    placeholder="Ex.: Nova Subcategoria"
                )
            
            elif category_input:  # Se selecionou uma categoria do catálogo
                # Busca subcategorias da categoria selecionada
                subs = sub_by_cat.get(category_input, [])
                
                if subs:
                    # Tem subcategorias cadastradas
                    options_sub = ["(sem subcategoria)"] + subs
                    
                    subcategory_input = st.selectbox(
                        "Subcategoria", 
                        options_sub,
                        help="Selecione uma subcategoria ou deixe sem"
                    )
                    
                    # Se escolheu "sem subcategoria"
                    if subcategory_input == "(sem subcategoria)":
                        subcategory_input = None
                
                else:
                    # Não tem subcategorias cadastradas
                    st.info(f"ℹ️ A categoria '{category_input}' não possui subcategorias cadastradas.")
                    subcategory_input = None
        
        else:
            # ========== MODO MANUAL ==========
            category_input = st.text_input(
                "Categoria",
                placeholder="Ex.: Alimentação, Transporte",
                help="Digite o nome da categoria"
            )
            
            subcategory_input = st.text_input(
                "Subcategoria",
                placeholder="Ex.: Delivery, Uber",
                help="Digite o nome da subcategoria (opcional)"
            )
    
    # -------------------- LINHA 3: Tags --------------------
    tags_input = st.text_input(
        "Tags (opcional)", 
        placeholder="Ex.: nubank, ifood, trabalho",
        help="Tags separadas por vírgula para facilitar buscas futuras"
    )
    
    # -------------------- BOTÃO DE SUBMIT --------------------
    submitted_transaction = st.form_submit_button("➕ Adicionar lançamento", type="primary")
    
    if submitted_transaction:
        # Validações
        if not description_input or not description_input.strip():
            st.warning("⚠️ Preencha a descrição do lançamento.")
        
        elif amount_input is None or amount_input == 0:
            st.warning("⚠️ Informe um valor diferente de zero.")
        
        else:
            # Insere o lançamento
            success = insert_transaction(
                uid=uid,
                account_id=aid,
                trans_date=date_input,
                description=description_input,
                amount=amount_input,
                category=category_input,
                subcategory=subcategory_input,
                tags=tags_input
            )
            
            if success:
                st.success("✅ Lançamento inserido com sucesso!")
                st.rerun()

st.divider()

# =========================================================
# LISTAGEM DE LANÇAMENTOS
# =========================================================
st.subheader("📜 Lançamentos Registrados")

# Carrega lançamentos da conta selecionada
data = load_transactions(uid, aid)
df = pd.DataFrame(data)

if df.empty:
    st.info("ℹ️ Nenhum lançamento encontrado para esta conta.")

else:
    # Define colunas a serem exibidas
    view_cols = ["date", "description", "amount", "category", "subcategory", "tags"]
    
    # Garante que todas as colunas existem
    for col in view_cols:
        if col not in df.columns:
            df[col] = None
    
    # Formata a coluna de valor para mostrar tipo de transação
    df_display = df[view_cols].copy()
    
    # Exibe tabela
    st.dataframe(
        df_display, 
        use_container_width=True, 
        height=460,
        column_config={
            "date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "description": st.column_config.TextColumn("Descrição", width="large"),
            "amount": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            "category": st.column_config.TextColumn("Categoria"),
            "subcategory": st.column_config.TextColumn("Subcategoria"),
            "tags": st.column_config.ListColumn("Tags"),
        }
    )
    
    # Estatísticas rápidas
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        total_receitas = df[df["amount"] > 0]["amount"].sum()
        st.metric("💰 Total Receitas", f"R$ {total_receitas:,.2f}")
    
    with col_stat2:
        total_despesas = df[df["amount"] < 0]["amount"].sum()
        st.metric("💸 Total Despesas", f"R$ {total_despesas:,.2f}")
    
    with col_stat3:
        saldo = df["amount"].sum()
        st.metric("📊 Saldo", f"R$ {saldo:,.2f}")
    
    # -------------------- EXCLUSÃO DE LANÇAMENTO --------------------
    with st.expander("🗑️ Excluir lançamento"):
        st.caption("⚠️ Esta ação não pode ser desfeita.")
        
        # Cria DataFrame simplificado para seleção
        df_small = df[["id", "date", "description", "amount"]].copy()
        
        # Cria label legível para cada lançamento
        df_small["label"] = df_small.apply(
            lambda r: (
                f'{str(r["date"])} | '
                f'{str(r["description"])[:50]} | '
                f'R$ {float(r["amount"]):.2f}'
            ),
            axis=1
        )
        
        # Selectbox para escolher lançamento
        to_delete_label = st.selectbox(
            "Selecione o lançamento a excluir",
            df_small["label"],
            help="Escolha o lançamento que deseja remover"
        )
        
        # Botão de exclusão
        if st.button("🗑️ Confirmar exclusão", type="primary"):
            # Encontra o registro correspondente
            row = df_small[df_small["label"] == to_delete_label].iloc[0]
            
            # Exclui do banco
            success = delete_transaction(row["id"])
            
            if success:
                st.success("✅ Lançamento excluído com sucesso!")
                st.rerun()
