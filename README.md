# 💸 Gestor de Finanças Pessoais & Familiares

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37+-red.svg)](https://streamlit.io/)
[![Supabase](https://img.shields.io/badge/Supabase-Backend-green.svg)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Aplicativo completo para gestão de finanças pessoais e familiares com autenticação, importação de extratos bancários, categorização automática, dashboards interativos e muito mais.

---

## 🎯 **Funcionalidades**

### ✅ **Implementadas**

- **🔐 Autenticação Segura**
  - Login e cadastro via Supabase Auth
  - Validação de senhas fortes (maiúsculas, minúsculas, números)
  - Rate limiting (5 tentativas de login/15min, 3 cadastros/hora)
  - Proteção contra força bruta

- **📥 Importação de Extratos**
  - Suporte para múltiplos formatos: CSV, XLSX, OFX, PDF
  - Detecção automática de formato
  - Higienização e normalização de dados
  - Prevenção de duplicatas via hash

- **💼 Gestão de Contas**
  - Múltiplas contas bancárias
  - Tipos: Corrente, Poupança, Crédito, Investimento
  - Saldo inicial e controle de status

- **💰 Lançamentos Financeiros**
  - Registro manual de transações
  - Categorização por categoria e subcategoria
  - Tags personalizadas
  - Notas e observações
  - Transações recorrentes

- **🧠 Regras de Categorização**
  - Regras baseadas em regex
  - Priorização de regras
  - Aplicação automática em importações
  - Gerenciamento fácil via interface

- **📊 Dashboard Interativo**
  - Visão geral de receitas e despesas
  - Gráficos de fluxo de caixa
  - Análise por categoria (treemap, barras)
  - Filtros por período
  - Métricas em tempo real

- **🎯 Orçamentos e Metas**
  - Definição de orçamentos por categoria
  - Metas financeiras com deadline
  - Acompanhamento de progresso
  - Alertas de limite

- **⚙️ Configurações**
  - Personalização de categorias
  - Preferências de visualização
  - Gerenciamento de conta

---

## 🚀 **Início Rápido**

### **Pré-requisitos**

- Python 3.11 ou superior
- Conta no [Supabase](https://supabase.com/) (gratuita)
- Git

### **Instalação**

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/personal-finance-app.git
cd personal-finance-app
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**

Crie um arquivo `.streamlit/secrets.toml` na raiz do projeto:

```toml
# .streamlit/secrets.toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-chave-anonima-aqui"
```

**Como obter as credenciais do Supabase:**
1. Acesse [supabase.com](https://supabase.com/)
2. Crie um novo projeto (gratuito)
3. Vá em Settings > API
4. Copie a URL e a `anon` key

5. **Execute o aplicativo**
```bash
streamlit run run_app.py
```

O aplicativo abrirá automaticamente no navegador em `http://localhost:8501`

---

## 🗄️ **Configuração do Banco de Dados**

O aplicativo utiliza o Supabase (PostgreSQL) como backend. Você precisa criar as seguintes tabelas:

### **Tabela: accounts**
```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK (account_type IN ('checking', 'savings', 'credit', 'investment', 'other')),
    initial_balance NUMERIC DEFAULT 0,
    currency TEXT DEFAULT 'BRL',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);
```

### **Tabela: transactions**
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    description TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('income', 'expense', 'transfer')),
    category TEXT,
    subcategory TEXT,
    tags TEXT[],
    notes TEXT,
    is_recurring BOOLEAN DEFAULT false,
    hash_id TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_hash_id ON transactions(hash_id);
```

### **Tabela: category_rules**
```sql
CREATE TABLE category_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    pattern TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_category_rules_user_id ON category_rules(user_id);
CREATE INDEX idx_category_rules_priority ON category_rules(priority);
```

### **Tabela: budgets**
```sql
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    amount NUMERIC NOT NULL CHECK (amount > 0),
    period TEXT NOT NULL CHECK (period IN ('weekly', 'monthly', 'yearly')),
    start_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_budgets_user_id ON budgets(user_id);
```

### **Tabela: goals**
```sql
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    target_amount NUMERIC NOT NULL CHECK (target_amount > 0),
    current_amount NUMERIC DEFAULT 0 CHECK (current_amount >= 0),
    deadline DATE,
    is_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_goals_user_id ON goals(user_id);
```

### **Políticas de Segurança (RLS)**

Ative o Row Level Security em todas as tabelas:

```sql
-- Para cada tabela, execute:
ALTER TABLE <nome_tabela> ENABLE ROW LEVEL SECURITY;

-- Política de SELECT (usuário só vê seus dados)
CREATE POLICY "Users can view own <tabela>" ON <nome_tabela>
    FOR SELECT USING (auth.uid() = user_id);

-- Política de INSERT
CREATE POLICY "Users can insert own <tabela>" ON <nome_tabela>
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Política de UPDATE
CREATE POLICY "Users can update own <tabela>" ON <nome_tabela>
    FOR UPDATE USING (auth.uid() = user_id);

-- Política de DELETE
CREATE POLICY "Users can delete own <tabela>" ON <nome_tabela>
    FOR DELETE USING (auth.uid() = user_id);
```

---

## 📁 **Estrutura do Projeto**

```
personal-finance-app/
├── .streamlit/
│   ├── config.toml          # Configurações do Streamlit
│   └── secrets.toml         # Credenciais (não versionado)
├── app/
│   ├── __init__.py
│   ├── auth.py              # Autenticação e segurança
│   ├── charts.py            # Gráficos e visualizações
│   ├── db.py                # Operações de banco de dados
│   ├── models.py            # Modelos Pydantic
│   ├── parsing.py           # Parsing de arquivos
│   ├── rules.py             # Regras de categorização
│   └── utils.py             # Utilidades e helpers
├── pages/
│   ├── 1_📥_Importar_e_Higienizar.py
│   ├── 2_📊_Dashboard.py
│   ├── 3_💼_Contas_e_Lançamentos.py
│   ├── 4_🧠_Regras_de_Categorização.py
│   ├── 5_🎯_Orçamentos_e_Metas.py
│   └── 6_⚙️_Configurações.py
├── tests/
│   ├── __init__.py
│   ├── test_utils.py        # Testes de utilidades
│   └── test_models.py       # Testes de modelos
├── logs/                    # Logs da aplicação (criado automaticamente)
├── .env.example             # Exemplo de variáveis de ambiente
├── .gitignore
├── pytest.ini               # Configuração do pytest
├── requirements.txt         # Dependências Python
├── run_app.py              # Arquivo principal
└── README.md               # Este arquivo
```

---

## 🧪 **Testes**

O projeto inclui testes unitários usando pytest.

### **Executar todos os testes**
```bash
pytest
```

### **Executar com cobertura**
```bash
pytest --cov=app tests/
```

### **Executar testes específicos**
```bash
pytest tests/test_utils.py
pytest tests/test_models.py
```

---

## 🔒 **Segurança**

O aplicativo implementa diversas medidas de segurança:

- ✅ Autenticação via Supabase Auth (JWT)
- ✅ Rate limiting em login (5 tentativas/15min)
- ✅ Rate limiting em cadastro (3 tentativas/hora)
- ✅ Validação forte de senhas (Pydantic)
- ✅ Sanitização de inputs
- ✅ Row Level Security (RLS) no Supabase
- ✅ Logging de eventos de segurança
- ✅ Proteção contra SQL injection
- ✅ Hash único para transações (prevenção de duplicatas)

### **Boas Práticas**

- ❌ **NUNCA** commite o arquivo `.streamlit/secrets.toml`
- ❌ **NUNCA** exponha suas credenciais do Supabase
- ✅ Use senhas fortes (8+ caracteres, maiúsculas, minúsculas, números)
- ✅ Ative 2FA no Supabase se disponível
- ✅ Revise os logs regularmente

---

## 🛠️ **Desenvolvimento**

### **Código de Qualidade**

O projeto utiliza:
- **Black** para formatação
- **Ruff** para linting
- **Pydantic** para validação de dados
- **Loguru** para logging estruturado

### **Formatação de código**
```bash
black .
ruff check .
```

### **Convenções**

- Use type hints em todas as funções
- Docstrings no formato Google
- Commits seguindo Conventional Commits
- PRs com descrição detalhada

---

## 📊 **Tecnologias Utilizadas**

- **Frontend:** [Streamlit](https://streamlit.io/) - Framework Python para web apps
- **Backend:** [Supabase](https://supabase.com/) - PostgreSQL + Auth + Storage
- **Validação:** [Pydantic](https://pydantic.dev/) - Validação de dados
- **Visualização:** [Plotly](https://plotly.com/) - Gráficos interativos
- **Processamento:** [Pandas](https://pandas.pydata.org/) - Análise de dados
- **Logging:** [Loguru](https://github.com/Delgan/loguru) - Logging estruturado
- **Testes:** [Pytest](https://pytest.org/) - Framework de testes

---

## 📝 **Roadmap**

### **Versão 1.1** (Próxima)
- [ ] Exportação de relatórios em PDF
- [ ] Gráficos adicionais (sankey, sunburst)
- [ ] Modo escuro
- [ ] Notificações por email

### **Versão 1.2**
- [ ] Suporte multi-moeda
- [ ] Conversão automática de câmbio
- [ ] Importação via Open Banking
- [ ] API REST

### **Versão 2.0**
- [ ] Mobile app (React Native)
- [ ] Compartilhamento familiar
- [ ] IA para previsões financeiras
- [ ] Integração com bancos brasileiros

---

## 🤝 **Contribuindo**

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'feat: Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 💬 **Suporte**

Encontrou um bug ou tem alguma sugestão?

- 🐛 Abra uma [Issue](https://github.com/seu-usuario/personal-finance-app/issues)
- 💡 Inicie uma [Discussion](https://github.com/seu-usuario/personal-finance-app/discussions)
- 📧 Entre em contato: seu-email@example.com

---

## 🙏 **Agradecimentos**

- Comunidade Streamlit
- Equipe Supabase
- Todos os contribuidores

---

<div align="center">

**Desenvolvido com ❤️ e ☕ por [Seu Nome]**

⭐ Se este projeto te ajudou, considere dar uma estrela!

</div>
# Force update Mon Dec 29 09:01:18 UTC 2025
