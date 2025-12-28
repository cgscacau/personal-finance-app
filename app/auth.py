"""
Módulo de autenticação do Gestor Financeiro
-------------------------------------------------------
Permite login e cadastro direto via Supabase Auth,
mantendo a sessão ativa no Streamlit.
Inclui validação, rate limiting e segurança aprimorada.
-------------------------------------------------------
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.utils import logger, is_valid_email, sanitize_string
from app.models import UserLogin, UserSignup
from pydantic import ValidationError


# =====================================================
# 🔧 EXCEÇÕES CUSTOMIZADAS
# =====================================================

class AuthenticationError(Exception):
    """Erro de autenticação"""
    pass


class RateLimitError(AuthenticationError):
    """Erro de limite de tentativas excedido"""
    pass


# =====================================================
# 🔒 RATE LIMITING
# =====================================================

def check_rate_limit(key: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
    """
    Verifica se usuário excedeu limite de tentativas
    
    Args:
        key: Identificador único (email, IP, etc)
        max_attempts: Máximo de tentativas permitidas
        window_minutes: Janela de tempo em minutos
        
    Returns:
        True se dentro do limite, False se excedeu
    """
    if "rate_limit" not in st.session_state:
        st.session_state.rate_limit = {}
    
    now = datetime.now()
    
    # Limpa tentativas antigas
    if key in st.session_state.rate_limit:
        attempts = st.session_state.rate_limit[key]
        # Remove tentativas fora da janela de tempo
        attempts = [t for t in attempts if now - t < timedelta(minutes=window_minutes)]
        st.session_state.rate_limit[key] = attempts
    else:
        st.session_state.rate_limit[key] = []
    
    # Verifica limite
    if len(st.session_state.rate_limit[key]) >= max_attempts:
        logger.warning(f"Rate limit excedido para {key}")
        return False
    
    return True


def record_attempt(key: str):
    """Registra tentativa de login"""
    if "rate_limit" not in st.session_state:
        st.session_state.rate_limit = {}
    
    if key not in st.session_state.rate_limit:
        st.session_state.rate_limit[key] = []
    
    st.session_state.rate_limit[key].append(datetime.now())


# =====================================================
# 🔧 CONFIGURAÇÃO DO SUPABASE
# =====================================================

@st.cache_resource
def get_supabase() -> Client:
    """
    Conecta ao Supabase usando as chaves do secrets.toml
    
    Returns:
        Cliente Supabase
        
    Raises:
        AuthenticationError: Se credenciais não configuradas
    """
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise AuthenticationError("Credenciais do Supabase não configuradas")
        
        logger.info("Cliente Supabase Auth criado")
        return create_client(url, key)
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente Supabase: {e}")
        raise AuthenticationError(f"Falha na configuração de autenticação: {e}")


# =====================================================
# 🔑 FUNÇÕES DE LOGIN / CADASTRO
# =====================================================

def sign_in(email: str, password: str) -> Dict[str, Any]:
    """
    Realiza login de usuário existente
    
    Args:
        email: Email do usuário
        password: Senha do usuário
        
    Returns:
        Dados da sessão
        
    Raises:
        ValidationError: Se dados inválidos
        RateLimitError: Se excedeu limite de tentativas
        AuthenticationError: Se falhar autenticação
    """
    try:
        # Sanitiza entrada
        email = sanitize_string(email.lower().strip(), max_length=100)
        
        # Valida formato de email básico
        if not is_valid_email(email):
            raise ValidationError("Formato de email inválido")
        
        # Verifica rate limit
        if not check_rate_limit(email, max_attempts=5, window_minutes=15):
            raise RateLimitError(
                "Muitas tentativas de login. Aguarde 15 minutos e tente novamente."
            )
        
        # Registra tentativa
        record_attempt(email)
        
        # Valida com Pydantic
        user_data = UserLogin(email=email, password=password)
        
        logger.info(f"Tentativa de login: {email}")
        
        # Realiza login
        supa = get_supabase()
        result = supa.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        
        logger.info(f"Login bem-sucedido: {email}")
        return result
        
    except ValidationError as e:
        logger.warning(f"Validação falhou no login: {e}")
        raise ValidationError(f"Dados inválidos: {e}")
        
    except RateLimitError:
        raise
        
    except Exception as e:
        logger.error(f"Erro no login para {email}: {e}")
        raise AuthenticationError(f"Falha no login: {e}")


def sign_up(email: str, password: str, confirm_password: Optional[str] = None) -> Dict[str, Any]:
    """
    Cria uma nova conta de usuário
    
    Args:
        email: Email do usuário
        password: Senha do usuário
        confirm_password: Confirmação de senha (opcional)
        
    Returns:
        Dados do usuário criado
        
    Raises:
        ValidationError: Se dados inválidos
        RateLimitError: Se excedeu limite de tentativas
        AuthenticationError: Se falhar criação
    """
    try:
        # Sanitiza entrada
        email = sanitize_string(email.lower().strip(), max_length=100)
        
        # Valida formato de email
        if not is_valid_email(email):
            raise ValidationError("Formato de email inválido")
        
        # Verifica confirmação de senha
        if confirm_password and password != confirm_password:
            raise ValidationError("As senhas não coincidem")
        
        # Verifica rate limit
        rate_limit_key = f"signup_{email}"
        if not check_rate_limit(rate_limit_key, max_attempts=3, window_minutes=60):
            raise RateLimitError(
                "Muitas tentativas de cadastro. Aguarde 1 hora e tente novamente."
            )
        
        # Registra tentativa
        record_attempt(rate_limit_key)
        
        # Valida com Pydantic (validação forte de senha)
        user_data = UserSignup(
            email=email,
            password=password,
            confirm_password=confirm_password
        )
        
        logger.info(f"Tentativa de cadastro: {email}")
        
        # Cria conta
        supa = get_supabase()
        result = supa.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        logger.info(f"Cadastro bem-sucedido: {email}")
        return result
        
    except ValidationError as e:
        logger.warning(f"Validação falhou no cadastro: {e}")
        # Retorna mensagens de erro mais amigáveis
        error_msg = str(e)
        if "senha" in error_msg.lower():
            raise ValidationError(
                "Senha deve ter: mínimo 8 caracteres, "
                "letras maiúsculas, minúsculas e números"
            )
        raise ValidationError(f"Dados inválidos: {e}")
        
    except RateLimitError:
        raise
        
    except Exception as e:
        logger.error(f"Erro no cadastro para {email}: {e}")
        raise AuthenticationError(f"Falha ao criar conta: {e}")


def sign_out():
    """
    Encerra sessão atual e limpa dados sensíveis
    """
    try:
        logger.info("Realizando logout")
        
        # Limpa dados da sessão
        if "session" in st.session_state:
            st.session_state.session = None
        
        # Limpa outros dados sensíveis
        keys_to_clear = ["user_id", "user_email", "cached_data"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        logger.info("Logout realizado com sucesso")
        st.success("✅ Sessão encerrada com sucesso.")
        st.rerun()
        
    except Exception as e:
        logger.error(f"Erro ao fazer logout: {e}")
        # Força limpeza mesmo com erro
        st.session_state.clear()
        st.rerun()


def current_user_id() -> Optional[str]:
    """
    Retorna o ID do usuário logado
    
    Returns:
        ID do usuário ou None se não logado
    """
    try:
        if "session" in st.session_state and st.session_state.session:
            user_id = st.session_state.session.user.id
            return user_id
    except Exception as e:
        logger.warning(f"Erro ao obter ID do usuário: {e}")
    
    return None


def current_user_email() -> Optional[str]:
    """
    Retorna o email do usuário logado
    
    Returns:
        Email do usuário ou None se não logado
    """
    try:
        if "session" in st.session_state and st.session_state.session:
            return st.session_state.session.user.email
    except Exception as e:
        logger.warning(f"Erro ao obter email do usuário: {e}")
    
    return None


def is_authenticated() -> bool:
    """
    Verifica se usuário está autenticado
    
    Returns:
        True se autenticado, False caso contrário
    """
    return current_user_id() is not None


# =====================================================
# 🧠 FUNÇÃO CENTRAL DE LOGIN/REGISTRO
# =====================================================

def require_login():
    """
    Exige login do usuário antes de acessar o app.
    Caso não haja sessão ativa, exibe as abas:
    - Login
    - Criar conta
    
    Com validação, rate limiting e mensagens de erro amigáveis.
    """
    if "session" not in st.session_state:
        st.session_state.session = None

    if st.session_state.session is None:
        st.markdown("### 🔐 Acesso ao Sistema")
        st.caption("Por favor, faça login ou crie uma conta para continuar")

        tab_login, tab_signup = st.tabs(["🔑 Login", "🆕 Criar Conta"])

        # ================ LOGIN ================
        with tab_login:
            st.subheader("Entre com suas credenciais")
            
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input(
                    "Email",
                    placeholder="seu@email.com",
                    key="login_email"
                )
                password = st.text_input(
                    "Senha",
                    type="password",
                    placeholder="••••••••",
                    key="login_pass"
                )
                
                submitted = st.form_submit_button("🔓 Entrar", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.warning("⚠️ Por favor, preencha email e senha.")
                    else:
                        try:
                            with st.spinner("Autenticando..."):
                                res = sign_in(email, password)
                                st.session_state.session = res
                                st.success("✅ Login realizado com sucesso!")
                                st.balloons()
                                st.rerun()
                                
                        except ValidationError as e:
                            st.error(f"❌ {str(e)}")
                            
                        except RateLimitError as e:
                            st.error(f"🚫 {str(e)}")
                            
                        except AuthenticationError as e:
                            st.error(f"❌ Credenciais inválidas. Verifique seu email e senha.")
                            logger.warning(f"Falha de autenticação: {e}")
                            
                        except Exception as e:
                            st.error("❌ Erro inesperado ao fazer login. Tente novamente.")
                            logger.error(f"Erro inesperado no login: {e}")
            
            st.caption("⚠️ Máximo de 5 tentativas a cada 15 minutos")

        # ================ CRIAR CONTA ================
        with tab_signup:
            st.subheader("Criar nova conta")
            st.info("ℹ️ **Requisitos de senha:**\n- Mínimo 8 caracteres\n- Letras maiúsculas e minúsculas\n- Pelo menos um número")
            
            with st.form("signup_form", clear_on_submit=False):
                new_email = st.text_input(
                    "Email",
                    placeholder="seu@email.com",
                    key="signup_email"
                )
                new_pass = st.text_input(
                    "Senha",
                    type="password",
                    placeholder="••••••••",
                    key="signup_pass"
                )
                confirm_pass = st.text_input(
                    "Confirmar Senha",
                    type="password",
                    placeholder="••••••••",
                    key="signup_confirm"
                )
                
                submitted = st.form_submit_button("🎉 Cadastrar", use_container_width=True)
                
                if submitted:
                    if not new_email or not new_pass:
                        st.warning("⚠️ Preencha todos os campos.")
                    elif new_pass != confirm_pass:
                        st.error("❌ As senhas não coincidem.")
                    else:
                        try:
                            with st.spinner("Criando conta..."):
                                res = sign_up(new_email, new_pass, confirm_pass)
                                
                                if res and res.user:
                                    st.success("✅ Conta criada com sucesso!")
                                    st.info("👉 Faça login na aba ao lado para começar.")
                                    st.balloons()
                                else:
                                    st.info("📧 Conta criada! Verifique seu email se a confirmação estiver ativada.")
                                    
                        except ValidationError as e:
                            st.error(f"❌ {str(e)}")
                            
                        except RateLimitError as e:
                            st.error(f"🚫 {str(e)}")
                            
                        except AuthenticationError as e:
                            error_msg = str(e)
                            if "already registered" in error_msg.lower() or "já cadastrado" in error_msg.lower():
                                st.error("❌ Este email já está cadastrado. Faça login na aba ao lado.")
                            else:
                                st.error(f"❌ Erro ao criar conta: {error_msg}")
                            logger.error(f"Erro no cadastro: {e}")
                            
                        except Exception as e:
                            st.error("❌ Erro inesperado ao criar conta. Tente novamente.")
                            logger.error(f"Erro inesperado no cadastro: {e}")
            
            st.caption("⚠️ Máximo de 3 tentativas por hora")

        st.stop()


# =====================================================
# 🔒 UTILITÁRIO DE PROTEÇÃO DE PÁGINAS
# =====================================================

def protected_page():
    """
    Chama esta função no topo de páginas que exigem login
    Redireciona para login se não autenticado
    """
    if not is_authenticated():
        st.warning("⚠️ Você precisa estar logado para acessar esta página.")
        st.info("👉 Por favor, volte à página inicial e faça login.")
        
        if st.button("🔙 Ir para Login"):
            st.switch_page("run_app.py")
        
        st.stop()
