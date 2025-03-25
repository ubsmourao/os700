# inventario.py

import streamlit as st
import pandas as pd
import base64  # Import para manipular a imagem em base64
import pytz
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder

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
    data_aquisicao=None, data_garantia_fim=None,
    image_data=None
):
    """
    Adiciona nova máquina ao inventário, incluindo data_aquisicao e data_garantia_fim
    se quiser usar controle de garantia. Ajuste o BD conforme necessidade.
    Permite também inserir image_data (foto em base64).
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
            "data_garantia_fim": data_garantia_fim,
            "image_data": image_data  # salva a foto em base64
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
# Cadastro de Máquina (com foto opcional)
###########################

def cadastro_maquina():
    """
    Cadastro básico de máquina no inventário, incluindo foto opcional.
    """
    st.subheader("Cadastrar Máquina no Inventário")

    tipo_options = ["Computador", "Impressora", "Monitor", "Outro"]
    tipo = st.selectbox("Tipo de Equipamento", tipo_options)

    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    numero_serie = st.text_input("Número de Série (Opcional)")

    patrimonio = st.text_input("Número de Patrimônio")

    status_options = ["Ativo", "Em Manutencao", "Inativo"]
    status = st.selectbox("Status", status_options)

    ubs_list = get_ubs_list()
    localizacao = st.selectbox("Localização (UBS)", sorted(ubs_list))

    setores_list = get_setores_list()
    setor = st.selectbox("Setor", sorted(setores_list))

    propria_options = ["Propria", "Locada"]
    propria_locada = st.selectbox("Própria ou Locada", propria_options)

    # Upload de foto (opcional)
    uploaded_file = st.file_uploader("Foto da máquina (opcional)", type=["png","jpg","jpeg"])

    if st.button("Cadastrar Máquina"):
        # Se houver imagem, converte para base64
        image_data = None
        if uploaded_file is not None:
            file_content = uploaded_file.read()
            image_data = base64.b64encode(file_content).decode("utf-8")

        try:
            add_machine_to_inventory(
                tipo=tipo,
                marca=marca,
                modelo=modelo,
                numero_serie=numero_serie,
                status=status,
                localizacao=localizacao,
                propria_locada=propria_locada,
                patrimonio=patrimonio,
                setor=setor,
                image_data=image_data  # Envia a foto (em base64) para salvar
            )
        except Exception as e:
            st.error("Erro ao cadastrar máquina.")
            st.write(e)

###########################
# Mostrar Inventário (com edição e foto)
###########################

def show_inventory_list():
    """
    Lista o inventário com opção de editar qualquer campo (incluindo foto),
    excluir e ver histórico (chamados e peças).
    """
    st.subheader("Inventário - Lista (com foto)")
    machines = get_machines_from_inventory()
    if machines:
        df = pd.DataFrame(machines)
        st.dataframe(df)

        patrimonio_options = df["numero_patrimonio"].unique().tolist()
        selected_patrimonio = st.selectbox("Selecione o patrimônio para visualizar detalhes", patrimonio_options)
        if selected_patrimonio:
            item = df[df["numero_patrimonio"] == selected_patrimonio].iloc[0]

            # Exibe a imagem atual, se existir
            st.markdown("### Foto Atual da Máquina")
            if item.get("image_data"):
                current_image = base64.b64decode(item["image_data"])
                st.image(current_image, caption=f"Foto da máquina {selected_patrimonio}")
            else:
                st.info("Nenhuma foto cadastrada para esta máquina.")

            with st.expander("Editar Máquina"):
                with st.form("editar_maquina"):
                    # Tipo
                    tipo_options = ["Computador", "Impressora", "Monitor", "Outro"]
                    if item.get("tipo") in tipo_options:
                        tipo_index = tipo_options.index(item.get("tipo"))
                    else:
                        tipo_index = 0
                    tipo = st.selectbox("Tipo de Equipamento", tipo_options, index=tipo_index)

                    marca = st.text_input("Marca", value=item.get("marca", ""))
                    modelo = st.text_input("Modelo", value=item.get("modelo", ""))
                    numero_serie = st.text_input("Número de Série", value=item.get("numero_serie", ""))

                    status_options = ["Ativo", "Em Manutencao", "Inativo"]
                    if item["status"] in status_options:
                        status_index = status_options.index(item["status"])
                    else:
                        status_index = 0
                    status = st.selectbox("Status", status_options, index=status_index)

                    # Localização (UBS)
                    ubs_list = get_ubs_list()
                    if item["localizacao"] in ubs_list:
                        loc_index = ubs_list.index(item["localizacao"])
                    else:
                        loc_index = 0
                    localizacao = st.selectbox("Localização (UBS)", sorted(ubs_list), index=loc_index)

                    # Setor
                    setores_list = get_setores_list()
                    if item["setor"] in setores_list:
                        setor_index = setores_list.index(item["setor"])
                    else:
                        setor_index = 0
                    setor = st.selectbox("Setor", sorted(setores_list), index=setor_index)

                    propria_options = ["Propria", "Locada"]
                    if item["propria_locada"] in propria_options:
                        propria_index = propria_options.index(item["propria_locada"])
                    else:
                        propria_index = 0
                    propria_locada = st.selectbox("Própria ou Locada", propria_options, index=propria_index)

                    # File uploader para trocar a foto
                    uploaded_file = st.file_uploader("Nova foto (opcional)", type=["png","jpg","jpeg"])
                    
                    # Botão para remover foto atual
                    remove_foto = st.checkbox("Remover foto atual?", value=False)

                    submit = st.form_submit_button("Salvar Alterações")
                    if submit:
                        new_values = {
                            "tipo": tipo,
                            "marca": marca,
                            "modelo": modelo,
                            "numero_serie": numero_serie or None,
                            "status": status,
                            "localizacao": localizacao,
                            "setor": setor,
                            "propria_locada": propria_locada
                        }

                        # Se o usuário marcou para remover a foto, seta 'image_data' para None
                        if remove_foto:
                            new_values["image_data"] = None
                        else:
                            # Se subiu uma nova foto, atualiza
                            if uploaded_file is not None:
                                file_content = uploaded_file.read()
                                encoded = base64.b64encode(file_content).decode("utf-8")
                                new_values["image_data"] = encoded

                        # Atualiza no BD
                        supabase.table("inventario").update(new_values).eq("numero_patrimonio", selected_patrimonio).execute()
                        st.success("Máquina atualizada com sucesso!")

            with st.expander("Excluir Máquina do Inventário"):
                if st.button("Excluir esta máquina"):
                    supabase.table("inventario").delete().eq("numero_patrimonio", selected_patrimonio).execute()
                    st.success("Máquina excluída com sucesso!")

            # Exemplo de histórico
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
# Edição em Massa (com selectbox para new_value)
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
    Agora com selectbox para o novo valor também.
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

    selected = grid_response["selected_rows"]  # lista de dicionários

    if isinstance(selected, list) and len(selected) > 0:
        st.write(f"{len(selected)} itens selecionados.")

    # Exportar CSV filtrado
    if st.button("Exportar CSV Filtrado"):
        csv_filtrado = df.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar CSV Filtrado", data=csv_filtrado, file_name="inventario_filtrado.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("Edição em Massa")

    # Campo a atualizar
    field = st.selectbox("Campo para atualizar", ["status", "setor", "localizacao", "propria_locada"])

    # Mapeamento de opções para cada campo
    field_options_map = {
        "status": ["Ativo", "Em Manutencao", "Inativo"],
        "setor": get_setores_list(),
        "localizacao": get_ubs_list(),
        "propria_locada": ["Propria", "Locada"]
    }

    # Exibe um selectbox para o novo valor, baseado no campo escolhido
    if field:
        options_for_new_value = field_options_map.get(field, [])
        if options_for_new_value:
            new_value = st.selectbox("Novo valor para esse campo", options_for_new_value)
        else:
            # Se por acaso o campo não estiver no map, fallback para text_input
            new_value = st.text_input("Novo valor para esse campo")
    else:
        new_value = st.text_input("Novo valor para esse campo")

    if st.button("Aplicar Edição em Massa"):
        if isinstance(selected, list) and len(selected) > 0:
            patrimonios_selecionados = [row["numero_patrimonio"] for row in selected]
            if field and new_value:
                batch_update_inventory(field, new_value, patrimonios_selecionados)
            else:
                st.warning("Selecione um campo e insira/defina o novo valor.")
        else:
            st.warning("Nenhum item selecionado.")