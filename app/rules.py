import re
import pandas as pd

def apply_rules(df: pd.DataFrame, rules: list[dict]):
    # rules: [{"pattern": "IFOOD|RAPPI", "category":"Alimentação","subcategory":"Delivery","priority":10}, ...]
    if df.empty or not rules:
        df["category"] = None
        df["subcategory"] = None
        return df
    df["category"] = None
    df["subcategory"] = None
    # ordenar por prioridade
    rules_sorted = sorted(rules, key=lambda r: r.get("priority",100))
    for r in rules_sorted:
        pat = re.compile(r["pattern"], flags=re.IGNORECASE)
        mask = df["description"].str.contains(pat)
        df.loc[mask, "category"] = r["category"]
        if r.get("subcategory"):
            df.loc[mask, "subcategory"] = r["subcategory"]
    return df
