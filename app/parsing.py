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
    """
    Parse CSV files with automatic encoding and delimiter detection
    Includes special handling for Bradesco format
    """
    from loguru import logger
    
    # Try to detect Bradesco format first (only check first 1000 bytes)
    try:
        # Tentar detectar formato Bradesco sem decodificar ainda
        sample = file_bytes[:1000].decode('windows-1252', errors='ignore')
        if 'Extrato de: Ag:' in sample and 'Crédito (R$)' in sample:
            logger.info("🏦 Detectado formato Bradesco, usando parser específico")
            # Full decode for Bradesco parsing
            text = file_bytes.decode('windows-1252', errors='replace')
            result = _parse_bradesco_csv(text, account_name)
            # Se o parser específico não encontrou nada, tentar método genérico
            if len(result) == 0:
                logger.warning("Parser específico do Bradesco não encontrou transações, tentando método alternativo")
                # Tentar processar como CSV normal pulando a primeira linha
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding='windows-1252', delimiter=';', skiprows=1)
                    return normalize_df(df, account_name)
                except Exception as inner_e:
                    logger.error(f"Método alternativo também falhou: {inner_e}")
                    pass
            else:
                logger.info(f"✅ Parser Bradesco retornou {len(result)} transações")
            return result
    except Exception as e:
        logger.error(f"Erro no parser do Bradesco: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # If detection fails, continue with normal parsing
        pass
    
    # Try with most common encodings for Brazilian banks (prioritize Windows-1252)
    encodings = ['windows-1252', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-8']
    delimiters = [',', ';', '\t', '|']
    
    logger.info("🔍 Tentando detectar encoding e delimitador automaticamente")
    
    # Try different encoding and delimiter combinations
    for encoding in encodings:
        for delimiter in delimiters:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding, delimiter=delimiter, skiprows=0, on_bad_lines='skip')
                # Check if we got at least 2 columns (valid CSV)
                if len(df.columns) > 1 and len(df) > 0:
                    logger.info(f"✅ Sucesso com encoding={encoding}, delimiter='{delimiter}'")
                    return normalize_df(df, account_name)
            except (UnicodeDecodeError, UnicodeError) as e:
                logger.debug(f"❌ {encoding} + '{delimiter}' falhou: {e}")
                continue
            except Exception as e:
                logger.debug(f"❌ {encoding} + '{delimiter}' erro: {e}")
                continue
    
    # If all combinations fail, try with error handling and auto-detection
    logger.warning("⚠️ Nenhuma combinação funcionou, tentando auto-detecção")
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding='windows-1252', errors='ignore', sep=None, engine='python', on_bad_lines='skip')
        return normalize_df(df, account_name)
    except Exception as e:
        raise ValueError(f"Não foi possível ler o arquivo CSV. Verifique se o formato está correto. Erro: {str(e)}")

def _parse_bradesco_csv(text, account_name):
    """
    Parser específico para CSV do Bradesco Internet Banking
    Formato: Data;Histórico;Docto.;Crédito (R$);Débito (R$);Saldo (R$)
    O arquivo vem todo em uma linha, separado por ponto-e-vírgula
    """
    import re
    from loguru import logger
    rows = []
    
    # Split by semicolon
    fields = [f.strip() for f in text.split(';')]
    logger.info(f"Bradesco parser: {len(fields)} campos encontrados")
    
    # Encontrar o índice onde começam os dados (após o cabeçalho)
    start_idx = 0
    for i, field in enumerate(fields):
        if re.match(r'^\d{2}/\d{2}/\d{2,4}$', field):
            start_idx = i
            logger.info(f"Primeira data encontrada no índice {i}: {field}")
            break
    
    # Processar campos em grupos de 6: Data, Histórico, Docto, Crédito, Débito, Saldo
    i = start_idx
    while i + 5 < len(fields):
        date_str = fields[i].strip()
        
        # Verificar se é uma data válida
        if not re.match(r'^\d{2}/\d{2}/\d{2,4}$', date_str):
            i += 1
            continue
        
        historic = fields[i+1].strip()
        docto = fields[i+2].strip()
        credit_str = fields[i+3].strip().replace('"', '')
        debit_str = fields[i+4].strip().replace('"', '')
        saldo_str = fields[i+5].strip().replace('"', '')
        
        logger.info(f"[{i}] Date: {date_str} | Hist: {historic[:40]} | Cred: '{credit_str}' | Deb: '{debit_str}'")
        
        # Skip SALDO ANTERIOR
        if 'SALDO ANTERIOR' in historic.upper():
            logger.info("  → Pulando SALDO ANTERIOR")
            i += 6
            continue
        
        # Parse date
        date = _parse_dates(date_str)
        if not date:
            logger.warning(f"  → Data inválida: {date_str}")
            i += 6
            continue
        
        # Parse amount
        amount = None
        try:
            if credit_str and credit_str not in ['', '-', '0', '0,00']:
                amount = float(credit_str.replace('.', '').replace(',', '.'))
                logger.info(f"  → Crédito: {credit_str} = R$ {amount}")
            elif debit_str and debit_str not in ['', '-', '0', '0,00']:
                # Remover o sinal de menos se já estiver (pois já vamos adicionar)
                debit_clean = debit_str.replace('-', '').replace('.', '').replace(',', '.')
                amount = -float(debit_clean)
                logger.info(f"  → Débito: {debit_str} = R$ {amount}")
        except ValueError as e:
            logger.error(f"  → Erro ao converter: cred='{credit_str}', deb='{debit_str}': {e}")
            pass
        
        # Se temos data e valor, adicionar
        skip_extra = 0
        if date and amount is not None and amount != 0:
            # Verificar se o próximo campo é uma descrição adicional (Des:)
            full_description = historic
            if i + 6 < len(fields):
                next_field = fields[i+6].strip()
                if next_field.startswith('Des:') or next_field.startswith('Remet.'):
                    full_description += ' - ' + next_field
                    skip_extra = 1  # Marcar para pular este campo extra
                    logger.info(f"  → Desc extra: {next_field[:50]}")
            
            rows.append({
                'date': date,
                'description': full_description,
                'amount': amount,
                'account': account_name,
                'raw': f"{date_str};{historic};{docto};{credit_str};{debit_str};{saldo_str}"
            })
            logger.info(f"  ✅ Transação #{len(rows)}: {date} | {full_description[:40]} | R$ {amount:,.2f}")
        else:
            logger.warning(f"  ❌ Ignorado: date={date}, amount={amount}")
        
        i += 6 + skip_extra
    
    logger.info(f"Bradesco parser: {len(rows)} transações extraídas")
    df = pd.DataFrame(rows)
    return finalize(df)

def from_xlsx(file_bytes, account_name):
    """
    Parse Excel files (.xlsx or .xls)
    Automatically detects the correct engine to use
    """
    try:
        # Try openpyxl first (for .xlsx files)
        df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
    except Exception as e:
        # If openpyxl fails, try xlrd (for old .xls files)
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
        except Exception as e2:
            # If both fail, let pandas decide
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
    """
    Normaliza dataframe para formato padrão
    Aceita múltiplas variações de nomes de colunas
    """
    mapping = {}
    
    # Lista expandida de possíveis nomes de colunas
    date_cols = [
        "data", "date", "dt", "posted date", "transaction date",
        "data de lançamento", "data lancamento", "data da transação",
        "data transacao", "dt movimentação", "dt movimentacao",
        "data movimentação", "data movimentacao"
    ]
    
    description_cols = [
        "descricao", "descrição", "description", "memo", "historico", "histórico",
        "histórico da transação", "historico da transacao", "detalhes",
        "descrição do lançamento", "descricao do lancamento", "transaction",
        "detalhe", "transacao", "transação"
    ]
    
    amount_cols = [
        "valor", "amount", "ammount", "valor (r$)", "total", "value",
        "vlr. lançamento", "vlr lancamento", "vlr", "montante",
        "valor da transação", "valor da transacao", "débito/crédito",
        "debito/credito", "entrada/saída", "entrada/saida"
    ]
    
    # Buscar matching de colunas (case insensitive)
    for col in df.columns:
        lc = str(col).strip().lower()
        
        if any(date_col in lc for date_col in date_cols):
            mapping["date"] = col
        elif any(desc_col in lc for desc_col in description_cols):
            mapping["description"] = col
        elif any(amt_col in lc for amt_col in amount_cols):
            mapping["amount"] = col

    # Se não encontrou colunas, tentar adivinhar pelas primeiras 3 colunas
    if not mapping:
        cols = list(df.columns)
        if len(cols) >= 3:
            mapping["date"] = cols[0]  # Primeira coluna geralmente é data
            mapping["description"] = cols[1]  # Segunda é descrição
            mapping["amount"] = cols[2]  # Terceira é valor

    out = pd.DataFrame()
    # preenche com None se faltarem colunas
    out["date"] = df[mapping["date"]].map(_parse_dates) if "date" in mapping else None
    out["description"] = df[mapping["description"]].astype(str) if "description" in mapping else ""
    if "amount" in mapping:
        out["amount"] = pd.to_numeric(
            df[mapping["amount"]].astype(str).str.replace(".","").str.replace(",",".").str.replace("R$","").str.strip(),
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

