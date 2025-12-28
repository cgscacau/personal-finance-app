"""
Testes para modelos Pydantic
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError
from app.models import (
    UserLogin,
    UserSignup,
    Account,
    Transaction,
    CategoryRule,
    Budget,
    Goal
)


class TestUserLogin:
    """Testes para modelo UserLogin"""
    
    def test_valid_login(self):
        user = UserLogin(email="user@example.com", password="123456")
        assert user.email == "user@example.com"
        assert user.password == "123456"
    
    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserLogin(email="invalid-email", password="123456")
    
    def test_short_password(self):
        with pytest.raises(ValidationError):
            UserLogin(email="user@example.com", password="12345")


class TestUserSignup:
    """Testes para modelo UserSignup"""
    
    def test_valid_signup(self):
        user = UserSignup(email="user@example.com", password="Test1234")
        assert user.email == "user@example.com"
    
    def test_weak_password(self):
        with pytest.raises(ValidationError):
            UserSignup(email="user@example.com", password="weak")
    
    def test_no_uppercase(self):
        with pytest.raises(ValidationError):
            UserSignup(email="user@example.com", password="test1234")
    
    def test_no_number(self):
        with pytest.raises(ValidationError):
            UserSignup(email="user@example.com", password="TestTest")


class TestAccount:
    """Testes para modelo Account"""
    
    def test_valid_account(self):
        account = Account(
            user_id="user-123",
            name="Conta Corrente",
            account_type="checking",
            initial_balance=1000.0
        )
        assert account.name == "Conta Corrente"
        assert account.account_type == "checking"
    
    def test_invalid_account_type(self):
        with pytest.raises(ValidationError):
            Account(
                user_id="user-123",
                name="Conta",
                account_type="invalid",
                initial_balance=0
            )
    
    def test_empty_name(self):
        with pytest.raises(ValidationError):
            Account(
                user_id="user-123",
                name="",
                account_type="checking"
            )
    
    def test_currency_normalization(self):
        account = Account(
            user_id="user-123",
            name="Conta",
            account_type="checking",
            currency="brl"
        )
        assert account.currency == "BRL"


class TestTransaction:
    """Testes para modelo Transaction"""
    
    def test_valid_transaction(self):
        tx = Transaction(
            user_id="user-123",
            account_id="account-456",
            date=date(2024, 1, 15),
            description="Supermercado",
            amount=-150.50,
            transaction_type="expense"
        )
        assert tx.description == "Supermercado"
        assert tx.amount == -150.50
    
    def test_zero_amount(self):
        with pytest.raises(ValidationError):
            Transaction(
                user_id="user-123",
                account_id="account-456",
                date=date(2024, 1, 15),
                description="Test",
                amount=0,
                transaction_type="expense"
            )
    
    def test_short_description(self):
        with pytest.raises(ValidationError):
            Transaction(
                user_id="user-123",
                account_id="account-456",
                date=date(2024, 1, 15),
                description="AB",
                amount=100,
                transaction_type="income"
            )
    
    def test_future_date(self):
        from datetime import timedelta
        future_date = date.today() + timedelta(days=10)
        
        with pytest.raises(ValidationError):
            Transaction(
                user_id="user-123",
                account_id="account-456",
                date=future_date,
                description="Future transaction",
                amount=100,
                transaction_type="income"
            )
    
    def test_tags_deduplication(self):
        tx = Transaction(
            user_id="user-123",
            account_id="account-456",
            date=date(2024, 1, 15),
            description="Test",
            amount=100,
            transaction_type="income",
            tags=["tag1", "tag1", "tag2"]
        )
        assert len(tx.tags) == 2
        assert "tag1" in tx.tags
        assert "tag2" in tx.tags


class TestCategoryRule:
    """Testes para modelo CategoryRule"""
    
    def test_valid_rule(self):
        rule = CategoryRule(
            user_id="user-123",
            pattern="IFOOD|RAPPI",
            category="Alimentação",
            subcategory="Delivery",
            priority=10
        )
        assert rule.pattern == "IFOOD|RAPPI"
        assert rule.priority == 10
    
    def test_invalid_regex(self):
        with pytest.raises(ValidationError):
            CategoryRule(
                user_id="user-123",
                pattern="[invalid(regex",
                category="Test",
                priority=10
            )
    
    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            CategoryRule(
                user_id="user-123",
                pattern="TEST",
                category="Test",
                priority=0
            )
        
        with pytest.raises(ValidationError):
            CategoryRule(
                user_id="user-123",
                pattern="TEST",
                category="Test",
                priority=1001
            )


class TestBudget:
    """Testes para modelo Budget"""
    
    def test_valid_budget(self):
        budget = Budget(
            user_id="user-123",
            name="Orçamento Janeiro",
            category="Alimentação",
            amount=1500.00,
            period="monthly",
            start_date=date(2024, 1, 1)
        )
        assert budget.amount == 1500.00
        assert budget.period == "monthly"
    
    def test_negative_amount(self):
        with pytest.raises(ValidationError):
            Budget(
                user_id="user-123",
                name="Budget",
                category="Test",
                amount=-100,
                period="monthly",
                start_date=date(2024, 1, 1)
            )
    
    def test_invalid_end_date(self):
        with pytest.raises(ValidationError):
            Budget(
                user_id="user-123",
                name="Budget",
                category="Test",
                amount=1000,
                period="monthly",
                start_date=date(2024, 2, 1),
                end_date=date(2024, 1, 1)  # Before start_date
            )


class TestGoal:
    """Testes para modelo Goal"""
    
    def test_valid_goal(self):
        goal = Goal(
            user_id="user-123",
            name="Viagem",
            target_amount=10000.00,
            current_amount=2000.00,
            deadline=date(2024, 12, 31)
        )
        assert goal.target_amount == 10000.00
        assert goal.current_amount == 2000.00
    
    def test_negative_current_amount(self):
        with pytest.raises(ValidationError):
            Goal(
                user_id="user-123",
                name="Goal",
                target_amount=1000,
                current_amount=-100
            )
    
    def test_zero_target_amount(self):
        with pytest.raises(ValidationError):
            Goal(
                user_id="user-123",
                name="Goal",
                target_amount=0
            )
    
    def test_past_deadline(self):
        with pytest.raises(ValidationError):
            Goal(
                user_id="user-123",
                name="Goal",
                target_amount=1000,
                deadline=date(2020, 1, 1)
            )
