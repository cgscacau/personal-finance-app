"""
Modelos de dados com validação usando Pydantic
"""

from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator, EmailStr
from decimal import Decimal


# =====================================================
# 👤 MODELOS DE USUÁRIO
# =====================================================

class UserLogin(BaseModel):
    """Modelo para login de usuário"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v.strip()) < 6:
            raise ValueError("Senha deve ter no mínimo 6 caracteres")
        return v.strip()


class UserSignup(BaseModel):
    """Modelo para cadastro de usuário"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: Optional[str] = None
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve conter ao menos uma letra maiúscula")
        if not any(c.islower() for c in v):
            raise ValueError("Senha deve conter ao menos uma letra minúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter ao menos um número")
        return v


# =====================================================
# 💳 MODELOS DE CONTA
# =====================================================

class Account(BaseModel):
    """Modelo para conta bancária"""
    id: Optional[str] = None
    user_id: str
    name: str = Field(..., min_length=1, max_length=100)
    account_type: Literal["checking", "savings", "credit", "investment", "other"]
    initial_balance: float = Field(default=0.0)
    currency: str = Field(default="BRL", max_length=3)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Nome da conta não pode estar vazio")
        return v.strip()
    
    @validator('currency')
    def validate_currency(cls, v):
        allowed = ["BRL", "USD", "EUR", "GBP"]
        if v.upper() not in allowed:
            raise ValueError(f"Moeda deve ser uma de: {', '.join(allowed)}")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "name": "Conta Corrente Banco do Brasil",
                "account_type": "checking",
                "initial_balance": 1000.00,
                "currency": "BRL",
                "is_active": True
            }
        }


# =====================================================
# 💰 MODELOS DE TRANSAÇÃO
# =====================================================

class Transaction(BaseModel):
    """Modelo para transação financeira"""
    id: Optional[str] = None
    user_id: str
    account_id: str
    date: date
    description: str = Field(..., min_length=1, max_length=500)
    amount: float
    transaction_type: Literal["income", "expense", "transfer"]
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)
    is_recurring: bool = Field(default=False)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    hash_id: Optional[str] = None
    
    @validator('description')
    def validate_description(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError("Descrição deve ter ao menos 3 caracteres")
        return v.strip()
    
    @validator('amount')
    def validate_amount(cls, v):
        if v == 0:
            raise ValueError("Valor não pode ser zero")
        return round(v, 2)
    
    @validator('date')
    def validate_date(cls, v):
        if v > date.today():
            raise ValueError("Data não pode ser no futuro (use transações planejadas)")
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Remove duplicatas e limita a 10 tags
            unique_tags = list(set(tag.strip() for tag in v if tag.strip()))
            return unique_tags[:10]
        return []
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "account_id": "account-456",
                "date": "2024-01-15",
                "description": "Supermercado Extra",
                "amount": -150.50,
                "transaction_type": "expense",
                "category": "Alimentação",
                "subcategory": "Supermercado",
                "tags": ["essencial", "mensal"]
            }
        }


class TransactionImport(BaseModel):
    """Modelo para importação de transações"""
    account_name: str = Field(..., min_length=1)
    file_type: Literal["csv", "xlsx", "ofx", "pdf"]
    transactions: list[dict]
    
    @validator('transactions')
    def validate_transactions(cls, v):
        if not v:
            raise ValueError("Lista de transações está vazia")
        if len(v) > 10000:
            raise ValueError("Máximo de 10.000 transações por importação")
        return v


# =====================================================
# 🎯 MODELOS DE REGRAS
# =====================================================

class CategoryRule(BaseModel):
    """Modelo para regra de categorização"""
    id: Optional[str] = None
    user_id: str
    pattern: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    priority: int = Field(default=100, ge=1, le=1000)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    
    @validator('pattern')
    def validate_pattern(cls, v):
        # Valida se é um regex válido
        import re
        try:
            re.compile(v, flags=re.IGNORECASE)
        except re.error:
            raise ValueError("Padrão regex inválido")
        return v.strip()
    
    @validator('priority')
    def validate_priority(cls, v):
        if v < 1 or v > 1000:
            raise ValueError("Prioridade deve estar entre 1 e 1000")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "pattern": "IFOOD|RAPPI|UBER.*EATS",
                "category": "Alimentação",
                "subcategory": "Delivery",
                "priority": 10
            }
        }


# =====================================================
# 💵 MODELOS DE ORÇAMENTO
# =====================================================

class Budget(BaseModel):
    """Modelo para orçamento"""
    id: Optional[str] = None
    user_id: str
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    period: Literal["weekly", "monthly", "yearly"]
    start_date: date
    end_date: Optional[date] = None
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Valor do orçamento deve ser maior que zero")
        return round(v, 2)
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and v < values['start_date']:
            raise ValueError("Data final não pode ser anterior à data inicial")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "name": "Orçamento Alimentação Janeiro",
                "category": "Alimentação",
                "amount": 1500.00,
                "period": "monthly",
                "start_date": "2024-01-01"
            }
        }


class Goal(BaseModel):
    """Modelo para meta financeira"""
    id: Optional[str] = None
    user_id: str
    name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(default=0.0, ge=0)
    deadline: Optional[date] = None
    is_completed: bool = Field(default=False)
    created_at: Optional[datetime] = None
    
    @validator('current_amount')
    def validate_current_amount(cls, v):
        if v < 0:
            raise ValueError("Valor atual não pode ser negativo")
        return round(v, 2)
    
    @validator('target_amount')
    def validate_target_amount(cls, v):
        if v <= 0:
            raise ValueError("Valor alvo deve ser maior que zero")
        return round(v, 2)
    
    @validator('deadline')
    def validate_deadline(cls, v):
        if v and v < date.today():
            raise ValueError("Prazo não pode ser no passado")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "name": "Viagem para Europa",
                "target_amount": 15000.00,
                "current_amount": 5000.00,
                "deadline": "2024-12-31"
            }
        }
