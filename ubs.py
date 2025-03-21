import streamlit as st
import pandas as pd
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
        st.error("Erro ao adicionar UBS.")
        print(f"Erro ao adicionar UBS: {e}")
        return False

def remove_ubs(nome_ubs):
    try:
        supabase.table("ubs").delete().eq("nome_ubs", nome_ubs).execute()
        return True
    except Exception as e:
        st.error("Erro ao remover UBS.")
        print(f"Erro ao remover UBS: {e}")
        return False

def update_ubs(old_name, new_name):
    try:
        supabase.table("ubs").update({"nome_ubs": new_name}).eq("nome_ubs", old_name).execute()
        return True
    except Exception as e:
        st.error("Erro ao atualizar UBS.")
        print(f"Erro ao atualizar UBS: {e}")
        return False

def get_inventario_por_ubs(ubs):
    try:
        resp = supabase.table("inventario").select("*").eq("localizacao", ubs).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error("Erro ao recuperar inventário.")
        print(f"Erro: {e}")
        return []

def get_chamados_por_ubs(ubs):
    try:
        resp = supabase.table("chamados").select("*").eq("ubs", ubs).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error("Erro ao recuperar chamados técnicos.")
        print(f"Erro: {e}")
        return []

def manage_ubs():
    st.subheader("Gerenciar UBSs")
    action = st.selectbox("Ação", ["Listar", "Adicionar", "Editar", "Remover"])
    
    if action == "Listar":
        ubs = get_ubs_list()
        if ubs:
            # Exibe cada UBS em um expander para que o usuário possa clicar e visualizar os detalhes
            for ubs_item in ubs:
                with st.expander(f"{ubs_item}"):
                    # Consulta e exibe informações do inventário associadas à UBS
                    inventario = get_inventario_por_ubs(ubs_item)
                    if inventario:
                        st.markdown("**Inventário:**")
                        df_inv = pd.DataFrame(inventario)
                        st.dataframe(df_inv)
                    else:
                        st.write("Nenhum item de inventário encontrado.")
                    
                    # Consulta e exibe os chamados técnicos associados à UBS
                    chamados = get_chamados_por_ubs(ubs_item)
                    if chamados:
                        st.markdown("**Chamados Técnicos:**")
                        df_chamados = pd.DataFrame(chamados)
                        st.dataframe(df_chamados)
                    else:
                        st.write("Nenhum chamado técnico encontrado.")
        else:
            st.write("Nenhuma UBS cadastrada.")
    
    elif action == "Adicionar":
        nome = st.text_input("Nome da UBS")
        if st.button("Adicionar"):
            if nome:
                if add_ubs(nome):
                    st.success("UBS adicionada com sucesso!")
                else:
                    st.error("Erro ao adicionar UBS.")
            else:
                st.error("Por favor, insira o nome da UBS.")
    
    elif action == "Editar":
        ubs = get_ubs_list()
        if ubs:
            old_name = st.selectbox("Selecione a UBS para editar:", ubs)
            new_name = st.text_input("Novo nome da UBS", value=old_name)
            if st.button("Atualizar"):
                if new_name:
                    if update_ubs(old_name, new_name):
                        st.success("UBS atualizada com sucesso!")
                    else:
                        st.error("Erro ao atualizar UBS.")
                else:
                    st.error("Por favor, insira o novo nome da UBS.")
        else:
            st.write("Nenhuma UBS cadastrada para editar.")
    
    elif action == "Remover":
        ubs = get_ubs_list()
        if ubs:
            nome = st.selectbox("Selecione a UBS para remover:", ubs)
            if st.button("Remover"):
                if remove_ubs(nome):
                    st.success("UBS removida com sucesso!")
                else:
                    st.error("Erro ao remover UBS.")
        else:
            st.write("Nenhuma UBS cadastrada para remover.")

if __name__ == "__main__":
    manage_ubs()
