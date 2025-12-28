import io, re, hashlib
import pandas as pd
import pdfplumber
from ofxparse import OfxParser
from datetime import datetime

COLS = ["date","description","amount","account","raw"]
DATE_FORMATS = ["%d/%m/%Y","%Y-%m-%d","%d-%m-%Y","%m/%d/%Y"]

def _parse_dates(val):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except:
            pass
    # tentar pandas
    try:
        return pd.to_datetime(val, dayfirst=True).date()
    except:
        return None

def _hash_row(row):
    h = hashlib.sha1(("|".join([str(row.get(c,"")) for c in ["date","description","amount","account"]])).encode()).hexdigest()
    return h

def from_csv(file_bytes, account_name):
    df = pd.read_csv(io.BytesIO(file_bytes))
    return normalize_df(df, account_name)

def from_xlsx(file_bytes, account_name):
    df = pd.read_excel(io.BytesIO(file_bytes))
    return normalize_df(df, account_name)

def from_ofx(file_bytes, account_name):
    ofx = OfxParser.parse(io.BytesIO(file_bytes))
    rows = []
    for acct in ofx.accounts:
        for tx in acct.statement.transactions:
            rows.append({
                "date": tx.date.date() if hasattr(tx.date, "date") else tx.date,
                "description": tx.memo or tx.payee or "",
                "amount": float(tx.amount),
                "account": account_name,
                "raw": tx.id or ""
            })
    df = pd.DataFrame(rows)
    return finalize(df)

def from_pdf(file_bytes, account_name):
    """
    Faz parsing de extratos PDF do Bradesco (Internet Banking)
    ou usa o padrão genérico se outro formato.
    """
    import re, pdfplumber
    rows = []
    text_full = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_full += (page.extract_text() or "") + "\n"

    # --- Caso seja Bradesco ---
    if "Bradesco Internet Banking" in text_full:
        # Divide por linhas
        lines = [ln.strip() for ln in text_full.splitlines() if ln.strip()]
        current_date = None
        current_desc = ""
        for ln in lines:
            # detecta data
            mdate = re.match(r"^(\d{2}/\d{2}/\d{2,4})", ln)
            if mdate:
                current_date = _parse_dates(mdate.group(1))
                continue
            # detecta descrição iniciada por Des: ou Pgto ou Pix
            if ln.lower().startswith(("des:", "pgto", "pix", "trans", "fii", "rem:", "poup", "bco")):
                current_desc = ln
                continue
            # detecta valor (usa vírgula decimal)
            mval = re.search(r"([-+]?\d{1,3}(?:\.\d{3})*,\d{2})", ln)
            if mval and current_date:
                try:
                    amount = float(mval.group(1).replace(".", "").replace(",", "."))
                except:
                    amount = None
                # se houver palavra "Des" antes do número → débito
                sign = -1 if re.search(r"\s-\s|\s-\d", ln) or "Des:" in current_desc else 1
                rows.append({
                    "date": current_date,
                    "description": current_desc or ln,
                    "amount": sign * amount if amount else None,
                    "account": account_name,
                    "raw": ln
                })
                current_desc = ""
                current_date = None
        df = pd.DataFrame(rows)
        return finalize(df)

    # --- Caso padrão genérico (outros bancos) ---
    rows = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                m = re.search(r'(\d{2}/\d{2}/\d{4}).*?([-+]?\d+[.,]\d{2})', line)
                if m:
                    date = _parse_dates(m.group(1))
                    try:
                        amount = float(m.group(2).replace(".","").replace(",","."))
                    except:
                        amount = None
                    rows.append({"date": date, "description": line.strip(), "amount": amount, "account": account_name, "raw": line})
    df = pd.DataFrame(rows)
    return finalize(df)



def normalize_df(df, account_name):
    mapping = {}
    for col in df.columns:
        lc = str(col).strip().lower()
        if lc in ["data","date","dt","posted date","transaction date"]:
            mapping["date"] = col
        elif lc in ["descricao","descrição","description","memo","historico","histórico"]:
            mapping["description"] = col
        elif lc in ["valor","amount","ammount","valor (r$)","total"]:
            mapping["amount"] = col

    out = pd.DataFrame()
    # preenche com None se faltarem colunas
    out["date"] = df[mapping["date"]].map(_parse_dates) if "date" in mapping else None
    out["description"] = df[mapping["description"]].astype(str) if "description" in mapping else ""
    if "amount" in mapping:
        out["amount"] = pd.to_numeric(
            df[mapping["amount"]].astype(str).str.replace(".","").str.replace(",","."),
            errors="coerce"
        )
    else:
        out["amount"] = None
    out["account"] = account_name
    out["raw"] = df[mapping["description"]].astype(str) if "description" in mapping else ""
    return finalize(out)


def finalize(df):
    # garante colunas esperadas mesmo que o df venha vazio/incompleto
    for col in ["date", "description", "amount", "account", "raw"]:
        if col not in df.columns:
            df[col] = None

    # normalizações finais
    df = df[["date","description","amount","account","raw"]].copy()
    # tenta converter tipos (sem quebrar)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # se nada válido, retorna vazio com colunas e hash
    if df[["date","amount"]].isna().all(axis=None):
        df["hash"] = []
        return df

    df = df.dropna(subset=["date","amount"]).copy()

    # hash de deduplicação
    df["hash"] = df.apply(_hash_row, axis=1)
    return df[["date","description","amount","account","raw","hash"]]

