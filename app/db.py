"""
Módulo de conexão e operações com Supabase
Inclui tratamento de erros, logging e retry logic
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, List, Any, Tuple
from app.utils import logger
import time


# =====================================================
# 🔧 EXCEÇÕES CUSTOMIZADAS
# =====================================================

class DatabaseError(Exception):
    """Erro genérico de banco de dados"""
    pass


class ConnectionError(DatabaseError):
    """Erro de conexão com banco"""
    pass


class QueryError(DatabaseError):
    """Erro ao executar query"""
    pass


# =====================================================
# 🔌 CONEXÃO COM SUPABASE
# =====================================================

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Cria e retorna cliente Supabase (cached)
    
    Returns:
        Cliente Supabase configurado
        
    Raises:
        ConnectionError: Se não conseguir conectar
    """
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ConnectionError("Credenciais do Supabase não configuradas")
        
        client = create_client(url, key)
        logger.info("Cliente Supabase criado com sucesso")
        return client
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente Supabase: {e}")
        raise ConnectionError(f"Falha ao conectar ao banco de dados: {e}")


def supa() -> Client:
    """
    Retorna cliente Supabase com sessão do usuário
    
    Returns:
        Cliente Supabase autenticado
    """
    try:
        client = get_supabase_client()
        
        # Vincula sessão do usuário logado
        sess = st.session_state.get("session", None)
        
        if sess:
            try:
                # Tenta diferentes formatos de sessão
                if hasattr(sess, "session") and sess.session:
                    access_token = sess.session.access_token
                    refresh_token = sess.session.refresh_token
                    client.auth.set_session(access_token, refresh_token)
                    logger.debug("Sessão vinculada ao cliente (formato 1)")
                    
                elif hasattr(sess, "access_token"):
                    client.auth.set_auth(sess.access_token)
                    logger.debug("Sessão vinculada ao cliente (formato 2)")
                    
            except Exception as e:
                logger.warning(f"Falha ao vincular sessão do usuário: {e}")
                # Não é crítico, continua sem sessão
        
        return client
        
    except ConnectionError:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao obter cliente: {e}")
        raise DatabaseError(f"Erro ao acessar banco de dados: {e}")


# =====================================================
# 🔄 RETRY LOGIC
# =====================================================

def retry_on_failure(func, max_attempts: int = 3, delay: float = 1.0):
    """
    Executa função com retry em caso de falha
    
    Args:
        func: Função a executar
        max_attempts: Número máximo de tentativas
        delay: Delay entre tentativas (segundos)
        
    Returns:
        Resultado da função
        
    Raises:
        Exception: Última exceção após todas as tentativas
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            logger.warning(f"Tentativa {attempt}/{max_attempts} falhou: {e}")
            
            if attempt < max_attempts:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
    
    logger.error(f"Todas as {max_attempts} tentativas falharam")
    raise last_exception


# =====================================================
# 📝 OPERAÇÕES CRUD
# =====================================================

def insert(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insere registro no banco
    
    Args:
        table: Nome da tabela
        data: Dados a inserir
        
    Returns:
        Registro inserido
        
    Raises:
        QueryError: Se falhar ao inserir
    """
    try:
        logger.info(f"Inserindo em {table}: {list(data.keys())}")
        
        def _insert():
            return supa().table(table).insert(data).execute()
        
        result = retry_on_failure(_insert)
        
        if result.data:
            logger.info(f"Registro inserido com sucesso em {table}")
            return result.data[0] if isinstance(result.data, list) else result.data
        else:
            raise QueryError(f"Nenhum dado retornado ao inserir em {table}")
            
    except Exception as e:
        logger.error(f"Erro ao inserir em {table}: {e}")
        raise QueryError(f"Falha ao inserir registro: {e}")


def upsert(table: str, data: Dict[str, Any], on: str = "id") -> Dict[str, Any]:
    """
    Insere ou atualiza registro
    
    Args:
        table: Nome da tabela
        data: Dados a inserir/atualizar
        on: Campo para conflito
        
    Returns:
        Registro inserido/atualizado
        
    Raises:
        QueryError: Se falhar ao fazer upsert
    """
    try:
        logger.info(f"Upsert em {table} (on={on}): {list(data.keys())}")
        
        def _upsert():
            return supa().table(table).upsert(data, on_conflict=on).execute()
        
        result = retry_on_failure(_upsert)
        
        if result.data:
            logger.info(f"Upsert realizado com sucesso em {table}")
            return result.data[0] if isinstance(result.data, list) else result.data
        else:
            raise QueryError(f"Nenhum dado retornado ao fazer upsert em {table}")
            
    except Exception as e:
        logger.error(f"Erro ao fazer upsert em {table}: {e}")
        raise QueryError(f"Falha ao inserir/atualizar registro: {e}")


def select(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    order: Optional[Tuple[str, str]] = ("created_at", "desc"),
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Busca registros no banco
    
    Args:
        table: Nome da tabela
        filters: Filtros a aplicar (campo: valor)
        order: Tupla (campo, direção) para ordenação
        limit: Limite de registros
        
    Returns:
        Lista de registros
        
    Raises:
        QueryError: Se falhar ao buscar
    """
    try:
        logger.debug(f"Buscando em {table} com filtros: {filters}")
        
        def _select():
            q = supa().table(table).select("*")
            
            # Aplica filtros
            if filters:
                for k, v in filters.items():
                    q = q.eq(k, v)
            
            # Aplica ordenação
            if order:
                q = q.order(order[0], desc=(order[1] == "desc"))
            
            # Aplica limite
            if limit:
                q = q.limit(limit)
            
            return q.execute()
        
        result = retry_on_failure(_select)
        
        data = result.data or []
        logger.info(f"Encontrados {len(data)} registros em {table}")
        return data
        
    except Exception as e:
        logger.error(f"Erro ao buscar em {table}: {e}")
        raise QueryError(f"Falha ao buscar registros: {e}")


def update(table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Atualiza registros no banco
    
    Args:
        table: Nome da tabela
        data: Dados a atualizar
        filters: Filtros para identificar registros
        
    Returns:
        Lista de registros atualizados
        
    Raises:
        QueryError: Se falhar ao atualizar
    """
    try:
        logger.info(f"Atualizando {table} com filtros: {filters}")
        
        def _update():
            q = supa().table(table).update(data)
            for k, v in filters.items():
                q = q.eq(k, v)
            return q.execute()
        
        result = retry_on_failure(_update)
        
        data_result = result.data or []
        logger.info(f"{len(data_result)} registros atualizados em {table}")
        return data_result
        
    except Exception as e:
        logger.error(f"Erro ao atualizar {table}: {e}")
        raise QueryError(f"Falha ao atualizar registros: {e}")


def delete(table: str, filters: Dict[str, Any]) -> int:
    """
    Remove registros do banco
    
    Args:
        table: Nome da tabela
        filters: Filtros para identificar registros
        
    Returns:
        Número de registros removidos
        
    Raises:
        QueryError: Se falhar ao deletar
    """
    try:
        logger.warning(f"Deletando de {table} com filtros: {filters}")
        
        if not filters:
            raise QueryError("Filtros são obrigatórios para delete (segurança)")
        
        def _delete():
            q = supa().table(table).delete()
            for k, v in filters.items():
                q = q.eq(k, v)
            return q.execute()
        
        result = retry_on_failure(_delete)
        
        count = len(result.data) if result.data else 0
        logger.info(f"{count} registros deletados de {table}")
        return count
        
    except Exception as e:
        logger.error(f"Erro ao deletar de {table}: {e}")
        raise QueryError(f"Falha ao remover registros: {e}")


# =====================================================
# 🔍 QUERIES ESPECIALIZADAS
# =====================================================

def select_paginated(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    order: Optional[Tuple[str, str]] = ("created_at", "desc"),
    page: int = 1,
    page_size: int = 50
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Busca registros com paginação
    
    Args:
        table: Nome da tabela
        filters: Filtros a aplicar
        order: Ordenação
        page: Número da página (começa em 1)
        page_size: Tamanho da página
        
    Returns:
        Tupla (registros, total_count)
    """
    try:
        # Calcula offset
        offset = (page - 1) * page_size
        
        logger.debug(f"Busca paginada em {table}: página {page}, tamanho {page_size}")
        
        def _select():
            q = supa().table(table).select("*", count="exact")
            
            if filters:
                for k, v in filters.items():
                    q = q.eq(k, v)
            
            if order:
                q = q.order(order[0], desc=(order[1] == "desc"))
            
            q = q.range(offset, offset + page_size - 1)
            
            return q.execute()
        
        result = retry_on_failure(_select)
        
        data = result.data or []
        total = result.count or 0
        
        logger.info(f"Página {page}: {len(data)} registros de {total} total")
        return data, total
        
    except Exception as e:
        logger.error(f"Erro ao buscar paginado de {table}: {e}")
        raise QueryError(f"Falha ao buscar registros paginados: {e}")


def count_records(table: str, filters: Optional[Dict[str, Any]] = None) -> int:
    """
    Conta registros na tabela
    
    Args:
        table: Nome da tabela
        filters: Filtros a aplicar
        
    Returns:
        Número de registros
    """
    try:
        def _count():
            q = supa().table(table).select("*", count="exact", head=True)
            
            if filters:
                for k, v in filters.items():
                    q = q.eq(k, v)
            
            return q.execute()
        
        result = retry_on_failure(_count)
        return result.count or 0
        
    except Exception as e:
        logger.error(f"Erro ao contar registros em {table}: {e}")
        return 0
