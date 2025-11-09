"""
Módulo de autenticação do Gestor Financeiro
-------------------------------------------------------
Permite login e cadastro direto via Supabase Auth,
mantendo a sessão ativa no Streamlit.
-------------------------------------------------------
"""

import streamlit as st
from supabase import create_client, Client


# =====================================================
# 🔧 CONFIGURAÇÃO DO SUPABASE
# =====================================================
def get_supabase() -> Client:
    """Conecta ao Supabase usando as chaves do secrets.toml"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


# =====================================================
# 🔑 FUNÇÕES DE LOGIN / CADASTRO
# =====================================================
def sign_in(email: str, password: str):
    """Realiza login de usuário existente"""
    supa = get_supabase()
    return supa.auth.sign_in_with_password({"email": email, "password": password})


def sign_up(email: str, password: str):
    """Cria uma nova conta de usuário"""
    supa = get_supabase()
    return supa.auth.sign_up({"email": email, "password": password})


def sign_out():
    """Encerra sessão atual"""
    if "session" in st.session_state:
        st.session_state.session = None
        st.success("Sessão encerrada com sucesso.")
        st.rerun()


def current_user_id():
    """Retorna o ID do usuário logado"""
    if "session" in st.session_state and st.session_state.session:
        try:
            return st.session_state.session.user.id
        except Exception:
            return None
    return None


# =====================================================
# 🧠 FUNÇÃO CENTRAL DE LOGIN/REGISTRO
# =====================================================
def require_login():
    """
    Exige login do usuário antes de acessar o app.
    Caso não haja sessão ativa, exibe as abas:
    - Login
    - Criar conta
    """
    if "session" not in st.session_state:
        st.session_state.session = None

    if st.session_state.session is None:
        st.markdown("### 🔐 Acesso ao Sistema")

        tab_login, tab_signup = st.tabs(["🔑 Login", "🆕 Criar Conta"])

        # ---------------- LOGIN ----------------
        with tab_login:
            st.subheader("Entre com suas credenciais")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Senha", type="password", key="login_pass")

            if st.button("Entrar"):
                if not email or not password:
                    st.warning("Por favor, preencha email e senha.")
                else:
                    try:
                        res = sign_in(email, password)
                        st.session_state.session = res
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Falha no login: {e}")

        # ---------------- CRIAR CONTA ----------------
        with tab_signup:
            st.subheader("Criar nova conta")
            new_email = st.text_input("Novo email", key="signup_email")
            new_pass = st.text_input("Nova senha", type="password", key="signup_pass")

            if st.button("Cadastrar"):
                if not new_email or not new_pass:
                    st.warning("Preencha email e senha para criar a conta.")
                else:
                    try:
                        res = sign_up(new_email, new_pass)
                        if res and res.user:
                            st.success("✅ Conta criada com sucesso! Faça login na aba ao lado.")
                        else:
                            st.info("Conta criada! Verifique seu e-mail (se confirmação estiver ativada).")
                    except Exception as e:
                        st.error(f"Erro ao criar conta: {e}")

        st.stop()


# =====================================================
# 🔒 UTILITÁRIO DE PROTEÇÃO DE PÁGINAS
# =====================================================
def protected_page():
    """Chama esta função no topo de páginas que exigem login"""
    if "session" not in st.session_state or st.session_state.session is None:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()
