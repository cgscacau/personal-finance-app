import streamlit as st
import pandas as pd
from app.auth import require_login, current_user_id
from app.db import supa, insert, select
from app.parsing import from_csv, from_xlsx, from_pdf, from_ofx
from app.rules import apply_rules

st.title("📥 Importar & Higienizar Extratos")
require_login()
uid = current_user_id()

# selecionar/crear conta
accounts = select("accounts", {"user_id": uid})
acc_names = [a["name"] for a in accounts]
acc = st.selectbox("Conta", options=acc_names + ["➕ Criar nova conta"])
if acc == "➕ Criar nova conta":
    with st.form("new_acc"):
        name = st.text_input("Nome da conta")
        inst = st.text_input("Instituição (opcional)")
        tp = st.selectbox("Tipo", ["checking","savings","credit","investment","other"])
        s = st.form_submit_button("Criar")
        if s and name:
            insert("accounts", {"user_id": uid, "name": name, "institution": inst, "account_type": tp})
            st.success("Conta criada. Recarregue a página."); st.stop()
else:
    account_name = acc

uploaded = st.file_uploader("Envie extratos (CSV, XLSX, OFX, PDF)", accept_multiple_files=True)
if uploaded:
    frames=[]
    for f in uploaded:
        data = f.read()
        ext = f.name.lower().split(".")[-1]
        
        st.info(f"📄 Processando: **{f.name}** ({len(data)} bytes)")
        
        try:
            if ext in ["csv"]:
                df = from_csv(data, account_name)
            elif ext in ["xlsx","xls"]:
                df = from_xlsx(data, account_name)
            elif ext in ["ofx"]:
                df = from_ofx(data, account_name)
            elif ext in ["pdf"]:
                df = from_pdf(data, account_name)
            else:
                st.warning(f"Formato não suportado: {f.name}")
                continue
            
            st.success(f"✅ {len(df)} transações encontradas em {f.name}")
            
            # Mostrar preview dos dados brutos
            with st.expander(f"🔍 Ver dados brutos de {f.name}"):
                st.dataframe(df, use_container_width=True)
            
            frames.append(df)
            
        except Exception as e:
            st.error(f"❌ Erro ao processar {f.name}")
            st.code(f"Tipo de erro: {type(e).__name__}\nMensagem: {str(e)}")
            
            # Mostrar preview do arquivo para debug
            with st.expander("🔍 Ver conteúdo do arquivo (primeiras 500 caracteres)"):
                try:
                    # Tentar diferentes encodings
                    for enc in ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']:
                        try:
                            text_preview = data[:500].decode(enc, errors='ignore')
                            st.write(f"**Encoding usado:** {enc}")
                            st.code(text_preview)
                            break
                        except:
                            continue
                except:
                    st.warning("Não foi possível exibir o preview do arquivo")
            
            st.info("💡 **Dica:** Tente converter o arquivo para Excel (.xlsx) no Excel/LibreOffice")
            continue

    if frames:
        df = pd.concat(frames, ignore_index=True).drop_duplicates("hash")
        if df.empty:
            st.warning("⚠️ Nenhuma transação válida detectada após processar todos os arquivos.")
            st.info("💡 **Dicas:**\n- Verifique se o arquivo contém transações\n- Confirme se as colunas têm os nomes corretos (Data, Descrição, Valor)\n- Tente abrir o arquivo no Excel para ver sua estrutura")
            st.stop()
        # carregar regras do usuário
        rules = supa().table("categorization_rules").select("*").eq("user_id", uid).execute().data
        df = apply_rules(df, rules)
        st.dataframe(df, use_container_width=True)

        if st.button("Gravar no banco"):
            # descobrir account_id
            aid = [a["id"] for a in accounts if a["name"]==account_name][0]
            payload = []
            for _,r in df.iterrows():
                amount = float(r["amount"])
                transaction_type = "income" if amount > 0 else "expense"
                payload.append({
                    "user_id": uid,
                    "account_id": aid,
                    "date": str(r["date"]),
                    "description": r["description"],
                    "amount": amount,
		    "transaction_type": transaction_type,
                    "category": r.get("category"),
                    "subcategory": r.get("subcategory"),
                    "tags": None,
                    "notes": None,
                    "hash_id": r["hash"]
                    
                })
            supa().table("transactions").upsert(payload, on_conflict="hash_id").execute()
            st.success("Importação concluída!")
