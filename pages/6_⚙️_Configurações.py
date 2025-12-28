import streamlit as st
import pandas as pd
from datetime import datetime
from app.auth import require_login, current_user_id
from app.db import supa

st.title("⚙️ Administração do Sistema")
require_login()
uid = current_user_id()

# Abas principais
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Resumo",
    "🏦 Contas", 
    "💰 Transações",
    "🧠 Regras",
    "🎯 Orçamentos",
    "🏆 Metas"
])

# ============================================================
# TAB 1: RESUMO GERAL
# ============================================================
with tab1:
    st.header("📊 Visão Geral dos Dados")
    
    col1, col2, col3 = st.columns(3)
    
    # Estatísticas
    accounts = supa().table("accounts").select("*").eq("user_id", uid).execute().data
    transactions = supa().table("transactions").select("*").eq("user_id", uid).execute().data
    rules = supa().table("category_rules").select("*").eq("user_id", uid).execute().data
    budgets = supa().table("budgets").select("*").eq("user_id", uid).execute().data
    goals = supa().table("goals").select("*").eq("user_id", uid).execute().data
    
    with col1:
        st.metric("🏦 Contas", len(accounts))
        st.metric("💰 Transações", len(transactions))
    
    with col2:
        st.metric("🧠 Regras", len(rules))
        st.metric("🎯 Orçamentos", len(budgets))
    
    with col3:
        st.metric("🏆 Metas", len(goals))
        
        if transactions:
            total = sum(t.get("amount", 0) for t in transactions)
            st.metric("💵 Saldo Total", f"R$ {total:,.2f}")
    
    st.divider()
    
    # Gráfico de transações por categoria
    if transactions:
        st.subheader("📈 Transações por Categoria")
        df_trans = pd.DataFrame(transactions)
        if "category" in df_trans.columns:
            cat_count = df_trans["category"].value_counts()
            st.bar_chart(cat_count)

# ============================================================
# TAB 2: GERENCIAR CONTAS
# ============================================================
with tab2:
    st.header("🏦 Gerenciar Contas")
    
    if not accounts:
        st.info("📭 Nenhuma conta cadastrada ainda.")
    else:
        for acc in accounts:
            with st.expander(f"🏦 {acc['name']} ({acc['account_type']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID:** `{acc['id']}`")
                    st.write(f"**Tipo:** {acc['account_type']}")
                    st.write(f"**Instituição:** {acc.get('institution', 'N/A')}")
                    st.write(f"**Saldo Inicial:** R$ {acc.get('initial_balance', 0):,.2f}")
                    st.write(f"**Moeda:** {acc.get('currency', 'BRL')}")
                    st.write(f"**Ativa:** {'✅ Sim' if acc.get('is_active', True) else '❌ Não'}")
                    st.write(f"**Criada em:** {acc.get('created_at', 'N/A')[:10]}")
                
                with col2:
                    # Botão de editar
                    if st.button("✏️ Editar", key=f"edit_acc_{acc['id']}"):
                        st.session_state[f"editing_acc_{acc['id']}"] = True
                    
                    # Botão de deletar
                    if st.button("🗑️ Deletar", key=f"del_acc_{acc['id']}", type="secondary"):
                        st.session_state[f"confirm_del_acc_{acc['id']}"] = True
                
                # Formulário de edição
                if st.session_state.get(f"editing_acc_{acc['id']}", False):
                    with st.form(f"edit_form_acc_{acc['id']}"):
                        st.subheader("✏️ Editar Conta")
                        new_name = st.text_input("Nome", acc['name'])
                        new_inst = st.text_input("Instituição", acc.get('institution', ''))
                        new_type = st.selectbox("Tipo", 
                            ["checking", "savings", "credit", "investment", "other"],
                            index=["checking", "savings", "credit", "investment", "other"].index(acc['account_type'])
                        )
                        new_balance = st.number_input("Saldo Inicial", value=float(acc.get('initial_balance', 0)), step=100.0)
                        new_active = st.checkbox("Conta Ativa", value=acc.get('is_active', True))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Salvar", type="primary"):
                                supa().table("accounts").update({
                                    "name": new_name,
                                    "institution": new_inst,
                                    "account_type": new_type,
                                    "initial_balance": new_balance,
                                    "is_active": new_active
                                }).eq("id", acc['id']).execute()
                                st.success("✅ Conta atualizada!")
                                del st.session_state[f"editing_acc_{acc['id']}"]
                                st.rerun()
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar"):
                                del st.session_state[f"editing_acc_{acc['id']}"]
                                st.rerun()
                
                # Confirmação de deleção
                if st.session_state.get(f"confirm_del_acc_{acc['id']}", False):
                    st.warning("⚠️ **ATENÇÃO:** Esta ação irá deletar a conta e TODAS as transações associadas!")
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("✅ Confirmar Exclusão", key=f"confirm_yes_acc_{acc['id']}", type="primary"):
                            supa().table("accounts").delete().eq("id", acc['id']).execute()
                            st.success("✅ Conta deletada com sucesso!")
                            del st.session_state[f"confirm_del_acc_{acc['id']}"]
                            st.rerun()
                    
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"confirm_no_acc_{acc['id']}"):
                            del st.session_state[f"confirm_del_acc_{acc['id']}"]
                            st.rerun()

# ============================================================
# TAB 3: GERENCIAR TRANSAÇÕES
# ============================================================
with tab3:
    st.header("💰 Gerenciar Transações")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_desc = st.text_input("🔍 Buscar por descrição", "")
    
    with col2:
        if accounts:
            account_filter = st.selectbox("Filtrar por conta", 
                ["Todas"] + [acc['name'] for acc in accounts]
            )
        else:
            account_filter = "Todas"
    
    with col3:
        category_filter = st.text_input("Filtrar por categoria", "")
    
    # Filtrar transações
    filtered_trans = transactions
    
    if search_desc:
        filtered_trans = [t for t in filtered_trans if search_desc.lower() in t.get('description', '').lower()]
    
    if account_filter != "Todas" and accounts:
        acc_id = next((a['id'] for a in accounts if a['name'] == account_filter), None)
        if acc_id:
            filtered_trans = [t for t in filtered_trans if t.get('account_id') == acc_id]
    
    if category_filter:
        filtered_trans = [t for t in filtered_trans if category_filter.lower() in t.get('category', '').lower()]
    
    st.write(f"**Total:** {len(filtered_trans)} transações")
    
    if not filtered_trans:
        st.info("📭 Nenhuma transação encontrada.")
    else:
        # Ordenar por data (mais recente primeiro)
        filtered_trans = sorted(filtered_trans, key=lambda x: x.get('date', ''), reverse=True)
        
        # Paginação
        items_per_page = 10
        total_pages = (len(filtered_trans) - 1) // items_per_page + 1
        
        page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1)
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_trans = filtered_trans[start_idx:end_idx]
        
        for trans in page_trans:
            amount = trans.get('amount', 0)
            is_income = amount > 0
            emoji = "💰" if is_income else "💸"
            color = "green" if is_income else "red"
            
            with st.expander(f"{emoji} {trans.get('description', 'N/A')} - R$ {abs(amount):,.2f}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID:** `{trans['id']}`")
                    st.write(f"**Data:** {trans.get('date', 'N/A')}")
                    st.write(f"**Descrição:** {trans.get('description', 'N/A')}")
                    st.write(f"**Valor:** ::{color}[R$ {amount:,.2f}]")
                    st.write(f"**Tipo:** {trans.get('transaction_type', 'N/A')}")
                    st.write(f"**Categoria:** {trans.get('category', 'N/A')}")
                    st.write(f"**Subcategoria:** {trans.get('subcategory', 'N/A')}")
                    
                    # Buscar nome da conta
                    acc_name = "N/A"
                    if accounts and trans.get('account_id'):
                        acc = next((a for a in accounts if a['id'] == trans.get('account_id')), None)
                        if acc:
                            acc_name = acc['name']
                    st.write(f"**Conta:** {acc_name}")
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_trans_{trans['id']}"):
                        st.session_state[f"editing_trans_{trans['id']}"] = True
                    
                    if st.button("🗑️ Deletar", key=f"del_trans_{trans['id']}", type="secondary"):
                        st.session_state[f"confirm_del_trans_{trans['id']}"] = True
                
                # Formulário de edição
                if st.session_state.get(f"editing_trans_{trans['id']}", False):
                    with st.form(f"edit_form_trans_{trans['id']}"):
                        st.subheader("✏️ Editar Transação")
                        
                        new_date = st.date_input("Data", value=pd.to_datetime(trans.get('date', datetime.now())))
                        new_desc = st.text_input("Descrição", trans.get('description', ''))
                        new_amount = st.number_input("Valor", value=float(trans.get('amount', 0)), step=10.0)
                        new_category = st.text_input("Categoria", trans.get('category', ''))
                        new_subcategory = st.text_input("Subcategoria", trans.get('subcategory', ''))
                        new_notes = st.text_area("Notas", trans.get('notes', ''))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Salvar", type="primary"):
                                supa().table("transactions").update({
                                    "date": str(new_date),
                                    "description": new_desc,
                                    "amount": new_amount,
                                    "transaction_type": "income" if new_amount > 0 else "expense",
                                    "category": new_category,
                                    "subcategory": new_subcategory,
                                    "notes": new_notes
                                }).eq("id", trans['id']).execute()
                                st.success("✅ Transação atualizada!")
                                del st.session_state[f"editing_trans_{trans['id']}"]
                                st.rerun()
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar"):
                                del st.session_state[f"editing_trans_{trans['id']}"]
                                st.rerun()
                
                # Confirmação de deleção
                if st.session_state.get(f"confirm_del_trans_{trans['id']}", False):
                    st.warning("⚠️ Tem certeza que deseja deletar esta transação?")
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("✅ Confirmar", key=f"confirm_yes_trans_{trans['id']}", type="primary"):
                            supa().table("transactions").delete().eq("id", trans['id']).execute()
                            st.success("✅ Transação deletada!")
                            del st.session_state[f"confirm_del_trans_{trans['id']}"]
                            st.rerun()
                    
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"confirm_no_trans_{trans['id']}"):
                            del st.session_state[f"confirm_del_trans_{trans['id']}"]
                            st.rerun()

# ============================================================
# TAB 4: GERENCIAR REGRAS
# ============================================================
with tab4:
    st.header("🧠 Gerenciar Regras de Categorização")
    
    if not rules:
        st.info("📭 Nenhuma regra cadastrada ainda.")
    else:
        for rule in sorted(rules, key=lambda x: x.get('priority', 999)):
            with st.expander(f"🧠 {rule.get('pattern', 'N/A')} → {rule.get('category', 'N/A')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Padrão:** `{rule.get('pattern', 'N/A')}`")
                    st.write(f"**Categoria:** {rule.get('category', 'N/A')}")
                    st.write(f"**Subcategoria:** {rule.get('subcategory', 'N/A')}")
                    st.write(f"**Prioridade:** {rule.get('priority', 'N/A')}")
                    st.write(f"**Ativa:** {'✅ Sim' if rule.get('is_active', True) else '❌ Não'}")
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_rule_{rule['id']}"):
                        st.session_state[f"editing_rule_{rule['id']}"] = True
                    
                    if st.button("🗑️ Deletar", key=f"del_rule_{rule['id']}", type="secondary"):
                        supa().table("category_rules").delete().eq("id", rule['id']).execute()
                        st.success("✅ Regra deletada!")
                        st.rerun()
                
                # Formulário de edição
                if st.session_state.get(f"editing_rule_{rule['id']}", False):
                    with st.form(f"edit_form_rule_{rule['id']}"):
                        st.subheader("✏️ Editar Regra")
                        
                        new_pattern = st.text_input("Padrão (regex)", rule.get('pattern', ''))
                        new_category = st.text_input("Categoria", rule.get('category', ''))
                        new_subcategory = st.text_input("Subcategoria", rule.get('subcategory', ''))
                        new_priority = st.number_input("Prioridade", value=int(rule.get('priority', 0)), min_value=0, max_value=100)
                        new_active = st.checkbox("Regra Ativa", value=rule.get('is_active', True))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Salvar", type="primary"):
                                supa().table("category_rules").update({
                                    "pattern": new_pattern,
                                    "category": new_category,
                                    "subcategory": new_subcategory,
                                    "priority": new_priority,
                                    "is_active": new_active
                                }).eq("id", rule['id']).execute()
                                st.success("✅ Regra atualizada!")
                                del st.session_state[f"editing_rule_{rule['id']}"]
                                st.rerun()
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar"):
                                del st.session_state[f"editing_rule_{rule['id']}"]
                                st.rerun()

# ============================================================
# TAB 5: GERENCIAR ORÇAMENTOS
# ============================================================
with tab5:
    st.header("🎯 Gerenciar Orçamentos")
    
    if not budgets:
        st.info("📭 Nenhum orçamento cadastrado ainda.")
    else:
        for budget in budgets:
            with st.expander(f"🎯 {budget.get('name', 'N/A')} - {budget.get('category', 'N/A')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Nome:** {budget.get('name', 'N/A')}")
                    st.write(f"**Categoria:** {budget.get('category', 'N/A')}")
                    st.write(f"**Valor:** R$ {budget.get('amount', 0):,.2f}")
                    st.write(f"**Período:** {budget.get('period', 'N/A')}")
                    st.write(f"**Início:** {budget.get('start_date', 'N/A')}")
                    st.write(f"**Fim:** {budget.get('end_date', 'N/A')}")
                    st.write(f"**Ativo:** {'✅ Sim' if budget.get('is_active', True) else '❌ Não'}")
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_budget_{budget['id']}"):
                        st.session_state[f"editing_budget_{budget['id']}"] = True
                    
                    if st.button("🗑️ Deletar", key=f"del_budget_{budget['id']}", type="secondary"):
                        supa().table("budgets").delete().eq("id", budget['id']).execute()
                        st.success("✅ Orçamento deletado!")
                        st.rerun()
                
                # Formulário de edição
                if st.session_state.get(f"editing_budget_{budget['id']}", False):
                    with st.form(f"edit_form_budget_{budget['id']}"):
                        st.subheader("✏️ Editar Orçamento")
                        
                        new_name = st.text_input("Nome", budget.get('name', ''))
                        new_category = st.text_input("Categoria", budget.get('category', ''))
                        new_amount = st.number_input("Valor", value=float(budget.get('amount', 0)), step=100.0, min_value=0.01)
                        new_period = st.selectbox("Período", 
                            ["weekly", "monthly", "yearly"],
                            index=["weekly", "monthly", "yearly"].index(budget.get('period', 'monthly'))
                        )
                        new_start = st.date_input("Início", value=pd.to_datetime(budget.get('start_date', datetime.now())))
                        new_end = st.date_input("Fim", value=pd.to_datetime(budget.get('end_date', datetime.now())) if budget.get('end_date') else None)
                        new_active = st.checkbox("Orçamento Ativo", value=budget.get('is_active', True))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Salvar", type="primary"):
                                supa().table("budgets").update({
                                    "name": new_name,
                                    "category": new_category,
                                    "amount": new_amount,
                                    "period": new_period,
                                    "start_date": str(new_start),
                                    "end_date": str(new_end) if new_end else None,
                                    "is_active": new_active
                                }).eq("id", budget['id']).execute()
                                st.success("✅ Orçamento atualizado!")
                                del st.session_state[f"editing_budget_{budget['id']}"]
                                st.rerun()
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar"):
                                del st.session_state[f"editing_budget_{budget['id']}"]
                                st.rerun()

# ============================================================
# TAB 6: GERENCIAR METAS
# ============================================================
with tab6:
    st.header("🏆 Gerenciar Metas")
    
    if not goals:
        st.info("📭 Nenhuma meta cadastrada ainda.")
    else:
        for goal in goals:
            progress = (goal.get('current_amount', 0) / goal.get('target_amount', 1)) * 100 if goal.get('target_amount', 0) > 0 else 0
            
            with st.expander(f"🏆 {goal.get('name', 'N/A')} - {progress:.1f}% concluído"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Nome:** {goal.get('name', 'N/A')}")
                    st.write(f"**Meta:** R$ {goal.get('target_amount', 0):,.2f}")
                    st.write(f"**Atual:** R$ {goal.get('current_amount', 0):,.2f}")
                    st.write(f"**Progresso:** {progress:.1f}%")
                    st.progress(min(progress / 100, 1.0))
                    st.write(f"**Prazo:** {goal.get('deadline', 'N/A')}")
                    st.write(f"**Concluída:** {'✅ Sim' if goal.get('is_completed', False) else '❌ Não'}")
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_goal_{goal['id']}"):
                        st.session_state[f"editing_goal_{goal['id']}"] = True
                    
                    if st.button("🗑️ Deletar", key=f"del_goal_{goal['id']}", type="secondary"):
                        supa().table("goals").delete().eq("id", goal['id']).execute()
                        st.success("✅ Meta deletada!")
                        st.rerun()
                
                # Formulário de edição
                if st.session_state.get(f"editing_goal_{goal['id']}", False):
                    with st.form(f"edit_form_goal_{goal['id']}"):
                        st.subheader("✏️ Editar Meta")
                        
                        new_name = st.text_input("Nome", goal.get('name', ''))
                        new_target = st.number_input("Meta", value=float(goal.get('target_amount', 0)), step=100.0, min_value=0.01)
                        new_current = st.number_input("Valor Atual", value=float(goal.get('current_amount', 0)), step=100.0, min_value=0.0)
                        new_deadline = st.date_input("Prazo", value=pd.to_datetime(goal.get('deadline', datetime.now())) if goal.get('deadline') else None)
                        new_completed = st.checkbox("Meta Concluída", value=goal.get('is_completed', False))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Salvar", type="primary"):
                                supa().table("goals").update({
                                    "name": new_name,
                                    "target_amount": new_target,
                                    "current_amount": new_current,
                                    "deadline": str(new_deadline) if new_deadline else None,
                                    "is_completed": new_completed
                                }).eq("id", goal['id']).execute()
                                st.success("✅ Meta atualizada!")
                                del st.session_state[f"editing_goal_{goal['id']}"]
                                st.rerun()
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar"):
                                del st.session_state[f"editing_goal_{goal['id']}"]
                                st.rerun()
