import streamlit as st
from app.auth import require_login, current_user_id, logout

st.set_page_config(page_title="Gestor Financeiro", page_icon="💸", layout="wide")

# exige login e cria sessão se necessário
require_login()
uid = current_user_id()

# =========================================================
# CONTEÚDO PRINCIPAL
# =========================================================
st.title("💸 Gestor de Finanças Pessoais & Familiares")
st.write("Use o menu lateral para navegar: Importar, Dashboard, Lançamentos, Regras, Orçamentos e Metas, Configurações.")

st.markdown("---")

# Seção de boas-vindas
st.subheader("👋 Bem-vindo!")
st.write("""
Organize suas finanças de forma simples e eficiente:

- **📊 Dashboard**: Visualize suas receitas, despesas e saldo
- **📥 Importar & Higienizar**: Importe extratos bancários
- **💳 Contas & Lançamentos**: Gerencie seus lançamentos manuais
- **🎯 Regras**: Configure regras de categorização automática
- **💰 Orçamentos e Metas**: Defina e acompanhe seus objetivos financeiros
- **⚙️ Configurações**: Personalize suas preferências
""")

# =========================================================
# SIDEBAR - INFORMAÇÕES E LOGOUT
# =========================================================
st.sidebar.success("✅ Autenticado!")

# Informações da sessão
st.sidebar.markdown("---")
st.sidebar.subheader("👤 Sessão Atual")

if "session" in st.session_state and st.session_state.session:
    st.sidebar.success("✅ Sessão autenticada")
    
    # Mostra email do usuário
    user_email = st.session_state.session.user.email
    st.sidebar.write(f"**Email:** {user_email}")
    
    # Mostra ID do usuário (primeiros 8 caracteres)
    st.sidebar.caption(f"ID: {uid[:8]}...")
else:
    st.sidebar.error("🚫 Sessão não detectada")

# Separador visual
st.sidebar.markdown("---")

# =========================================================
# BOTÕES DE AÇÃO
# =========================================================
st.sidebar.subheader("🔧 Ações")

# Botão para atualizar a página
if st.sidebar.button("🔄 Atualizar Página", use_container_width=True):
    st.rerun()

# Espaçamento
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Seção de logout com destaque
st.sidebar.markdown("### 🚪 Sair do Sistema")

# Botão de logout com confirmação
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("🔓 Logout", type="primary", use_container_width=True):
        # Executa logout
        logout()
        st.success("✅ Logout realizado!")
        st.info("👋 Até logo! Redirecionando...")
        st.rerun()

with col2:
    if st.button("🔄 Trocar Conta", use_container_width=True):
        # Limpa sessão para trocar de conta
        logout()
        st.success("✅ Sessão encerrada!")
        st.info("🔑 Faça login com outra conta...")
        st.rerun()

# Aviso de segurança
st.sidebar.caption("⚠️ Lembre-se de fazer logout ao usar computadores compartilhados!")

# =========================================================
# RODAPÉ
# =========================================================
st.markdown("---")
st.caption("💡 **Dica:** Explore todas as funcionalidades usando o menu lateral!")
