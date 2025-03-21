import streamlit as st
import pandas as pd
from supabase_client import supabase

def get_machines_from_inventory():
    try:
        resp = supabase.table("inventario").select("*").execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error("Erro ao recuperar inventário.")
        print(f"Erro: {e}")
        return []

def edit_inventory_item(patrimonio, new_values):
    """
    Atualiza os dados do item do inventário identificado pelo número de patrimônio.
    new_values deve ser um dicionário com as chaves: tipo, marca, modelo, status, localizacao, setor, propria_locada.
    """
    try:
        supabase.table("inventario").update(new_values).eq("numero_patrimonio", patrimonio).execute()
        st.success("Item atualizado com sucesso!")
    except Exception as e:
        st.error("Erro ao atualizar o item do inventário.")
        print(f"Erro: {e}")

def add_machine_to_inventory(tipo, marca, modelo, numero_serie, status, localizacao, propria_locada, patrimonio, setor):
    try:
        # Verifica se o item já existe
        resp = supabase.table("inventario").select("numero_patrimonio").eq("numero_patrimonio", patrimonio).execute()
        if resp.data:
            st.error(f"Máquina com patrimônio {patrimonio} já existe no inventário.")
            return
        data = {
            "numero_patrimonio": patrimonio,
            "tipo": tipo,
            "marca": marca,
            "modelo": modelo,
            "numero_serie": numero_serie or None,
            "status": status,
            "localizacao": localizacao,
            "propria_locada": propria_locada,
            "setor": setor
        }
        supabase.table("inventario").insert(data).execute()
        st.success("Máquina adicionada ao inventário com sucesso!")
    except Exception as e:
        st.error("Erro ao adicionar máquina ao inventário.")
        print(f"Erro: {e}")

def show_inventory_list():
    st.subheader("Lista de Inventário")
    machines = get_machines_from_inventory()
    if machines:
        # Exibe os dados em uma tabela
        df = pd.DataFrame(machines)
        st.dataframe(df)
        
        # Seleção do patrimônio para edição
        patrimonio_options = df["numero_patrimonio"].unique()
        patrimonio = st.selectbox("Selecione o número de patrimônio para editar", patrimonio_options)
        if patrimonio:
            # Recupera o item selecionado
            item = df[df["numero_patrimonio"] == patrimonio].iloc[0]
            with st.expander("Editar Item de Inventário"):
                with st.form("editar_item"):
                    tipo = st.text_input("Tipo", value=item.get("tipo", ""))
                    marca = st.text_input("Marca", value=item.get("marca", ""))
                    modelo = st.text_input("Modelo", value=item.get("modelo", ""))
                    status = st.text_input("Status", value=item.get("status", ""))
                    localizacao = st.text_input("Localização", value=item.get("localizacao", ""))
                    setor = st.text_input("Setor", value=item.get("setor", ""))
                    propria_locada = st.text_input("Própria/Locada", value=item.get("propria_locada", ""))
                    submit = st.form_submit_button("Atualizar Item")
                    if submit:
                        new_values = {
                            "tipo": tipo,
                            "marca": marca,
                            "modelo": modelo,
                            "status": status,
                            "localizacao": localizacao,
                            "setor": setor,
                            "propria_locada": propria_locada,
                        }
                        edit_inventory_item(patrimonio, new_values)
    else:
        st.write("Nenhum item encontrado no inventário.")

if __name__ == "__main__":
    show_inventory_list()
