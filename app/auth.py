import streamlit as st
from supabase import create_client

def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

def sign_in(email, password):
    return get_supabase().auth.sign_in_with_password({"email": email, "password": password})

def sign_up(email, password):
    return get_supabase().auth.sign_up({"email": email, "password": password})

def require_login():
    if "session" not in st.session_state:
        st.session_state.session = None

    if st.session_state.session is None:
        tab_login, tab_signup = st.tabs(["🔑 Login", "🆕 Criar Conta"])

        # ---- Login ----
        with tab_login:
            st.subheader("Acesso ao sistema")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Senha", type="password", key="login_pass")
            if st.button("Entrar"):
                try:
                    res = sign_in(email, password)
                    st.session_state.session = res
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Falha no login: {e}")

        # ---- Cadastro ----
        with tab_signup:
            st.subheader("Criar nova conta")
            new_email = st.text_input("Novo email", key="signup_email")
            new_pass = st.text_input("Nova senha", type="password", key="signup_pass")
            if st.button("Cadastrar"):
                if not new_email or not new_pass:
                    st.warning("Preencha email e senha.")
                else:
                    try:
                        res = sign_up(new_email, new_pass)
                        st.success("Conta criada com sucesso! Faça login na aba ao lado.")
                    except Exception as e:
                        st.error(f"Erro ao criar conta: {e}")

        st.stop()
