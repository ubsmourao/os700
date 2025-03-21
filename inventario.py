import streamlit as st
import pandas as pd
from supabase_client import supabase
from setores import get_setores_list
from ubs import get_ubs_list  # Para uso no cadastro de máquina

def get_machines_from_inventory():
    try:
        resp = supabase.table("inventario").select("*").execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error("Erro ao recuperar inventario.")
        print(f"Erro: {e}")
        return []

def edit_inventory_item(patrimonio, new_values):
    try:
        supabase.table("inventario").update(new_values).eq("numero_patrimonio", patrimonio).execute()
        st.success("Item atualizado com sucesso!")
    except Exception as e:
        st.error("Erro ao atualizar o item do inventario.")
        print(f"Erro: {e}")

def add_machine_to_inventory(tipo, marca, modelo, numero_serie, status, localizacao, propria_locada, patrimonio, setor):
    try:
        resp = supabase.table("inventario").select("numero_patrimonio").eq("numero_patrimonio", patrimonio).execute()
        if resp.data:
            st.error(f"Maquina com patrimonio {patrimonio} ja existe no inventario.")
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
        st.success("Maquina adicionada ao inventario com sucesso!")
    except Exception as e:
        st.error("Erro ao adicionar maquina ao inventario.")
        print(f"Erro: {e}")

def delete_inventory_item(patrimonio):
    try:
        supabase.table("inventario").delete().eq("numero_patrimonio", patrimonio).execute()
        st.success("Item excluido com sucesso!")
    except Exception as e:
        st.error("Erro ao excluir item do inventario.")
        print(f"Erro: {e}")

def get_pecas_usadas_por_patrimonio(patrimonio):
    """
    Recupera todas as pecas utilizadas associadas aos chamados tecnicos da maquina identificada pelo patrimonio.
    """
    try:
        # Importacao local para evitar dependencia circular
        mod = __import__("chamados", fromlist=["get_chamados_por_patrimonio"])
        get_chamados_por_patrimonio = mod.get_chamados_por_patrimonio
    except Exception as e:
        st.error("Erro ao importar funcao de chamados.")
        print(f"Erro: {e}")
        return []
    chamados = get_chamados_por_patrimonio(patrimonio)
    if not chamados:
        return []
    chamado_ids = [chamado["id"] for chamado in chamados if "id" in chamado]
    try:
        resp = supabase.table("pecas_usadas").select("*").in_("chamado_id", chamado_ids).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error("Erro ao recuperar pecas utilizadas.")
        print(f"Erro: {e}")
        return []

def show_inventory_list():
    st.subheader("Inventario")
    machines = get_machines_from_inventory()
    if machines:
        df = pd.DataFrame(machines)
        st.dataframe(df)
        
        patrimonio_options = df["numero_patrimonio"].unique().tolist()
        selected_patrimonio = st.selectbox("Selecione o patrimonio para visualizar detalhes", patrimonio_options)
        if selected_patrimonio:
            item = df[df["numero_patrimonio"] == selected_patrimonio].iloc[0]
            
            with st.expander("Editar Item de Inventario"):
                with st.form("editar_item"):
                    tipo = st.text_input("Tipo", value=item.get("tipo", ""))
                    marca = st.text_input("Marca", value=item.get("marca", ""))
                    modelo = st.text_input("Modelo", value=item.get("modelo", ""))
                    
                    status_options = ["Ativo", "Em Manutencao", "Inativo"]
                    status_index = status_options.index(item.get("status")) if item.get("status") in status_options else 0
                    status = st.selectbox("Status", status_options, index=status_index)
                    
                    localizacao = st.text_input("Localizacao", value=item.get("localizacao", ""))
                    
                    setores_list = get_setores_list()
                    setor_index = setores_list.index(item.get("setor")) if item.get("setor") in setores_list else 0
                    setor = st.selectbox("Setor", setores_list, index=setor_index)
                    
                    propria_options = ["Propria", "Locada"]
                    propria_index = propria_options.index(item.get("propria_locada")) if item.get("propria_locada") in propria_options else 0
                    propria_locada = st.selectbox("Propria/Locada", propria_options, index=propria_index)
                    
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
                        edit_inventory_item(selected_patrimonio, new_values)
            
            with st.expander("Excluir Item do Inventario"):
                if st.button("Excluir este item"):
                    delete_inventory_item(selected_patrimonio)
            
            with st.expander("Historico Completo da Maquina"):
                st.markdown("**Chamados Tecnicos:**")
                try:
                    mod = __import__("chamados", fromlist=["get_chamados_por_patrimonio"])
                    get_chamados_por_patrimonio = mod.get_chamados_por_patrimonio
                except Exception as e:
                    st.error("Erro ao importar funcao de chamados.")
                    print(f"Erro: {e}")
                    get_chamados_por_patrimonio = lambda x: []
                chamados = get_chamados_por_patrimonio(selected_patrimonio)
                if chamados:
                    st.dataframe(pd.DataFrame(chamados))
                else:
                    st.write("Nenhum chamado tecnico encontrado para este item.")
                
                st.markdown("**Pecas Utilizadas:**")
                pecas = get_pecas_usadas_por_patrimonio(selected_patrimonio)
                if pecas:
                    st.dataframe(pd.DataFrame(pecas))
                else:
                    st.write("Nenhuma peca utilizada encontrada para este item.")
    else:
        st.write("Nenhum item encontrado no inventario.")

def cadastro_maquina():
    st.subheader("Cadastrar Maquina no Inventario")
    tipo = st.selectbox("Tipo de Equipamento", ["Computador", "Impressora", "Monitor", "Outro"])
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    numero_serie = st.text_input("Numero de Serie (Opcional)")
    patrimonio = st.text_input("Numero de Patrimonio")
    status = st.selectbox("Status", ["Ativo", "Em Manutencao", "Inativo"])
    ubs = st.selectbox("UBS", sorted(get_ubs_list()))
    setores_list = get_setores_list()
    setor = st.selectbox("Setor", sorted(setores_list))
    propria_locada = st.selectbox("Propria ou Locada", ["Propria", "Locada"])
    
    if st.button("Cadastrar Maquina"):
        try:
            resp = supabase.table("inventario").select("numero_patrimonio").eq("numero_patrimonio", patrimonio).execute()
            if resp.data:
                st.error("Maquina com este patrimonio ja existe.")
            else:
                data = {
                    "numero_patrimonio": patrimonio,
                    "tipo": tipo,
                    "marca": marca,
                    "modelo": modelo,
                    "numero_serie": numero_serie or None,
                    "status": status,
                    "localizacao": ubs,
                    "propria_locada": propria_locada,
                    "setor": setor
                }
                supabase.table("inventario").insert(data).execute()
                st.success("Maquina cadastrada com sucesso!")
        except Exception as e:
            st.error("Erro ao cadastrar maquina.")
            st.write(e)

if __name__ == "__main__":
    opcao = st.radio("Selecione uma opcao:", ["Listar Inventario", "Cadastrar Maquina"])
    if opcao == "Listar Inventario":
        show_inventory_list()
    else:
        cadastro_maquina()
