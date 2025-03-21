import streamlit as st
import pandas as pd
from supabase_client import supabase

def get_estoque():
    try:
        resp = supabase.table("estoque").select("*").execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"Erro ao recuperar estoque: {e}")
        return []

def add_peca(nome, quantidade, descricao=""):
    try:
        data = {
            "nome": nome,
            "quantidade": quantidade,
            "descricao": descricao
        }
        supabase.table("estoque").insert(data).execute()
        st.success("Peça adicionada ao estoque!")
    except Exception as e:
        st.error(f"Erro ao adicionar peça: {e}")

def update_peca(id_peca, new_values):
    try:
        supabase.table("estoque").update(new_values).eq("id", id_peca).execute()
        st.success("Peça atualizada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao atualizar peça: {e}")

def delete_peca(id_peca):
    try:
        supabase.table("estoque").delete().eq("id", id_peca).execute()
        st.success("Peça excluída com sucesso!")
    except Exception as e:
        st.error(f"Erro ao excluir peça: {e}")

def manage_estoque():
    st.subheader("Gerenciar Estoque de Peças de Informática")
    action = st.selectbox("Ação", ["Listar", "Adicionar", "Editar", "Remover"])
    
    if action == "Listar":
        estoque = get_estoque()
        if estoque:
            st.dataframe(pd.DataFrame(estoque))
        else:
            st.write("Estoque vazio.")
    elif action == "Adicionar":
        nome = st.text_input("Nome da Peça")
        quantidade = st.number_input("Quantidade", min_value=0, step=1)
        descricao = st.text_area("Descrição (opcional)")
        if st.button("Adicionar Peça"):
            if nome:
                add_peca(nome, quantidade, descricao)
            else:
                st.error("Insira o nome da peça.")
    elif action == "Editar":
        estoque = get_estoque()
        if estoque:
            df = pd.DataFrame(estoque)
            st.dataframe(df)
            id_peca = st.selectbox("Selecione o ID da peça para editar", df["id"].tolist())
            if id_peca:
                nome = st.text_input("Nome da Peça")
                quantidade = st.number_input("Quantidade", min_value=0, step=1)
                descricao = st.text_area("Descrição (opcional)")
                if st.button("Atualizar Peça"):
                    new_values = {
                        "nome": nome,
                        "quantidade": quantidade,
                        "descricao": descricao
                    }
                    update_peca(id_peca, new_values)
        else:
            st.write("Estoque vazio para edição.")
    elif action == "Remover":
        estoque = get_estoque()
        if estoque:
            df = pd.DataFrame(estoque)
            st.dataframe(df)
            id_peca = st.selectbox("Selecione o ID da peça para remover", df["id"].tolist())
            if st.button("Remover Peça"):
                delete_peca(id_peca)
        else:
            st.write("Estoque vazio para remoção.")

if __name__ == "__main__":
    manage_estoque()
