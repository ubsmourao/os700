# inventario.py

import streamlit as st
import pandas as pd
import base64
import pytz
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder

# Ajuste conforme seu projeto
from supabase_client import supabase
from setores import get_setores_list
from ubs import get_ubs_list

FORTALEZA_TZ = pytz.timezone("America/Fortaleza")

###########################
# Funções Básicas
###########################

def get_machines_from_inventory():
    """
    Retorna todas as máquinas da tabela 'inventario'.
    """
    try:
        resp = supabase.table("inventario").select("*").execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error("Erro ao recuperar inventário.")
        print(f"Erro: {e}")
        return []

def edit_inventory_item(patrimonio, new_values):
    """
    Edita campos de uma máquina específica, identificada pelo patrimônio.
    new_values é um dicionário {coluna: valor}.
    """
    try:
        supabase.table("inventario").update(new_values).eq("numero_patrimonio", patrimonio).execute()
        st.success("Item atualizado com sucesso!")
    except Exception as e:
        st.error("Erro ao atualizar o item do inventário.")
        print(f"Erro: {e}")

def add_machine_to_inventory(
    tipo, marca, modelo, numero_serie, status, localizacao,
    propria_locada, patrimonio, setor,
    data_aquisicao=None, data_garantia_fim=None
):
    """
    Adiciona nova máquina ao inventário, incluindo data_aquisicao e data_garantia_fim
    se quiser usar controle de garantia. Ajuste o BD conforme necessidade.
    """
    try:
        # Verifica se já existe esse patrimônio
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
            "setor": setor,
            "data_aquisicao": data_aquisicao,
            "data_garantia_fim": data_garantia_fim
        }
        supabase.table("inventario").insert(data).execute()
        st.success("Máquina adicionada ao inventário com sucesso!")
    except Exception as e:
        st.error("Erro ao adicionar máquina ao inventário.")
        print(f"Erro: {e}")

def delete_inventory_item(patrimonio):
    """
    Exclui uma máquina do inventário pelo patrimônio.
    """
    try:
        supabase.table("inventario").delete().eq("numero_patrimonio", patrimonio).execute()
        st.success("Item excluído com sucesso!")
    except Exception as e:
        st.error("Erro ao excluir item do inventário.")
        print(f"Erro: {e}")

###########################
# Peças Usadas
###########################

def get_pecas_usadas_por_patrimonio(patrimonio):
    """
    Recupera todas as peças utilizadas associadas aos chamados técnicos da máquina.
    """
    try:
        # Importação local para evitar dependência circular
        mod = __import__("chamados", fromlist=["get_chamados_por_patrimonio"])
        get_chamados_por_patrimonio = mod.get_chamados_por_patrimonio
    except Exception as e:
        st.error("Erro ao importar função de chamados.")
        print(f"Erro: {e}")
        return []
    chamados = get_chamados_por_patrimonio(patrimonio)
    if not chamados:
        return []
    chamado_ids = [ch["id"] for ch in chamados if "id" in ch]
    try:
        resp = supabase.table("pecas_usadas").select("*").in_("chamado_id", chamado_ids).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error("Erro ao recuperar peças utilizadas.")
        print(f"Erro: {e}")
        return []

###########################
# Mostrar Inventário (Exemplo Original)
###########################

def show_inventory_list():
    """
    Lista o inventário com opção de editar, excluir e ver histórico (chamados e peças).
    """
    st.subheader("Inventário - Lista Original")
    machines = get_machines_from_inventory()
    if machines:
        df = pd.DataFrame(machines)
        st.dataframe(df)

        patrimonio_options = df["numero_patrimonio"].unique().tolist()
        selected_patrimonio = st.selectbox("Selecione o patrimônio para visualizar detalhes", patrimonio_options)
        if selected_patrimonio:
            item = df[df["numero_patrimonio"] == selected_patrimonio].iloc[0]
            
            with st.expander("Editar Item de Inventário"):
                with st.form("editar_item"):
                    tipo = st.text_input("Tipo", value=item.get("tipo", ""))
                    marca = st.text_input("Marca", value=item.get("marca", ""))
                    modelo = st.text_input("Modelo", value=item.get("modelo", ""))

                    status_options = ["Ativo", "Em Manutencao", "Inativo"]
                    if item.get("status") in status_options:
                        status_index = status_options.index(item.get("status"))
                    else:
                        status_index = 0
                    status = st.selectbox("Status", status_options, index=status_index)

                    localizacao = st.text_input("Localização", value=item.get("localizacao", ""))
                    
                    setores_list = get_setores_list()
                    if item.get("setor") in setores_list:
                        setor_index = setores_list.index(item.get("setor"))
                    else:
                        setor_index = 0
                    setor = st.selectbox("Setor", setores_list, index=setor_index)

                    propria_options = ["Propria", "Locada"]
                    if item.get("propria_locada") in propria_options:
                        propria_index = propria_options.index(item.get("propria_locada"))
                    else:
                        propria_index = 0
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
                            "propria_locada": propria_locada
                        }
                        edit_inventory_item(selected_patrimonio, new_values)
            
            with st.expander("Excluir Item do Inventário"):
                if st.button("Excluir este item"):
                    delete_inventory_item(selected_patrimonio)
            
            with st.expander("Histórico Completo da Máquina"):
                st.markdown("**Chamados Técnicos:**")
                try:
                    mod = __import__("chamados", fromlist=["get_chamados_por_patrimonio"])
                    get_chamados_por_patrimonio = mod.get_chamados_por_patrimonio
                except Exception as e:
                    st.error("Erro ao importar função de chamados.")
                    print(f"Erro: {e}")
                    get_chamados_por_patrimonio = lambda x: []
                chamados = get_chamados_por_patrimonio(selected_patrimonio)
                if chamados:
                    st.dataframe(pd.DataFrame(chamados))
                else:
                    st.write("Nenhum chamado técnico encontrado para este item.")

                st.markdown("**Peças Utilizadas:**")
                pecas = get_pecas_usadas_por_patrimonio(selected_patrimonio)
                if pecas:
                    st.dataframe(pd.DataFrame(pecas))
                else:
                    st.write("Nenhuma peça utilizada encontrada para este item.")
    else:
        st.write("Nenhum item encontrado no inventário.")

###########################
# Batch Update (Edição em Massa)
###########################

def batch_update_inventory(field_to_update, new_value, patrimonios):
    """
    Atualiza, em massa, o campo field_to_update para new_value
    em todos os patrimônios informados.
    """
    try:
        for pat in patrimonios:
            supabase.table("inventario").update({field_to_update: new_value}).eq("numero_patrimonio", pat).execute()
        st.success(f"{len(patrimonios)} itens atualizados para {field_to_update} = {new_value}")
    except Exception as e:
        st.error("Erro ao fazer edição em massa.")
        print(f"Erro: {e}")

def show_inventory_list_with_batch_edit():
    """
    Lista o inventário com filtros, exportação de CSV filtrado,
    e edição em massa de um campo (status, setor, localizacao, etc.).
    Corrige o 'if selected:' -> checamos se 'selected' é lista e seu tamanho.
    """
    st.subheader("Inventário - Edição em Massa")

    # Filtro por texto
    filtro_texto = st.text_input("Filtrar por texto (marca, modelo, setor...)")
    # Filtro por status
    status_filtro = st.selectbox("Filtrar por Status", ["Todos", "Ativo", "Em Manutencao", "Inativo"])

    data = get_machines_from_inventory()
    if not data:
        st.info("Nenhum item no inventário.")
        return

    df = pd.DataFrame(data)

    # Aplica filtro de texto
    if filtro_texto:
        filtro_lower = filtro_texto.lower()
        df = df[df.apply(lambda row: filtro_lower in str(row).lower(), axis=1)]

    # Filtro de status
    if status_filtro != "Todos":
        df = df[df["status"] == status_filtro]

    # Exibe via st_aggrid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(filter=True, sortable=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=400,
        fit_columns_on_grid_load=True,
        update_mode="MODEL_CHANGED"
    )

    # st_aggrid retorna um dicionário com 'selected_rows'
    selected = grid_response["selected_rows"]  # Normalmente é uma lista

    # Se 'selected' é lista, checamos se tem itens
    if isinstance(selected, list):
        if len(selected) > 0:
            st.write(f"{len(selected)} itens selecionados.")
    else:
        # Se por algum motivo 'selected' fosse DataFrame, faríamos:
        # if not selected.empty:
        #     st.write(f"{len(selected)} itens selecionados.")
        pass

    # Exportar CSV filtrado
    if st.button("Exportar CSV Filtrado"):
        csv_filtrado = df.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar CSV Filtrado", data=csv_filtrado, file_name="inventario_filtrado.csv", mime="text/csv")

    # Edição em massa
    st.markdown("---")
    st.subheader("Edição em Massa")
    field = st.selectbox("Campo para atualizar", ["status", "setor", "localizacao", "propria_locada"])
    new_value = st.text_input("Novo valor para esse campo")
    if st.button("Aplicar Edição em Massa"):
        # Verifica se 'selected' é lista e se há itens
        if isinstance(selected, list) and len(selected) > 0:
            patrimonios_selecionados = [row["numero_patrimonio"] for row in selected]
            if field and new_value:
                batch_update_inventory(field, new_value, patrimonios_selecionados)
            else:
                st.warning("Selecione um campo e insira o novo valor.")
        else:
            st.warning("Nenhum item selecionado.")

###########################
# Dashboard do Inventário
###########################

def dashboard_inventario():
    """
    Exemplo de dashboard simples: contagem por status e um gráfico de barras.
    """
    st.subheader("Dashboard do Inventário")
    data = get_machines_from_inventory()
    if not data:
        st.info("Nenhum item no inventário.")
        return
    df = pd.DataFrame(data)

    # Contagem por status
    contagem_status = df["status"].value_counts().reset_index()
    contagem_status.columns = ["status", "quantidade"]

    st.write("Contagem por Status:")
    st.dataframe(contagem_status)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.bar(contagem_status["status"], contagem_status["quantidade"], color="green")
    ax.set_xlabel("Status")
    ax.set_ylabel("Quantidade")
    ax.set_title("Distribuição de Status no Inventário")
    st.pyplot(fig)

###########################
# Gerenciar Imagens
###########################

def manage_images():
    """
    Permite fazer upload de imagem e associar ao patrimônio,
    salvando em base64 no campo 'image_data'.
    """
    st.subheader("Gerenciar Imagens do Equipamento")

    patrimonio = st.text_input("Informe o Patrimônio")
    uploaded_file = st.file_uploader("Selecione uma imagem (JPEG/PNG)")

    if st.button("Enviar Imagem"):
        if not patrimonio:
            st.warning("Informe o patrimônio.")
            return
        if not uploaded_file:
            st.warning("Nenhum arquivo selecionado.")
            return

        file_content = uploaded_file.read()
        encoded = base64.b64encode(file_content).decode("utf-8")
        try:
            supabase.table("inventario").update({"image_data": encoded}).eq("numero_patrimonio", patrimonio).execute()
            st.success("Imagem enviada com sucesso!")
        except Exception as e:
            st.error("Erro ao salvar imagem no inventário.")
            st.write(e)

    # Exibir imagem se existir
    if st.button("Ver Imagem"):
        if not patrimonio:
            st.warning("Informe o patrimônio.")
            return
        try:
            resp = supabase.table("inventario").select("image_data").eq("numero_patrimonio", patrimonio).execute()
            if resp.data and resp.data[0].get("image_data"):
                encoded = resp.data[0]["image_data"]
                import base64
                file_content = base64.b64decode(encoded)
                st.image(file_content, caption=f"Imagem da máquina {patrimonio}")
            else:
                st.info("Nenhuma imagem encontrada para este patrimônio.")
        except Exception as e:
            st.error("Erro ao buscar imagem.")
            st.write(e)

###########################
# Cadastro de Máquina
###########################

def cadastro_maquina():
    """
    Cadastro básico de máquina no inventário.
    Se quiser datas de aquisição/garantia, inclua os campos aqui e no BD.
    """
    st.subheader("Cadastrar Máquina no Inventário")
    tipo = st.selectbox("Tipo de Equipamento", ["Computador", "Impressora", "Monitor", "Outro"])
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    numero_serie = st.text_input("Número de Série (Opcional)")
    patrimonio = st.text_input("Número de Patrimônio")
    status = st.selectbox("Status", ["Ativo", "Em Manutencao", "Inativo"])
    ubs = st.selectbox("Localização (UBS)", sorted(get_ubs_list()))
    setores_list = get_setores_list()
    setor = st.selectbox("Setor", sorted(setores_list))
    propria_locada = st.selectbox("Própria ou Locada", ["Propria", "Locada"])

    if st.button("Cadastrar Máquina"):
        try:
            resp = supabase.table("inventario").select("numero_patrimonio").eq("numero_patrimonio", patrimonio).execute()
            if resp.data:
                st.error("Máquina com este patrimônio já existe.")
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
                st.success("Máquina cadastrada com sucesso!")
        except Exception as e:
            st.error("Erro ao cadastrar máquina.")
            st.write(e)