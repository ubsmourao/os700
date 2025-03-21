# ubs.py
import streamlit as st
from supabase_client import supabase

def get_ubs_list():
    try:
        resp = supabase.table("ubs").select("nome_ubs").execute()
        return [u["nome_ubs"] for u in resp.data] if resp.data else []
    except Exception as e:
        st.error("Erro ao recuperar UBSs.")
        print(f"Erro: {e}")
        return []

def add_ubs(nome_ubs):
    try:
        supabase.table("ubs").insert({"nome_ubs": nome_ubs}).execute()
        return True
    except Exception as e:
        print(f"Erro ao adicionar UBS: {e}")
        return False

def remove_ubs(nome_ubs):
    try:
        supabase.table("ubs").delete().eq("nome_ubs", nome_ubs).execute()
        return True
    except Exception as e:
        print(f"Erro ao remover UBS: {e}")
        return False

def update_ubs(old_name, new_name):
    try:
        supabase.table("ubs").update({"nome_ubs": new_name}).eq("nome_ubs", old_name).execute()
        return True
    except Exception as e:
        print(f"Erro ao atualizar UBS: {e}")
        return False

def manage_ubs():
    st.subheader("Gerenciar UBSs")
    action = st.selectbox("Ação", ["Listar", "Adicionar", "Editar", "Remover"])
    if action == "Listar":
        ubs = get_ubs_list()
        st.write(ubs if ubs else "Nenhuma UBS cadastrada.")
    elif action == "Adicionar":
        nome = st.text_input("Nome da UBS")
        if st.button("Adicionar") and nome:
            if add_ubs(nome):
                st.success("UBS adicionada!")
            else:
                st.error("Erro ao adicionar UBS.")
    elif action == "Editar":
        ubs = get_ubs_list()
        if ubs:
            old = st.selectbox("Selecione", ubs)
            new = st.text_input("Novo nome", value=old)
            if st.button("Atualizar") and new:
                if update_ubs(old, new):
                    st.success("UBS atualizada!")
                else:
                    st.error("Erro na atualização.")
    elif action == "Remover":
        ubs = get_ubs_list()
        if ubs:
            nome = st.selectbox("Selecione para remover", ubs)
            if st.button("Remover"):
                if remove_ubs(nome):
                    st.success("UBS removida!")
                else:
                    st.error("Erro ao remover UBS.")
