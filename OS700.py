import streamlit as st
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
from fpdf import FPDF
from st_aggrid import AgGrid, GridOptionsBuilder

# Importação dos módulos e funções
from autenticacao import authenticate, add_user, is_admin, list_users
from chamados import (
    add_chamado,
    get_chamado_by_protocolo,
    list_chamados,
    list_chamados_em_aberto,
    finalizar_chamado,
    buscar_no_inventario_por_patrimonio,
    calculate_working_hours
)
from inventario import show_inventory_list, cadastro_maquina, get_machines_from_inventory
from ubs import get_ubs_list
from setores import get_setores_list
from estoque import manage_estoque, get_estoque

# Configuração do logging
logging.basicConfig(level=logging.INFO)

# Inicializa variáveis de sessão
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Configuração da página
st.set_page_config(page_title="Gestão de Parque de Informática", layout="wide")
logo_path = os.getenv("LOGO_PATH", "infocustec.png")
if os.path.exists(logo_path):
    st.image(logo_path, width=300)
else:
    st.warning("Logotipo não encontrado.")

st.title("Gestão de Parque de Informática - UBS ITAPIPOCA")

# Definição do menu
if st.session_state.logged_in:
    if is_admin(st.session_state.username):
        menu_options = [
            "Dashboard",
            "Abrir Chamado",
            "Chamados Técnicos",
            "Inventário",
            "Estoque",
            "Administração",
            "Relatórios",
            "Exportar Dados",
            "Sair"
        ]
    else:
        # Usuários comuns: somente abrir chamado e buscar chamado
        menu_options = [
            "Abrir Chamado",
            "Buscar Chamado",
            "Sair"
        ]
else:
    menu_options = ["Login"]

selected = option_menu(
    menu_title=None,
    options=menu_options,
    icons=["speedometer", "chat-left-text", "card-list", "clipboard-data", "box-seam", "gear", "bar-chart-line", "download", "box-arrow-right"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "5!important", "background-color": "#F5F5F5"},
        "icon": {"color": "black", "font-size": "18px"},
        "nav-link": {
            "font-size": "16px",
            "text-align": "center",
            "margin": "0px",
            "color": "black",
            "padding": "10px"
        },
        "nav-link-selected": {"background-color": "#0275d8", "color": "white"}
    }
)

# --- Funções das Páginas ---

def login_page():
    st.subheader("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if not username or not password:
            st.error("Preencha todos os campos.")
        elif authenticate(username, password):
            st.success(f"Bem-vindo, {username}!")
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.error("Usuário ou senha incorretos.")

def dashboard_page():
    st.subheader("Dashboard - Administrativo")
    chamados = list_chamados()
    total_chamados = len(chamados) if chamados else 0
    abertos = len(list_chamados_em_aberto()) if chamados else 0
    st.metric("Total de Chamados", total_chamados)
    st.metric("Chamados Abertos", abertos)
    if chamados:
        df = pd.DataFrame(chamados)
        df["hora_abertura_dt"] = pd.to_datetime(df["hora_abertura"], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        df["mes"] = df["hora_abertura_dt"].dt.to_period("M").astype(str)
        tendencia = df.groupby("mes").size().reset_index(name="qtd")
        fig, ax = plt.subplots(figsize=(8,4))
        ax.plot(tendencia["mes"], tendencia["qtd"], marker="o")
        ax.set_xlabel("Mês")
        ax.set_ylabel("Quantidade de Chamados")
        ax.set_title("Tendência de Chamados no Tempo")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.write("Nenhum chamado registrado.")

def abrir_chamado_page():
    st.subheader("Abrir Chamado Técnico")
    patrimonio = st.text_input("Número de Patrimônio (opcional)")
    # Campo opcional para agendamento de manutenção
    data_agendada = st.date_input("Data Agendada para Manutenção (opcional)")
    machine_info = None
    machine_type = None
    ubs_selecionada = None
    setor = None

    if patrimonio:
        machine_info = buscar_no_inventario_por_patrimonio(patrimonio)
        if machine_info:
            st.write(f"Máquina encontrada: {machine_info['tipo']} - {machine_info['marca']} {machine_info['modelo']}")
            st.write(f"UBS: {machine_info['localizacao']} | Setor: {machine_info['setor']}")
            ubs_selecionada = machine_info["localizacao"]
            setor = machine_info["setor"]
            machine_type = machine_info["tipo"]
        else:
            st.error("Patrimônio não encontrado no inventário. Cadastre a máquina antes de abrir o chamado.")
            st.stop()
    else:
        ubs_selecionada = st.selectbox("UBS", get_ubs_list())
        setor = st.selectbox("Setor", get_setores_list())
        machine_type = st.selectbox("Tipo de Máquina", ["Computador", "Impressora", "Outro"])

    if machine_type == "Computador":
        defect_options = [
            "Computador não liga", "Computador lento", "Tela azul", "Sistema travando",
            "Erro de disco", "Problema com atualização", "Desligamento inesperado",
            "Problemas de internet", "Problema com Wi-Fi", "Sem conexão de rede",
            "Mouse não funciona", "Teclado não funciona"
        ]
    elif machine_type == "Impressora":
        defect_options = [
            "Impressora não imprime", "Impressão borrada", "Toner vazio",
            "Troca de toner", "Papel enroscado", "Erro de conexão com a impressora"
        ]
    else:
        defect_options = [
            "Solicitação de suporte geral", "Outros tipos de defeito"
        ]
    
    tipo_defeito = st.selectbox("Tipo de Defeito/Solicitação", defect_options)
    problema = st.text_area("Descreva o problema ou solicitação")
    
    if st.button("Abrir Chamado"):
        agendamento = data_agendada.strftime('%d/%m/%Y') if data_agendada else None
        protocolo = add_chamado(
            st.session_state.username,
            ubs_selecionada,
            setor,
            tipo_defeito,
            problema + (f" | Agendamento: {agendamento}" if agendamento else ""),
            patrimonio=patrimonio
        )
        if protocolo:
            st.success(f"Chamado aberto com sucesso! Protocolo: {protocolo}")
        else:
            st.error("Erro ao abrir chamado.")

def buscar_chamado_page():
    st.subheader("Buscar Chamado")
    protocolo = st.text_input("Informe o protocolo do chamado")
    if st.button("Buscar"):
        chamado = get_chamado_by_protocolo(protocolo)
        if chamado:
            st.write("Chamado encontrado:")
            st.json(chamado)
        else:
            st.error("Chamado não encontrado.")

def chamados_tecnicos_page():
    st.subheader("Chamados Técnicos")
    chamados = list_chamados()
    if not chamados:
        st.write("Nenhum chamado técnico encontrado.")
        return
    df = pd.DataFrame(chamados)
    def calcula_tempo(row):
        if pd.notnull(row.get("hora_fechamento")):
            try:
                abertura = datetime.strptime(row["hora_abertura"], '%d/%m/%Y %H:%M:%S')
                fechamento = datetime.strptime(row["hora_fechamento"], '%d/%m/%Y %H:%M:%S')
                tempo_util = calculate_working_hours(abertura, fechamento)
                return str(tempo_util)
            except Exception as e:
                return "Erro"
        else:
            return "Em aberto"
    df["Tempo Util"] = df.apply(calcula_tempo, axis=1)
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(filter=True, sortable=True)
    grid_options = gb.build()
    AgGrid(df, gridOptions=grid_options, height=400, fit_columns_on_grid_load=True)
    
    df_aberto = df[df["hora_fechamento"].isnull()]
    if df_aberto.empty:
        st.write("Não há chamados abertos para finalizar.")
    else:
        st.markdown("### Finalizar Chamado Técnico")
        chamado_id = st.selectbox("Selecione o ID do chamado para finalizar", df_aberto["id"].tolist())
        chamado = df_aberto[df_aberto["id"] == chamado_id].iloc[0]
        st.write(f"Problema: {chamado['problema']}")
        if "impressora" in chamado.get("tipo_defeito", "").lower():
            solucao_options = [
                "Limpeza e recalibração da impressora", "Substituição de cartucho/toner",
                "Verificação de conexão e drivers", "Reinicialização da impressora"
            ]
        else:
            solucao_options = [
                "Reinicialização do sistema", "Atualização de drivers/software",
                "Substituição de componente (ex.: HD, memória)", "Verificação de vírus/malware"
            ]
        solucao_selecionada = st.selectbox("Selecione a solução", solucao_options)
        solucao_complementar = st.text_area("Detalhes adicionais da solução (opcional)")
        solucao_final = solucao_selecionada + ((" - " + solucao_complementar) if solucao_complementar else "")
        comentarios = st.text_area("Comentários adicionais (opcional)")
        estoque_data = get_estoque()
        pieces_list = [item["nome"] for item in estoque_data] if estoque_data else []
        pecas_selecionadas = st.multiselect("Selecione as peças utilizadas (se houver)", pieces_list)
        if st.button("Finalizar Chamado"):
            if solucao_final:
                solucao_completa = solucao_final + (f" | Comentários: {comentarios}" if comentarios else "")
                finalizar_chamado(chamado_id, solucao_completa, pecas_usadas=pecas_selecionadas)
            else:
                st.error("Informe a solução para finalizar o chamado.")

def inventario_page():
    st.subheader("Inventário")
    opcao = st.radio("Selecione uma opção:", ["Listar Inventário", "Cadastrar Máquina"])
    if opcao == "Listar Inventário":
        inventario_data = get_machines_from_inventory()
        if inventario_data:
            df_inv = pd.DataFrame(inventario_data)
            gb_inv = GridOptionsBuilder.from_dataframe(df_inv)
            gb_inv.configure_pagination(paginationAutoPageSize=True)
            gb_inv.configure_default_column(filter=True, sortable=True)
            grid_options_inv = gb_inv.build()
            AgGrid(df_inv, gridOptions=grid_options_inv, height=400, fit_columns_on_grid_load=True)
        else:
            st.write("Nenhum item de inventário encontrado.")
    else:
        cadastro_maquina()

def estoque_page():
    manage_estoque()

def administracao_page():
    st.subheader("Administração")
    admin_option = st.selectbox("Opções de Administração", [
        "Cadastro de Usuário", "Gerenciar UBSs", "Gerenciar Setores", "Lista de Usuários"
    ])
    if admin_option == "Cadastro de Usuário":
        novo_user = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Senha", type="password")
        admin_flag = st.checkbox("Administrador")
        if st.button("Cadastrar Usuário"):
            if add_user(novo_user, nova_senha, admin_flag):
                st.success("Usuário cadastrado com sucesso!")
            else:
                st.error("Erro ao cadastrar usuário ou usuário já existe.")
    elif admin_option == "Gerenciar UBSs":
        from ubs import manage_ubs
        manage_ubs()
    elif admin_option == "Gerenciar Setores":
        from setores import manage_setores
        manage_setores()
    elif admin_option == "Lista de Usuários":
        usuarios = list_users()
        if usuarios:
            st.table(usuarios)
        else:
            st.write("Nenhum usuário cadastrado.")

def relatorios_page():
    st.subheader("Relatórios Completos - Estatísticas")
    st.markdown("### Filtros para Chamados")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Data Início")
    with col2:
        end_date = st.date_input("Data Fim")
    with col3:
        filtro_ubs = st.multiselect("Filtrar por UBS", get_ubs_list())
    if start_date > end_date:
        st.error("Data Início não pode ser maior que Data Fim")
        return
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Filtra os chamados pelo período
    chamados = list_chamados()
    if not chamados:
        st.write("Nenhum chamado técnico encontrado.")
        return
    df = pd.DataFrame(chamados)
    df["hora_abertura_dt"] = pd.to_datetime(df["hora_abertura"], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    df_period = df[(df["hora_abertura_dt"] >= start_datetime) & (df["hora_abertura_dt"] <= end_datetime)]
    if filtro_ubs:
        df_period = df_period[df_period["ubs"].isin(filtro_ubs)]
    st.markdown("### Chamados Técnicos no Período")
    gb = GridOptionsBuilder.from_dataframe(df_period)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(filter=True, sortable=True)
    grid_options = gb.build()
    AgGrid(df_period, gridOptions=grid_options, height=400, fit_columns_on_grid_load=True)
    
    # Estatística 1: Chamados por UBS por Mês
    df_period["mes"] = df_period["hora_abertura_dt"].dt.to_period("M").astype(str)
    chamados_ubs_mes = df_period.groupby(["ubs", "mes"]).size().reset_index(name="qtd_chamados")
    st.markdown("#### Chamados por UBS por Mês")
    st.dataframe(chamados_ubs_mes)
    fig1, ax1 = plt.subplots(figsize=(8,4))
    for ubs in chamados_ubs_mes["ubs"].unique():
        dados = chamados_ubs_mes[chamados_ubs_mes["ubs"] == ubs]
        ax1.plot(dados["mes"], dados["qtd_chamados"], marker="o", label=ubs)
    ax1.set_xlabel("Mês")
    ax1.set_ylabel("Quantidade de Chamados")
    ax1.set_title("Chamados por UBS por Mês")
    ax1.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig1)
    
    # Estatística 2: Chamados por Setor
    chamados_setor = df_period.groupby("setor").size().reset_index(name="qtd_chamados")
    st.markdown("#### Chamados por Setor")
    st.dataframe(chamados_setor)
    fig2, ax2 = plt.subplots(figsize=(8,4))
    ax2.bar(chamados_setor["setor"], chamados_setor["qtd_chamados"], color='orange')
    ax2.set_xlabel("Setor")
    ax2.set_ylabel("Quantidade de Chamados")
    ax2.set_title("Chamados por Setor")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig2)
    
    # Estatística 3: Tempo médio de atendimento por UBS e global (horas úteis)
    def calc_tempo(row):
        if pd.notnull(row["hora_fechamento"]):
            try:
                abertura = datetime.strptime(row["hora_abertura"], '%d/%m/%Y %H:%M:%S')
                fechamento = datetime.strptime(row["hora_fechamento"], '%d/%m/%Y %H:%M:%S')
                tempo_util = calculate_working_hours(abertura, fechamento)
                return tempo_util.total_seconds()
            except Exception as e:
                return None
        else:
            return None
    df_period["tempo_util_seg"] = df_period.apply(calc_tempo, axis=1)
    df_valid = df_period.dropna(subset=["tempo_util_seg"])
    if not df_valid.empty:
        tempo_medio_ubs = df_valid.groupby("ubs")["tempo_util_seg"].mean().reset_index()
        tempo_medio_ubs["Tempo Médio"] = tempo_medio_ubs["tempo_util_seg"].apply(
            lambda x: f"{int(x//3600)}h {int((x%3600)//60)}m"
        )
        st.markdown("#### Tempo Médio de Atendimento por UBS (horas úteis)")
        st.dataframe(tempo_medio_ubs[["ubs", "Tempo Médio"]])
        fig3, ax3 = plt.subplots(figsize=(8,4))
        ax3.bar(tempo_medio_ubs["ubs"], tempo_medio_ubs["tempo_util_seg"], color='green')
        ax3.set_xlabel("UBS")
        ax3.set_ylabel("Tempo Médio (segundos)")
        ax3.set_title("Tempo Médio de Atendimento por UBS")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig3)
        
        media_global = df_valid["tempo_util_seg"].mean()
        horas_global = int(media_global // 3600)
        minutos_global = int((media_global % 3600) // 60)
        st.markdown(f"**Tempo médio global de atendimento (horas úteis):** {horas_global}h {minutos_global}m")
    else:
        st.write("Nenhum chamado finalizado no período para calcular tempo médio.")
    
    # Estatística 4: Chamados por UBS por Mês (detalhado)
    chamados_ubs_detalhado = df_period.groupby(["ubs", "mes"]).size().reset_index(name="qtd_chamados")
    st.markdown("#### Chamados por UBS por Mês (detalhado)")
    st.dataframe(chamados_ubs_detalhado)
    
    # Geração de PDF para Relatório de Chamados
    if st.button("Gerar Relatório de Chamados em PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Relatório de Chamados - Gestão de Parque de Informática", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", ln=True)
        if filtro_ubs:
            pdf.cell(0, 10, f"UBS: {', '.join(filtro_ubs)}", ln=True)
        pdf.ln(5)
        pdf.cell(0, 10, "Chamados por UBS por Mês:", ln=True)
        for idx, row in chamados_ubs_detalhado.iterrows():
            pdf.cell(0, 8, f"UBS: {row['ubs']} | Mês: {row['mes']} | Qtd: {row['qtd_chamados']}", ln=True)
        pdf.ln(5)
        pdf.cell(0, 10, "Chamados por Setor:", ln=True)
        for idx, row in chamados_setor.iterrows():
            pdf.cell(0, 8, f"Setor: {row['setor']} | Qtd: {row['qtd_chamados']}", ln=True)
        pdf.ln(5)
        if not df_valid.empty:
            pdf.cell(0, 10, "Tempo Médio de Atendimento por UBS (horas úteis):", ln=True)
            for idx, row in tempo_medio_ubs.iterrows():
                pdf.cell(0, 8, f"UBS: {row['ubs']} | Tempo Médio: {row['Tempo Médio']}", ln=True)
            pdf.ln(5)
            pdf.cell(0, 10, f"Tempo médio global (horas úteis): {horas_global}h {minutos_global}m", ln=True)
        pdf_output = pdf.output(dest="S")
        st.download_button("Baixar Relatório de Chamados em PDF", data=pdf_output, file_name="relatorio_chamados.pdf", mime="application/pdf")
    
    # Relatório do Inventário
    st.markdown("### Relatório do Inventário")
    inventario_data = get_machines_from_inventory()
    if inventario_data:
        df_inv = pd.DataFrame(inventario_data)
        gb_inv = GridOptionsBuilder.from_dataframe(df_inv)
        gb_inv.configure_pagination(paginationAutoPageSize=True)
        gb_inv.configure_default_column(filter=True, sortable=True)
        grid_options_inv = gb_inv.build()
        AgGrid(df_inv, gridOptions=grid_options_inv, height=400, fit_columns_on_grid_load=True)
        if st.button("Gerar Relatório do Inventário em PDF"):
            pdf_inv = FPDF()
            pdf_inv.add_page()
            pdf_inv.set_font("Arial", "B", 16)
            pdf_inv.cell(0, 10, "Relatório do Inventário - Gestão de Parque de Informática", ln=True, align="C")
            pdf_inv.ln(10)
            pdf_inv.set_font("Arial", "", 12)
            for idx, row in df_inv.iterrows():
                linha = (f"Patrimônio: {row.get('numero_patrimonio')} | Tipo: {row.get('tipo')} | "
                         f"Marca: {row.get('marca')} | Modelo: {row.get('modelo')} | "
                         f"UBS: {row.get('localizacao')} | Setor: {row.get('setor')}")
                pdf_inv.multi_cell(0, 8, linha)
            pdf_inv_output = pdf_inv.output(dest="S")
            st.download_button("Baixar Relatório do Inventário em PDF", data=pdf_inv_output, file_name="relatorio_inventario.pdf", mime="application/pdf")
    else:
        st.write("Nenhum item de inventário encontrado.")

def exportar_dados_page():
    st.subheader("Exportar Dados")
    st.markdown("### Exportar Chamados em CSV")
    chamados = list_chamados()
    if chamados:
        df_chamados = pd.DataFrame(chamados)
        csv_chamados = df_chamados.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar Chamados CSV", data=csv_chamados, file_name="chamados.csv", mime="text/csv")
    else:
        st.write("Nenhum chamado para exportar.")
    
    st.markdown("### Exportar Inventário em CSV")
    inventario_data = get_machines_from_inventory()
    if inventario_data:
        df_inv = pd.DataFrame(inventario_data)
        csv_inv = df_inv.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar Inventário CSV", data=csv_inv, file_name="inventario.csv", mime="text/csv")
    else:
        st.write("Nenhum item de inventário para exportar.")

def sair_page():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Você saiu.")

# Mapeamento das páginas
pages = {
    "Login": login_page,
    "Dashboard": dashboard_page,
    "Abrir Chamado": abrir_chamado_page,
    "Chamados Técnicos": chamados_tecnicos_page,
    "Inventário": inventario_page,
    "Estoque": estoque_page,
    "Administração": administracao_page,
    "Relatórios": relatorios_page,
    "Exportar Dados": exportar_dados_page,
    "Sair": sair_page,
}

if selected in pages:
    pages[selected]()
else:
    st.write("Página não encontrada.")