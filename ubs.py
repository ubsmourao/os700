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
        # Tenta inserir; se a UBS já existir, o comando pode ser ignorado (dependendo da política do banco)
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

def manage_ubs():
    st.subheader("Gerenciar UBSs")
    action = st.selectbox("Ação", ["Listar", "Adicionar", "Editar", "Remover"])
    
    if action == "Listar":
        ubs = get_ubs_list()
        if ubs:
            # Distribui a lista em 3 colunas para melhorar o layout
            num_colunas = 3
            colunas = st.columns(num_colunas)
            for index, ubs_item in enumerate(ubs):
                colunas[index % num_colunas].write(f"- {ubs_item}")
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
