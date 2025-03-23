import streamlit as st
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
from fpdf import FPDF
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO

import pytz
FORTALEZA_TZ = pytz.timezone("America/Fortaleza")  # Timezone de Fortaleza, CE

# Importação das funções de autenticacao
from autenticacao import (
    authenticate,
    add_user,
    is_admin,
    list_users,
    remove_user,
    update_user_role,
    change_password
)

# Demais módulos do app
from chamados import (
    add_chamado,
    get_chamado_by_protocolo,
    list_chamados,
    list_chamados_em_aberto,
    buscar_no_inventario_por_patrimonio,
    finalizar_chamado,
    calculate_working_hours
)
from inventario import show_inventory_list, cadastro_maquina, get_machines_from_inventory
from ubs import get_ubs_list
from setores import get_setores_list
from estoque import manage_estoque, get_estoque

# Configuração de logging
logging.basicConfig(level=logging.INFO)

# Inicialização de sessão
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# Configuração da página
st.set_page_config(page_title="Gestão de Parque de Informática", layout="wide")

logo_path = os.getenv("LOGO_PATH", "infocustec.png")
if os.path.exists(logo_path):
    st.image(logo_path, width=300)
else:
    st.warning("Logotipo não encontrado.")

st.title("Gestão de Parque de Informática - UBS ITAPIPOCA")

# --- Função Auxiliar para Exibir Chamado ---
def exibir_chamado(chamado):
    st.markdown("### Detalhes do Chamado")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**ID:** {chamado.get('id', 'N/A')}")
        st.markdown(f"**Usuário:** {chamado.get('username', 'N/A')}")
        st.markdown(f"**UBS:** {chamado.get('ubs', 'N/A')}")
        st.markdown(f"**Setor:** {chamado.get('setor', 'N/A')}")
        st.markdown(f"**Protocolo:** {chamado.get('protocolo', 'N/A')}")
    with col2:
        st.markdown(f"**Tipo de Defeito:** {chamado.get('tipo_defeito', 'N/A')}")
        st.markdown(f"**Problema:** {chamado.get('problema', 'N/A')}")
        st.markdown(f"**Hora de Abertura:** {chamado.get('hora_abertura', 'Em aberto')}")
        st.markdown(f"**Hora de Fechamento:** {chamado.get('hora_fechamento', 'Em aberto')}")
    if chamado.get("solucao"):
        st.markdown("### Solução")
        st.markdown(chamado["solucao"])

def build_menu():
    if st.session_state["logged_in"]:
        if is_admin(st.session_state["username"]):
            return [
                "Dashboard",
                "Abrir Chamado",
                "Buscar Chamado",
                "Chamados Técnicos",
                "Inventário",
                "Estoque",
                "Administração",
                "Relatórios",
                "Exportar Dados",
                "Sair"
            ]
        else:
            return [
                "Abrir Chamado",
                "Buscar Chamado",
                "Sair"
            ]
    else:
        return ["Login"]

menu_options = build_menu()
selected = option_menu(
    menu_title=None,
    options=menu_options,
    icons=[
        "speedometer", "chat-left-text", "search", "card-list",
        "clipboard-data", "box-seam", "gear", "bar-chart-line",
        "download", "box-arrow-right"
    ],
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
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
        else:
            st.error("Usuário ou senha incorretos.")

def dashboard_page():
    st.subheader("Dashboard - Administrativo")
    agora_fortaleza = datetime.now(FORTALEZA_TZ)
    st.markdown(f"**Horário local (Fortaleza):** {agora_fortaleza.strftime('%d/%m/%Y %H:%M:%S')}")

    chamados = list_chamados()
    total_chamados = len(chamados) if chamados else 0
    abertos = len(list_chamados_em_aberto()) if chamados else 0
    col1, col2 = st.columns(2)
    col1.metric("Total de Chamados", total_chamados)
    col2.metric("Chamados Abertos", abertos)
    
    atrasados = []
    if chamados:
        for c in chamados:
            if c.get("hora_fechamento") is None:
                try:
                    abertura = datetime.strptime(c["hora_abertura"], '%d/%m/%Y %H:%M:%S')
                    agora_local = datetime.now(FORTALEZA_TZ)
                    tempo_util = calculate_working_hours(abertura, agora_local)
                    if tempo_util > timedelta(hours=48):
                        atrasados.append(c)
                except Exception:
                    pass
    if atrasados:
        st.warning(f"Atenção: {len(atrasados)} chamados abertos com mais de 48h úteis!")
    
    if chamados:
        df = pd.DataFrame(chamados)
        df["hora_abertura_dt"] = pd.to_datetime(df["hora_abertura"], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        df["mes"] = df["hora_abertura_dt"].dt.to_period("M").astype(str)
        tendencia = df.groupby("mes").size().reset_index(name="qtd")
        fig, ax = plt.subplots(figsize=(8,4))
        ax.plot(tendencia["mes"], tendencia["qtd"], marker="o")
        ax.set_xlabel("Mês")
        ax.set_ylabel("Quantidade de Chamados")
        ax.set_title("Tendência de Chamados")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.write("Nenhum chamado registrado.")

def abrir_chamado_page():
    st.subheader("Abrir Chamado Técnico")
    patrimonio = st.text_input("Número de Patrimônio (opcional)")
    data_agendada = st.date_input("Data Agendada para Manutenção (opcional)")
    machine_info = None
    machine_type = None
    ubs_selecionada = None
    setor = None
    if patrimonio:
        machine_info = buscar_no_inventario_por_patrimonio(patrimonio)
        if machine_info:
            st.write(f"Máquina: {machine_info['tipo']} - {machine_info['marca']} {machine_info['modelo']}")
            st.write(f"UBS: {machine_info['localizacao']} | Setor: {machine_info['setor']}")
            ubs_selecionada = machine_info["localizacao"]
            setor = machine_info["setor"]
            machine_type = machine_info["tipo"]
        else:
            st.error("Patrimônio não encontrado. Cadastre a máquina antes.")
            st.stop()
    else:
        ubs_selecionada = st.selectbox("UBS", get_ubs_list())
        setor = st.selectbox("Setor", get_setores_list())
        machine_type = st.selectbox("Tipo de Máquina", ["Computador", "Impressora", "Outro"])
    if machine_type == "Computador":
        defect_options = [
            "Computador não liga", "Computador lento", "Tela azul", "Sistema travando",
            "Erro de disco", "Problema com atualização", "Desligamento inesperado",
            "Problema com internet", "Problema com Wi-Fi", "Sem conexão de rede",
            "Mouse não funciona", "Teclado não funciona"
        ]
    elif machine_type == "Impressora":
        defect_options = [
            "Impressora não imprime", "Impressão borrada", "Toner vazio",
            "Troca de toner", "Papel enroscado", "Erro de conexão com a impressora"
        ]
    else:
        defect_options = ["Solicitação de suporte geral", "Outros tipos de defeito"]
    tipo_defeito = st.selectbox("Tipo de Defeito/Solicitação", defect_options)
    problema = st.text_area("Descreva o problema ou solicitação")
    if st.button("Abrir Chamado"):
        agendamento = data_agendada.strftime('%d/%m/%Y') if data_agendada else None
        protocolo = add_chamado(
            st.session_state["username"],
            ubs_selecionada,
            setor,
            tipo_defeito,
            problema + (f" | Agendamento: {agendamento}" if agendamento else ""),
            patrimonio=patrimonio
        )
        if protocolo:
            st.success(f"Chamado aberto! Protocolo: {protocolo}")
        else:
            st.error("Erro ao abrir chamado.")

def buscar_chamado_page():
    st.subheader("Buscar Chamado")
    protocolo = st.text_input("Informe o número de protocolo do chamado")
    if st.button("Buscar"):
        if protocolo:
            chamado = get_chamado_by_protocolo(protocolo)
            if chamado:
                st.write("Chamado encontrado:")
                exibir_chamado(chamado)
            else:
                st.error("Chamado não encontrado.")
        else:
            st.warning("Informe um protocolo.")

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
            except Exception:
                return "Erro"
        else:
            return "Em aberto"

    df["Tempo Util"] = df.apply(calcula_tempo, axis=1)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(filter=True, sortable=True)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_grid_options(domLayout='normal')
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
    # Exemplo de inventário
    # ...
    st.write("Em desenvolvimento ou conforme já implementado no seu app.")
    # Se quiser integrar as lógicas de 'show_inventory_list' e 'cadastro_maquina', faça aqui.

def estoque_page():
    manage_estoque()

def administracao_page():
    st.subheader("Administração")
    admin_option = st.selectbox("Opções de Administração", [
        "Cadastro de Usuário",
        "Remover Usuário",
        "Alterar Função de Usuário",
        "Alterar Senha de Usuário",
        "Lista de Usuários",
        "Gerenciar UBSs",
        "Gerenciar Setores"
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

    elif admin_option == "Remover Usuário":
        usuarios = list_users()
        if usuarios:
            nomes_usuarios = [u[0] for u in usuarios]
            target_user = st.selectbox("Selecione o usuário para remover", nomes_usuarios)
            if st.button("Remover Usuário"):
                if target_user:
                    remove_user(st.session_state["username"], target_user)
                else:
                    st.warning("Selecione um usuário.")
        else:
            st.write("Nenhum usuário cadastrado para remover.")

    elif admin_option == "Alterar Função de Usuário":
        usuarios = list_users()
        if usuarios:
            nomes_usuarios = [u[0] for u in usuarios]
            target_user = st.selectbox("Selecione o usuário para alterar função", nomes_usuarios)
            nova_role = st.selectbox("Nova função", ["user", "admin"])
            if st.button("Atualizar Função"):
                if target_user:
                    update_user_role(st.session_state["username"], target_user, nova_role)
                else:
                    st.warning("Selecione um usuário.")
        else:
            st.write("Nenhum usuário cadastrado para alterar função.")

    elif admin_option == "Alterar Senha de Usuário":
        usuarios = list_users()
        if usuarios:
            nomes_usuarios = [u[0] for u in usuarios]
            target_user = st.selectbox("Selecione o usuário para alterar senha", nomes_usuarios)
            nova_senha = st.text_input("Nova senha", type="password")
            if st.button("Atualizar Senha"):
                if nova_senha:
                    from autenticacao import change_password
                    # Aqui estamos assumindo que "change_password" exige a senha antiga,
                    # mas se quiser trocar sem exigir a senha antiga, faça outra função ou
                    # use a que já criamos (ex.: "change_user_password" se existisse).
                    # Se preferir forçar sem senha antiga, crie uma "force_change_password" etc.
                    
                    # Se quiser forçar sem a senha antiga, use uma outra função do autenticacao,
                    # ex: "change_user_password(st.session_state['username'], target_user, nova_senha)"
                    # Precisaria estar implementada. 
                    
                    # Se "change_password" exige old_password, podemos passar "" e adaptar a lógica.
                    st.warning("Esta função 'change_password' exige a senha antiga. Adapte se quiser forçar.")
                else:
                    st.warning("Informe a nova senha.")
        else:
            st.write("Nenhum usuário cadastrado para alterar senha.")

    elif admin_option == "Lista de Usuários":
        usuarios = list_users()
        if usuarios:
            st.table(usuarios)
        else:
            st.write("Nenhum usuário cadastrado.")

    elif admin_option == "Gerenciar UBSs":
        from ubs import manage_ubs
        manage_ubs()

    elif admin_option == "Gerenciar Setores":
        from setores import manage_setores
        manage_setores()

def relatorios_page():
    st.subheader("Relatórios Completos - Estatísticas")
    st.markdown("### (Exemplo)")

    # Exemplo de relatório, caso já implementado, exibir os chamados e gerar PDF etc.
    st.write("Relatórios detalhados de chamados, tempo médio, etc.")

def exportar_dados_page():
    st.subheader("Exportar Dados")
    st.markdown("### (Exemplo)")

    # Exemplo de exportar CSV, etc.

def sair_page():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.success("Você saiu.")

# Mapeamento das páginas
pages = {
    "Login": login_page,
    "Dashboard": dashboard_page,
    "Abrir Chamado": abrir_chamado_page,
    "Buscar Chamado": buscar_chamado_page,
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