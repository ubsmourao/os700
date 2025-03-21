# OS700.py
import streamlit as st
import os
import logging
import pandas as pd
from streamlit_option_menu import option_menu

# Importando funções refatoradas
from database import check_or_create_admin_user
from autenticacao import authenticate, add_user, list_users, change_password
from chamados import add_chamado, list_chamados, list_chamados_em_aberto, finalizar_chamado, get_chamado_by_protocolo, buscar_no_inventario_por_patrimonio
from inventario import add_machine_to_inventory, show_inventory_list, show_maintenance_history, add_maintenance_history
from ubs import get_ubs_list, manage_ubs
from setores import get_setores_list, manage_setores

# Configura o logging
logging.basicConfig(level=logging.INFO)

# Inicializa o admin se necessário
check_or_create_admin_user()

# Inicializa o session_state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ''

st.set_page_config(page_title="Gestão de Parque de Informática", layout="wide")
logo_path = os.getenv("LOGO_PATH", "infocustec.png")
if os.path.exists(logo_path):
    st.image(logo_path, width=300)
else:
    st.warning("Logotipo não encontrado.")

st.title("Gestão de Parque de Informática - UBS ITAPIPOCA")

# Define o menu conforme privilégios
if st.session_state.logged_in and authenticate(st.session_state.username, "dummy"):  # is_admin pode ser usado aqui
    menu_options = ['Login', 'Abrir Chamado', 'Administração', 'Relatórios']
else:
    menu_options = ['Login', 'Abrir Chamado']

selected = option_menu(None, menu_options, orientation="horizontal")

def login():
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

def abrir_chamado():
    if not st.session_state.logged_in:
        st.warning("Faça login para abrir um chamado.")
        return
    st.subheader("Abrir Chamado")
    patrimonio = st.text_input("Número de Patrimônio")
    machine_info = None
    if patrimonio:
        machine_info = buscar_no_inventario_por_patrimonio(patrimonio)
        if machine_info:
            st.write(f"Máquina: {machine_info['tipo']} - {machine_info['marca']} {machine_info['modelo']}")
            ubs_selecionada = machine_info["localizacao"]
            setor = machine_info["setor"]
        else:
            st.error("Patrimônio não encontrado. Preencha manualmente.")
            ubs_selecionada = st.selectbox("UBS", get_ubs_list())
            setor = st.selectbox("Setor", get_setores_list())
    else:
        ubs_selecionada = st.selectbox("UBS", get_ubs_list())
        setor = st.selectbox("Setor", get_setores_list())
    tipo_defeito = st.selectbox("Tipo de Defeito", ["Defeito X", "Defeito Y", "Outros"])
    problema = st.text_area("Descreva o problema")
    if st.button("Abrir Chamado"):
        protocolo = add_chamado(st.session_state.username, ubs_selecionada, setor, tipo_defeito, problema, patrimonio=patrimonio)
        if protocolo:
            st.success(f"Chamado aberto! Protocolo: {protocolo}")
        else:
            st.error("Erro ao abrir chamado.")

def administracao():
    if not st.session_state.logged_in:
        st.warning("Faça login para acessar a administração.")
        return
    st.subheader("Administração")
    opcao = st.selectbox("Opções", ["Cadastro de Usuário", "Cadastro de Máquina", "Lista de Usuários", "Gerenciar UBSs", "Gerenciar Setores"])
    if opcao == "Cadastro de Usuário":
        novo_user = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Senha", type="password")
        is_admin = st.checkbox("Administrador")
        if st.button("Cadastrar"):
            if add_user(novo_user, nova_senha, is_admin):
                st.success("Usuário cadastrado!")
            else:
                st.error("Erro ao cadastrar usuário ou usuário já existe.")
    elif opcao == "Cadastro de Máquina":
        tipo = st.selectbox("Tipo", ["Computador", "Impressora", "Outro"])
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        num_serie = st.text_input("Número de Série (opcional)")
        patrimonio = st.text_input("Patrimônio")
        status = st.selectbox("Status", ["Ativo", "Em Manutenção", "Inativo"])
        ubs = st.selectbox("UBS", get_ubs_list())
        setor = st.selectbox("Setor", get_setores_list())
        propria_locada = st.selectbox("Própria/Locada", ["Própria", "Locada"])
        if st.button("Cadastrar Máquina"):
            add_machine_to_inventory(tipo, marca, modelo, num_serie, status, ubs, propria_locada, patrimonio, setor)
    elif opcao == "Lista de Usuários":
        users = list_users()
        st.write(users)
    elif opcao == "Gerenciar UBSs":
        manage_ubs()
    elif opcao == "Gerenciar Setores":
        manage_setores()

if selected == "Login":
    login()
elif selected == "Abrir Chamado":
    abrir_chamado()
elif selected == "Administração":
    administracao()
