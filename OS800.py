import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz
from streamlit_option_menu import option_menu

# Importações dos módulos internos (assumindo que eles estão disponíveis)
from chamados import list_chamados, chamados_tecnicos_page
from inventario import show_inventory_list, cadastro_maquina, dashboard_inventario
from ubs import get_ubs_list, manage_ubs
from setores import manage_setores
from estoque import manage_estoque
from autenticacao import authenticate, add_user, is_admin, list_users

# Configura a página (incluindo o favicon e layout)
st.set_page_config(page_title="Gestão de Parque de Informática", 
                   page_icon="gear.png", 
                   layout="wide")

# Inicializa o estado de login se ainda não estiver definido
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# Define as opções do menu de acordo com o status de login e perfil
if st.session_state["logged_in"]:
    if is_admin(st.session_state["username"]):
        menu_options = ["Dashboard", "Chamados Técnicos", "Inventário", "Estoque", "Administração", "Sair"]
    else:
        menu_options = ["Chamados Técnicos", "Inventário", "Sair"]
else:
    menu_options = ["Login"]

# Cria o menu horizontal usando streamlit-option-menu
selected = option_menu(
    None,
    options=menu_options,
    icons=["speedometer", "chat-left-text", "clipboard-data", "box-seam", "gear", "box-arrow-right"],
    orientation="horizontal",
    menu_icon="cast",
    default_index=0
)

# Define as páginas de acordo com a opção selecionada
if selected == "Login":
    st.subheader("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if not username or not password:
            st.error("Preencha os dados corretamente.")
        elif authenticate(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"Bem-vindo, {username}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")

elif selected == "Dashboard":
    st.subheader("Dashboard")
    # Exemplo: usando chamados para exibir um gráfico de tendência com Plotly
    chamados = list_chamados()
    if chamados:
        df = pd.DataFrame(chamados)
        # Converte a coluna "hora_abertura" para datetime e cria uma coluna com o mês
        df['hora_abertura_dt'] = pd.to_datetime(df['hora_abertura'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        df['mes'] = df['hora_abertura_dt'].dt.to_period("M").astype(str)
        trend = df.groupby("mes").size().reset_index(name="qtd")
        st.write("### Tendência de Chamados por Mês")
        fig = px.line(trend, x="mes", y="qtd", markers=True,
                      title="Tendência de Chamados")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum chamado registrado.")

elif selected == "Chamados Técnicos":
    # Chama a função já existente que exibe os chamados técnicos (por exemplo, com AgGrid)
    chamados_tecnicos_page()

elif selected == "Inventário":
    st.subheader("Inventário")
    inventario_opt = st.radio("Opções de Inventário", 
                              ["Listar Inventário", "Cadastrar Máquina", "Dashboard Inventário"])
    if inventario_opt == "Listar Inventário":
        show_inventory_list()
    elif inventario_opt == "Cadastrar Máquina":
        cadastro_maquina()
    else:
        dashboard_inventario()

elif selected == "Estoque":
    st.subheader("Estoque")
    manage_estoque()

elif selected == "Administração":
    st.subheader("Administração")
    admin_opt = st.selectbox("Opções de Administração", 
                             ["Cadastro de Usuário", "Gerenciar UBSs", "Gerenciar Setores", "Lista de Usuários"])
    if admin_opt == "Cadastro de Usuário":
        novo_user = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Senha", type="password")
        admin_flag = st.checkbox("Administrador")
        if st.button("Cadastrar Usuário"):
            if add_user(novo_user, nova_senha, admin_flag):
                st.success("Usuário cadastrado com sucesso!")
            else:
                st.error("Erro ao cadastrar usuário ou usuário já existe.")
    elif admin_opt == "Gerenciar UBSs":
        manage_ubs()
    elif admin_opt == "Gerenciar Setores":
        manage_setores()
    else:
        usuarios = list_users()
        if usuarios:
            st.table(usuarios)
        else:
            st.write("Nenhum usuário cadastrado.")

elif selected == "Sair":
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.experimental_rerun()
