"""
Utilidades gerais do aplicativo
Inclui logging, validação, formatação e helpers
"""

import os
import sys
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Any
from loguru import logger

# =====================================================
# 🔧 CONFIGURAÇÃO DE LOGGING
# =====================================================

def setup_logger(log_level: str = "INFO"):
    """
    Configura o sistema de logging com loguru
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove handlers padrão
    logger.remove()
    
    # Console handler com formatação colorida
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # File handler com rotação
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logger.add(
        os.path.join(log_dir, "app_{time:YYYY-MM-DD}.log"),
        rotation="1 day",
        retention="30 days",
        compression="zip",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    return logger


# =====================================================
# 💰 FORMATAÇÃO DE VALORES
# =====================================================

def format_currency(value: float, currency: str = "R$") -> str:
    """
    Formata valor como moeda
    
    Args:
        value: Valor numérico
        currency: Símbolo da moeda
    
    Returns:
        String formatada (ex: "R$ 1.234,56")
    """
    try:
        if value < 0:
            return f"-{currency} {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{currency} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return f"{currency} 0,00"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formata valor como porcentagem
    
    Args:
        value: Valor numérico (0.15 = 15%)
        decimals: Casas decimais
    
    Returns:
        String formatada (ex: "15,00%")
    """
    try:
        return f"{value * 100:.{decimals}f}%".replace(".", ",")
    except (TypeError, ValueError):
        return "0,00%"


def parse_currency(value: str) -> Optional[float]:
    """
    Converte string de moeda em float
    
    Args:
        value: String no formato "R$ 1.234,56"
    
    Returns:
        Valor float ou None se inválido
    """
    try:
        # Remove símbolos e espaços
        clean = value.replace("R$", "").replace(" ", "").strip()
        # Substitui separadores brasileiros
        clean = clean.replace(".", "").replace(",", ".")
        return float(clean)
    except (ValueError, AttributeError):
        return None


# =====================================================
# 📅 FORMATAÇÃO DE DATAS
# =====================================================

def format_date(dt: Any, fmt: str = "%d/%m/%Y") -> str:
    """
    Formata data para string
    
    Args:
        dt: datetime, date ou string ISO
        fmt: Formato de saída
    
    Returns:
        Data formatada ou string vazia se inválido
    """
    try:
        if isinstance(dt, datetime):
            return dt.strftime(fmt)
        elif isinstance(dt, date):
            return dt.strftime(fmt)
        elif isinstance(dt, str):
            # Tenta converter de ISO
            parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            return parsed.strftime(fmt)
        return ""
    except (ValueError, AttributeError):
        return ""


def parse_date(value: str, formats: list = None) -> Optional[date]:
    """
    Converte string em objeto date
    
    Args:
        value: String de data
        formats: Lista de formatos a tentar (padrão: formatos brasileiros)
    
    Returns:
        Objeto date ou None se inválido
    """
    if formats is None:
        formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]
    
    for fmt in formats:
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    
    return None


# =====================================================
# ✅ VALIDAÇÃO
# =====================================================

def is_valid_email(email: str) -> bool:
    """
    Valida formato de email (validação básica)
    
    Args:
        email: String de email
    
    Returns:
        True se válido
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_string(text: str, max_length: int = 500) -> str:
    """
    Remove caracteres perigosos de string
    
    Args:
        text: String a sanitizar
        max_length: Comprimento máximo
    
    Returns:
        String sanitizada
    """
    if not text:
        return ""
    
    # Remove caracteres de controle
    sanitized = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")
    
    # Limita tamanho
    return sanitized[:max_length].strip()


# =====================================================
# 🔐 SEGURANÇA
# =====================================================

def hash_transaction_id(*fields) -> str:
    """
    Gera hash único para transação
    
    Args:
        *fields: Campos para gerar hash
    
    Returns:
        Hash SHA256
    """
    import hashlib
    content = "|".join(str(f) for f in fields)
    return hashlib.sha256(content.encode()).hexdigest()


# =====================================================
# 📊 ANÁLISE DE DADOS
# =====================================================

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calcula variação percentual
    
    Args:
        old_value: Valor anterior
        new_value: Valor novo
    
    Returns:
        Variação percentual (0.15 = 15%)
    """
    if old_value == 0:
        return 0.0 if new_value == 0 else float('inf')
    
    return (new_value - old_value) / abs(old_value)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Divisão segura que evita divisão por zero
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor padrão se divisão por zero
    
    Returns:
        Resultado da divisão ou valor padrão
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


# Inicializa logger
log_level = os.getenv("LOG_LEVEL", "INFO")
logger = setup_logger(log_level)
