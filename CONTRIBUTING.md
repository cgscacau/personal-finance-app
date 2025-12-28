# 🤝 Guia de Contribuição

Obrigado por considerar contribuir para o Gestor de Finanças Pessoais! 🎉

Este documento fornece diretrizes para contribuir com o projeto.

---

## 📋 **Código de Conduta**

Este projeto e todos os seus participantes devem seguir nosso Código de Conduta. Ao participar, você concorda em manter um ambiente respeitoso e acolhedor.

### **Comportamentos Esperados**
- ✅ Seja respeitoso e inclusivo
- ✅ Aceite críticas construtivas
- ✅ Foque no que é melhor para a comunidade
- ✅ Mostre empatia com outros membros

### **Comportamentos Inaceitáveis**
- ❌ Linguagem ou imagens ofensivas
- ❌ Comentários insultuosos ou depreciativos
- ❌ Assédio público ou privado
- ❌ Publicação de informações privadas sem permissão

---

## 🚀 **Como Contribuir**

### **1. Reportar Bugs**

Encontrou um bug? Ajude-nos a corrigi-lo!

1. Verifique se o bug já não foi reportado nas [Issues](https://github.com/seu-usuario/personal-finance-app/issues)
2. Se não foi, abra uma nova issue com:
   - Título claro e descritivo
   - Passos para reproduzir o problema
   - Comportamento esperado vs. atual
   - Screenshots (se aplicável)
   - Versão do Python e SO

**Template de Bug Report:**
```markdown
**Descrição do Bug**
Uma descrição clara do que está acontecendo.

**Passos para Reproduzir**
1. Vá para '...'
2. Clique em '...'
3. Veja o erro

**Comportamento Esperado**
O que deveria acontecer.

**Screenshots**
Se aplicável, adicione screenshots.

**Ambiente:**
- OS: [ex: Ubuntu 22.04]
- Python: [ex: 3.11.5]
- Navegador: [ex: Chrome 120]
```

### **2. Sugerir Melhorias**

Tem uma ideia? Compartilhe conosco!

1. Verifique se a sugestão já não existe nas [Discussions](https://github.com/seu-usuario/personal-finance-app/discussions)
2. Abra uma nova discussion com:
   - Descrição clara da funcionalidade
   - Por que seria útil
   - Como deveria funcionar
   - Exemplos de uso

### **3. Contribuir com Código**

#### **Setup do Ambiente**

1. **Fork o repositório**
```bash
# Clique em "Fork" no GitHub
```

2. **Clone seu fork**
```bash
git clone https://github.com/SEU-USUARIO/personal-finance-app.git
cd personal-finance-app
```

3. **Adicione o repositório original como upstream**
```bash
git remote add upstream https://github.com/USUARIO-ORIGINAL/personal-finance-app.git
```

4. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

5. **Instale as dependências**
```bash
pip install -r requirements.txt
```

#### **Fluxo de Trabalho**

1. **Crie uma branch para sua feature**
```bash
git checkout -b feature/nome-da-feature
# ou
git checkout -b fix/nome-do-bug
```

2. **Faça suas alterações**
   - Escreva código limpo e legível
   - Adicione docstrings
   - Adicione testes
   - Siga as convenções do projeto

3. **Execute os testes**
```bash
pytest
pytest --cov=app tests/
```

4. **Formate o código**
```bash
black .
ruff check .
```

5. **Commit suas mudanças**
```bash
git add .
git commit -m "tipo(escopo): mensagem"
```

**Tipos de commit:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação (não afeta código)
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Manutenção

**Exemplos:**
```bash
git commit -m "feat(auth): adiciona validação de senha forte"
git commit -m "fix(dashboard): corrige cálculo de saldo"
git commit -m "docs(readme): atualiza instruções de instalação"
```

6. **Push para seu fork**
```bash
git push origin feature/nome-da-feature
```

7. **Abra um Pull Request**
   - Vá para o GitHub e clique em "New Pull Request"
   - Selecione sua branch
   - Preencha o template do PR
   - Aguarde o review

---

## 📝 **Padrões de Código**

### **Python**

- Use **Python 3.11+**
- Siga **PEP 8**
- Use **type hints** sempre que possível
- Docstrings no formato **Google**

**Exemplo:**
```python
def calculate_total(transactions: list[Transaction], filter_type: str = "all") -> float:
    """
    Calcula o total de transações.
    
    Args:
        transactions: Lista de transações
        filter_type: Tipo de filtro ('income', 'expense', 'all')
    
    Returns:
        Total calculado
    
    Raises:
        ValueError: Se filter_type inválido
    """
    if filter_type not in ["income", "expense", "all"]:
        raise ValueError(f"filter_type inválido: {filter_type}")
    
    # Implementação...
    return total
```

### **Estrutura de Arquivos**

```python
# 1. Imports stdlib
import os
from datetime import datetime

# 2. Imports third-party
import pandas as pd
import streamlit as st

# 3. Imports locais
from app.models import Transaction
from app.utils import logger

# 4. Constantes
DEFAULT_CURRENCY = "BRL"

# 5. Classes e funções
class MyClass:
    pass

def my_function():
    pass
```

### **Naming Conventions**

- **Variáveis e funções:** `snake_case`
- **Classes:** `PascalCase`
- **Constantes:** `UPPER_SNAKE_CASE`
- **Privado:** `_prefixo_underscore`

### **Comentários**

- Escreva comentários claros e úteis
- Evite comentários óbvios
- Use docstrings para funções e classes
- Comente "por quê", não "o quê"

**Bom:**
```python
# Aplica desconto progressivo baseado no volume de transações
# para incentivar uso da plataforma
discount = calculate_volume_discount(transaction_count)
```

**Ruim:**
```python
# Define discount como resultado da função
discount = calculate_volume_discount(transaction_count)
```

---

## 🧪 **Testes**

### **Todos os PRs devem incluir testes!**

- Testes unitários para novas funções
- Testes de integração para fluxos completos
- Cobertura mínima de **80%**

**Estrutura de teste:**
```python
import pytest
from app.utils import format_currency

class TestFormatCurrency:
    """Testes para formatação de moeda"""
    
    def test_format_positive_value(self):
        assert format_currency(1234.56) == "R$ 1.234,56"
    
    def test_format_negative_value(self):
        assert format_currency(-1234.56) == "-R$ 1.234,56"
    
    def test_format_zero(self):
        assert format_currency(0) == "R$ 0,00"
```

---

## 📚 **Documentação**

- Atualize o README.md se necessário
- Adicione docstrings em funções novas
- Comente código complexo
- Atualize CHANGELOG.md

---

## 🔍 **Processo de Review**

Seu PR será revisado por um mantenedor. O processo inclui:

1. **Verificação automática** (CI/CD)
   - Testes passando
   - Linting sem erros
   - Cobertura adequada

2. **Review manual**
   - Qualidade do código
   - Aderência aos padrões
   - Clareza e documentação

3. **Feedback**
   - Sugestões de melhoria
   - Solicitação de mudanças
   - Aprovação

### **O que esperamos:**

✅ Código limpo e legível
✅ Testes passando
✅ Documentação atualizada
✅ Commits bem escritos
✅ Sem código comentado
✅ Sem debugging prints

### **Tempo de resposta:**

- Issues: 2-3 dias úteis
- PRs: 3-5 dias úteis

---

## 🎯 **Áreas que Precisam de Ajuda**

Procurando por onde começar? Estas áreas sempre precisam de contribuições:

- 📝 **Documentação:** Tutoriais, exemplos, traduções
- 🐛 **Bugs:** Issues marcadas com `good first issue`
- 🧪 **Testes:** Aumentar cobertura de testes
- 🎨 **UI/UX:** Melhorias de interface
- 🌐 **Internacionalização:** Traduções
- 📊 **Features:** Issues marcadas com `enhancement`

---

## 💡 **Dicas para Contribuidores**

1. **Comece pequeno:** Pequenas melhorias são mais fáceis de revisar
2. **Pergunte primeiro:** Abra uma issue antes de grandes mudanças
3. **Seja paciente:** Reviews levam tempo
4. **Aprenda com feedback:** Use comentários para melhorar
5. **Divirta-se:** Contribuir deve ser prazeroso!

---

## 📞 **Precisa de Ajuda?**

- 💬 [Discussions](https://github.com/seu-usuario/personal-finance-app/discussions)
- 📧 Email: seu-email@example.com
- 🐦 Twitter: @seu_usuario

---

## 🙏 **Agradecimentos**

Obrigado por dedicar seu tempo para melhorar este projeto!

Toda contribuição, não importa o tamanho, é valiosa e apreciada. 💚

---

<div align="center">

**Happy Coding! 🚀**

</div>
