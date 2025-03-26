# inventario.py

import streamlit as st
import pandas as pd
import base64  # Para manipular a imagem em base64
import pytz
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
import matplotlib.pyplot as plt

from supabase_client import supabase
from setores import get_setores_list
from ubs import get_ubs_list

FORTALEZA_TZ = pytz.timezone("America/Fortaleza")

###########################
# 1. Funções Básicas
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
# 2. Peças Usadas
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
# 3. Histórico de Manutenção
###########################

def get_historico_manutencao_por_patrimonio(patrimonio):
    """
    Retorna todos os registros de manutenção (tabela 'historico_manutencao')
    para a máquina identificada pelo numero_patrimonio.
    """
    try:
        resp = supabase.table("historico_manutencao").select("*").eq("numero_patrimonio", patrimonio).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error("Erro ao buscar histórico de manutenção.")
        print(f"Erro: {e}")
        return []

###########################
# 4. Cadastro de Máquina
###########################

def cadastro_maquina():
    """
    Cadastro básico de máquina no inventário, incluindo foto opcional.
    """
    st.subheader("Cadastrar Máquina no Inventário")

    tipo_options = ["Computador", "Impressora", "Monitor", "Nobreak", "Outro"]
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
# 5. Mostrar Inventário (com filtros e edição)
###########################

def show_inventory_list():
    """
    Lista o inventário com:
      - Filtros para refinar a busca
      - Opção de editar qualquer campo (incluindo foto)
      - Excluir item
      - Histórico (chamados, peças, manutenção)
    """

    st.subheader("Inventário - Lista com Filtros")

    # 1) Filtro por texto (marca, modelo, patrimônio, etc.)
    filtro_texto = st.text_input("Buscar por texto (marca, modelo, patrimônio...)")

    # 2) Filtro por Status
    status_options = ["Todos", "Ativo", "Em Manutencao", "Inativo"]
    status_filtro = st.selectbox("Filtrar por Status", status_options)

    # 3) Filtro por Localização (UBS)
    ubs_list = get_ubs_list()
    ubs_list_filtro = ["Todas"] + sorted(ubs_list)
    localizacao_filtro = st.selectbox("Filtrar por Localização (UBS)", ubs_list_filtro)

    # 4) Filtro por Setor
    setores_list = get_setores_list()
    setores_list_filtro = ["Todos"] + sorted(setores_list)
    setor_filtro = st.selectbox("Filtrar por Setor", setores_list_filtro)

    # Obter dados do inventário
    machines = get_machines_from_inventory()
    if not machines:
        st.info("Nenhum item encontrado no inventário.")
        return

    df = pd.DataFrame(machines)

    # Aplica filtro de texto (buscando em qualquer campo do DF)
    if filtro_texto:
        filtro_lower = filtro_texto.lower()
        df = df[df.apply(lambda row: filtro_lower in str(row).lower(), axis=1)]

    # Aplica filtro de status
    if status_filtro != "Todos":
        df = df[df["status"] == status_filtro]

    # Aplica filtro de localização (UBS)
    if localizacao_filtro != "Todas":
        df = df[df["localizacao"] == localizacao_filtro]

    # Aplica filtro de setor
    if setor_filtro != "Todos":
        df = df[df["setor"] == setor_filtro]

    # Exibe via st_aggrid ou st.dataframe
    st.markdown("### Resultado do Inventário (Filtrado)")
    if not df.empty:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(filter=True, sortable=True)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_grid_options(domLayout='normal')
        grid_options = gb.build()

        AgGrid(
            df,
            gridOptions=grid_options,
            height=400,
            fit_columns_on_grid_load=True
        )
    else:
        st.warning("Nenhum resultado com esses filtros.")

    # Abaixo, permitir que o usuário selecione um patrimônio para ver detalhes
    st.markdown("---")
    st.subheader("Detalhes / Edição de Item do Inventário")

    patrimonio_options = df["numero_patrimonio"].unique().tolist()
    if patrimonio_options:
        selected_patrimonio = st.selectbox("Selecione o patrimônio para visualizar detalhes", patrimonio_options)
    else:
        selected_patrimonio = None

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
                tipo_options = ["Computador", "Impressora", "Monitor", "Nobreak", "Outro"]
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
                ubs_list_sorted = sorted(ubs_list)
                if item["localizacao"] in ubs_list_sorted:
                    loc_index = ubs_list_sorted.index(item["localizacao"])
                else:
                    loc_index = 0
                localizacao = st.selectbox("Localização (UBS)", ubs_list_sorted, index=loc_index)

                # Setor
                setores_list_sorted = sorted(setores_list)
                if item["setor"] in setores_list_sorted:
                    setor_index = setores_list_sorted.index(item["setor"])
                else:
                    setor_index = 0
                setor = st.selectbox("Setor", setores_list_sorted, index=setor_index)

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

        # Histórico Completo da Máquina
        with st.expander("Histórico Completo da Máquina"):
            # Chamados Técnicos
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
            
            # Peças Utilizadas
            st.markdown("**Peças Utilizadas:**")
            pecas = get_pecas_usadas_por_patrimonio(selected_patrimonio)
            if pecas:
                st.dataframe(pd.DataFrame(pecas))
            else:
                st.write("Nenhuma peça utilizada encontrada para este item.")

            # Histórico de Manutenção
            st.markdown("**Histórico de Manutenção:**")
            historico_manut = get_historico_manutencao_por_patrimonio(selected_patrimonio)
            if historico_manut:
                st.dataframe(pd.DataFrame(historico_manut))
            else:
                st.write("Nenhum registro de manutenção encontrado para este item.")

###########################
# 6. Dashboard do Inventário
###########################

def dashboard_inventario():
    """
    Exemplo de painel do inventário que inclui:
      - Distribuição por Status
      - Distribuição por Tipo
      - Distribuição por UBS (Computadores e Impressoras SEPARADOS)
      - Distribuição por Setor
      - Máquinas com mais chamados
    """
    st.subheader("Dashboard do Inventário")

    data = get_machines_from_inventory()
    if not data:
        st.info("Nenhum item no inventário.")
        return
    df = pd.DataFrame(data)

    from chamados import list_chamados
    chamados = list_chamados() or []
    df_chamados = pd.DataFrame(chamados)

    #################################################
    # 1) Distribuição por Status
    #################################################
    if "status" in df.columns:
        status_count = df["status"].value_counts().reset_index()
        status_count.columns = ["status", "quantidade"]

        st.markdown("### 1) Distribuição por Status")
        st.table(status_count)

        fig, ax = plt.subplots()
        ax.bar(status_count["status"], status_count["quantidade"], color="green")
        ax.set_xlabel("Status")
        ax.set_ylabel("Quantidade")
        ax.set_title("Distribuição de Status no Inventário")
        st.pyplot(fig)
    else:
        st.warning("Coluna 'status' não encontrada no inventário.")

    #################################################
    # 2) Distribuição por Tipo
    #################################################
    if "tipo" in df.columns:
        st.markdown("### 2) Distribuição por Tipo de Equipamento")
        type_count = df["tipo"].value_counts().reset_index()
        type_count.columns = ["tipo", "quantidade"]

        st.table(type_count)

        fig2, ax2 = plt.subplots()
        ax2.bar(type_count["tipo"], type_count["quantidade"], color="blue")
        ax2.set_xlabel("Tipo de Equipamento")
        ax2.set_ylabel("Quantidade")
        ax2.set_title("Distribuição por Tipo de Equipamento")
        plt.xticks(rotation=45)
        st.pyplot(fig2)
    else:
        st.warning("Coluna 'tipo' não encontrada no inventário.")

    #################################################
    # 3) Distribuição por UBS (Computadores e Impressoras, separados)
    #################################################
    if "localizacao" in df.columns and "tipo" in df.columns:
        st.markdown("### 3) Distribuição por UBS (Computadores e Impressoras, separados)")

        # Filtra somente Computador e Impressora
        df_ubs = df[df["tipo"].isin(["Computador", "Impressora"])]
        if df_ubs.empty:
            st.write("Nenhum Computador ou Impressora encontrado no inventário.")
        else:
            # Agrupa por localizacao e tipo
            group_ubs = df_ubs.groupby(["localizacao", "tipo"]).size().reset_index(name="quantidade")

            # Faz pivot para ter colunas: Computador, Impressora
            pivot_ubs = group_ubs.pivot(index="localizacao", columns="tipo", values="quantidade").fillna(0)

            st.markdown("#### Tabela por UBS (linhas) e Tipo (colunas)")
            st.table(pivot_ubs)

            # Faz um gráfico de barras lado a lado (stacked=False)
            fig3, ax3 = plt.subplots()
            pivot_ubs.plot(kind="bar", ax=ax3, stacked=False)
            ax3.set_xlabel("UBS (Localização)")
            ax3.set_ylabel("Quantidade")
            ax3.set_title("Computadores e Impressoras por UBS (Separados)")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig3)
    else:
        st.warning("Coluna 'localizacao' ou 'tipo' não encontrada no inventário.")

    #################################################
    # 4) Distribuição por Setor (sem mês)
    #################################################
    if "setor" in df.columns:
        st.markdown("### 4) Distribuição por Setor")
        setor_count = df["setor"].value_counts().reset_index()
        setor_count.columns = ["setor", "quantidade"]

        st.table(setor_count)

        fig4, ax4 = plt.subplots()
        ax4.barh(setor_count["setor"], setor_count["quantidade"], color="purple")
        ax4.set_xlabel("Quantidade")
        ax4.set_ylabel("Setor")
        ax4.set_title("Distribuição por Setor")
        st.pyplot(fig4)
    else:
        st.warning("Coluna 'setor' não encontrada no inventário.")

    #################################################
    # 5) Máquinas com Mais Chamados (Top 10)
    #################################################
    st.markdown("### 5) Máquinas com Mais Chamados (Top 10)")
    if df_chamados.empty:
        st.info("Não há chamados registrados para cruzar com o inventário.")
    else:
        # Conta quantos chamados cada patrimônio teve
        maquinas_mais_chamados = df_chamados.groupby("patrimonio").size().reset_index(name="qtd_chamados")

        # Faz merge com df de inventário
        df_merged = pd.merge(df, maquinas_mais_chamados, how="left",
                             left_on="numero_patrimonio", right_on="patrimonio")

        # Substitui NaN por 0 (caso alguma máquina não tenha chamado)
        df_merged["qtd_chamados"] = df_merged["qtd_chamados"].fillna(0)

        # Ordena do maior para o menor
        df_merged.sort_values("qtd_chamados", ascending=False, inplace=True)

        # Exibe top 10
        top_10 = df_merged.head(10)

        st.dataframe(top_10[["numero_patrimonio", "tipo", "marca", "modelo", "qtd_chamados"]])

        fig5, ax5 = plt.subplots()
        ax5.barh(top_10["numero_patrimonio"].astype(str), top_10["qtd_chamados"], color="red")
        ax5.set_xlabel("Quantidade de Chamados")
        ax5.set_ylabel("Patrimônio")
        ax5.set_title("Top 10 Máquinas com Mais Chamados")
        ax5.invert_yaxis()  # Inverte o eixo Y para a maior ficar em cima
        st.pyplot(fig5)