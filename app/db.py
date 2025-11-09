import streamlit as st
from supabase import create_client

def supa():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

def insert(table, data: dict):
    return supa().table(table).insert(data).execute()

def upsert(table, data: dict, on: str):
    return supa().table(table).upsert(data, on_conflict=on).execute()

def select(table, filters: dict=None, order=("created_at","desc")):
    q = supa().table(table).select("*")
    if filters:
        for k,v in filters.items():
            q = q.eq(k, v)
    if order:
        q = q.order(order[0], desc=(order[1]=="desc"))
    return q.execute().data

def delete(table, filters: dict):
    q = supa().table(table).delete()
    for k,v in filters.items():
        q = q.eq(k, v)
    return q.execute()
