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
        tp = st.selectbox("Tipo", ["checking","savings","credit","cash","brokerage"])
        s = st.form_submit_button("Criar")
        if s and name:
            insert("accounts", {"user_id": uid, "name": name, "institution": inst, "type": tp})
            st.success("Conta criada. Recarregue a página."); st.stop()
else:
    account_name = acc

uploaded = st.file_uploader("Envie extratos (CSV, XLSX, OFX, PDF)", accept_multiple_files=True)
if uploaded:
    frames=[]
    for f in uploaded:
        data = f.read()
        ext = f.name.lower().split(".")[-1]
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
        frames.append(df)

    if frames:
        df = pd.concat(frames, ignore_index=True).drop_duplicates("hash")
        if df.empty:
            st.warning("Nenhuma transação válida detectada. Verifique o layout do arquivo ou ajuste as regras de parsing.")
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
                payload.append({
                    "user_id": uid,
                    "account_id": aid,
                    "date": str(r["date"]),
                    "description": r["description"],
                    "amount": float(r["amount"]),
                    "category": r.get("category"),
                    "subcategory": r.get("subcategory"),
                    "tags": None,
                    "source_file": None,
                    "hash": r["hash"]
                })
            supa().table("transactions").upsert(payload, on_conflict="hash").execute()
            st.success("Importação concluída!")
