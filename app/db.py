import streamlit as st
from supabase import create_client

def supa():
    client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

    # ------------ ADIÇÃO IMPORTANTE: associar a sessão atual ------------
    # st.session_state.session é o AuthResponse retornado pelo sign_in/sign_up
    sess = st.session_state.get("session", None)
    try:
        # v2 do supabase-py
        if sess and getattr(sess, "session", None):
            access_token = sess.session.access_token
            refresh_token = sess.session.refresh_token
            client.auth.set_session(access_token, refresh_token)
        # fallback (algumas versões usam set_auth)
        elif sess and getattr(sess, "access_token", None):
            client.auth.set_auth(sess.access_token)
    except Exception:
        pass
    # --------------------------------------------------------------------

    return client

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
