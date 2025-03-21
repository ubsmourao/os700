# setores.py
import streamlit as st
from supabase_client import supabase

def get_setores_list():
    try:
        resp = supabase.table("setores").select("nome_setor").execute()
        return [s["nome_setor"] for s in resp.data] if resp.data else []
    except Exception as e:
        st.error("Erro ao recuperar setores.")
        print(f"Erro: {e}")
        return []

def add_setor(nome_setor):
    try:
        # Tenta inserir; se já existir, ignora
        supabase.table("setores").insert({"nome_setor": nome_setor}).execute()
        return True
    except Exception as e:
        print(f"Erro ao adicionar setor: {e}")
        return False

def remove_setor(nome_setor):
    try:
        supabase.table("setores").delete().eq("nome_setor", nome_setor).execute()
        return True
    except Exception as e:
        print(f"Erro ao remover setor: {e}")
        return False

def update_setor(old_name, new_name):
    try:
        supabase.table("setores").update({"nome_setor": new_name}).eq("nome_setor", old_name).execute()
        return True
    except Exception as e:
        print(f"Erro ao atualizar setor: {e}")
        return False

def manage_setores():
    st.subheader("Gerenciar Setores")
    action = st.selectbox("Ação", ["Listar", "Adicionar", "Editar", "Remover"])
    if action == "Listar":
        setores = get_setores_list()
        st.write(setores if setores else "Nenhum setor cadastrado.")
    elif action == "Adicionar":
        nome = st.text_input("Nome do Setor")
        if st.button("Adicionar") and nome:
            if add_setor(nome):
                st.success("Setor adicionado!")
            else:
                st.error("Erro ao adicionar setor.")
    elif action == "Editar":
        setores = get_setores_list()
        if setores:
            old = st.selectbox("Selecione", setores)
            new = st.text_input("Novo nome", value=old)
            if st.button("Atualizar") and new:
                if update_setor(old, new):
                    st.success("Setor atualizado!")
                else:
                    st.error("Erro na atualização.")
    elif action == "Remover":
        setores = get_setores_list()
        if setores:
            nome = st.selectbox("Selecione para remover", setores)
            if st.button("Remover"):
                if remove_setor(nome):
                    st.success("Setor removido!")
                else:
                    st.error("Erro ao remover setor.")
