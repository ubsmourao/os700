# OS700.py
import streamlit as st
import os
import logging
import pandas as pd
from streamlit_option_menu import option_menu

# Importando funções dos módulos refatorados
from autenticacao import authenticate, add_user, is_admin, list_users
from chamados import add_chamado, list_chamados, list_chamados_em_aberto, finalizar_chamado, get_chamado_by_protocolo, buscar_no_inventario_por_patrimonio
from inventario import add_machine_to_inventory, show_inventory_list, show_maintenance_history, add_maintenance_history
from ubs import get_ubs_list, manage_ubs
from setores import get_setores_list, manage_setores

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)

# Inicializando variáveis de sessão
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# Configuração da página
st.set_page_config(page_title="Gestão de Parque de Informática", layout="wide")
logo_path = os.getenv("LOGO_PATH", "infocustec.png")
if os.path.exists(logo_path):
    st.image(logo_path, width=300)
else:
    st.warning("Logotipo não encontrado.")

st.title("Gestão de Parque de Informática - UBS ITAPIPOCA")

# Define as opções do menu conforme o status do login e privilégios
if st.session_state.logged_in:
    if is_admin(st.session_state.username):
        menu_options = ['Home', 'Abrir Chamado', 'Administração', 'Relatórios', 'Sair']
    else:
        menu_options = ['Home', 'Abrir Chamado', 'Sair']
else:
    menu_options = ['Login']

selected = option_menu("Menu", menu_options, orientation="horizontal")

# Função de login
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

# Função de logout
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Você saiu.")

# Função para abrir chamado com os tipos de defeito originais
def abrir_chamado():
    if not st.session_state.logged_in:
        st.warning("Você precisa estar logado para abrir um chamado.")
        return
    st.subheader("Abrir Chamado")
    
    patrimonio = st.text_input("Número de Patrimônio")
    machine_info = None
    machine_type = None
    
    if patrimonio:
        machine_info = buscar_no_inventario_por_patrimonio(patrimonio)
        if machine_info:
            st.write(f"Máquina encontrada: {machine_info['tipo']} - {machine_info['marca']} {machine_info['modelo']}")
            st.write(f"UBS: {machine_info['localizacao']} | Setor: {machine_info['setor']}")
            ubs_selecionada = machine_info["localizacao"]
            setor = machine_info["setor"]
            machine_type = machine_info["tipo"]
        else:
            st.error("Patrimônio não encontrado no inventário. Preencha os dados manualmente.")
            ubs_selecionada = st.selectbox("UBS", get_ubs_list())
            setor = st.selectbox("Setor", get_setores_list())
            machine_type = st.selectbox("Tipo de Máquina", ["Computador", "Impressora", "Outro"])
    else:
        ubs_selecionada = st.selectbox("UBS", get_ubs_list())
        setor = st.selectbox("Setor", get_setores_list())
        machine_type = st.selectbox("Tipo de Máquina", ["Computador", "Impressora", "Outro"])
    
    # Definir os tipos de defeito com os nomes originais
    if machine_type == "Computador":
        defect_options = [
            "Computador não liga",
            "Computador lento",
            "Tela azul",
            "Sistema travando",
            "Erro de disco",
            "Problema com atualização",
            "Desligamento inesperado",
            "Problemas de internet",
            "Problema com Wi-Fi",
            "Sem conexão de rede",
            "Mouse não funciona",
            "Teclado não funciona"
        ]
    elif machine_type == "Impressora":
        defect_options = [
            "Impressora não imprime",
            "Impressão borrada",
            "Toner vazio",
            "Troca de toner",
            "Papel enroscado",
            "Erro de conexão com a impressora"
        ]
    else:
        defect_options = [
            "Solicitação de suporte geral",
            "Outros tipos de defeito"
        ]
    
    tipo_defeito = st.selectbox("Tipo de Defeito/Solicitação", defect_options)
    problema = st.text_area("Descreva o problema ou solicitação")
    
    if st.button("Abrir Chamado"):
        protocolo = add_chamado(
            st.session_state.username,
            ubs_selecionada,
            setor,
            tipo_defeito,
            problema,
            patrimonio=patrimonio
        )
        if protocolo:
            st.success(f"Chamado aberto com sucesso! Protocolo: {protocolo}")
        else:
            st.error("Erro ao abrir chamado.")

# Função de administração para usuários administradores
def administracao():
    if not st.session_state.logged_in or not is_admin(st.session_state.username):
        st.warning("Você precisa estar logado como admin para acessar esta área.")
        return
    st.subheader("Administração")
    opcao = st.selectbox("Opções de Administração", ["Cadastro de Usuário", "Cadastro de Máquina", "Lista de Usuários", "Gerenciar UBSs", "Gerenciar Setores"])
    
    if opcao == "Cadastro de Usuário":
        novo_user = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Senha", type="password")
        admin_check = st.checkbox("Administrador")
        if st.button("Cadastrar Usuário"):
            if add_user(novo_user, nova_senha, admin_check):
                st.success("Usuário cadastrado com sucesso!")
            else:
                st.error("Erro ao cadastrar usuário ou usuário já existe.")
    elif opcao == "Cadastro de Máquina":
        tipo = st.selectbox("Tipo de Equipamento", ["Computador", "Impressora", "Monitor", "Outro"])
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        num_serie = st.text_input("Número de Série (Opcional)")
        patrimonio = st.text_input("Número de Patrimônio")
        status = st.selectbox("Status", ["Ativo", "Em Manutenção", "Inativo"])
        ubs = st.selectbox("UBS", get_ubs_list())
        setor = st.selectbox("Setor", get_setores_list())
        propria_locada = st.selectbox("Própria ou Locada", ["Própria", "Locada"])
        if st.button("Cadastrar Máquina"):
            add_machine_to_inventory(tipo, marca, modelo, num_serie, status, ubs, propria_locada, patrimonio, setor)
    elif opcao == "Lista de Usuários":
        users = list_users()
        st.write("Lista de Usuários:")
        st.table(users)
    elif opcao == "Gerenciar UBSs":
        manage_ubs()
    elif opcao == "Gerenciar Setores":
        manage_setores()

# Função de relatórios (exemplo simples listando os chamados)
def relatorios():
    st.subheader("Relatórios")
    chamados = list_chamados()
    if chamados:
        df = pd.DataFrame(chamados)
        st.dataframe(df)
    else:
        st.write("Nenhum chamado encontrado.")

# Exibição da página conforme a opção selecionada no menu
if selected == "Login":
    login()
elif selected == "Abrir Chamado":
    abrir_chamado()
elif selected == "Administração":
    administracao()
elif selected == "Relatórios":
    relatorios()
elif selected == "Sair":
    logout()
elif selected == "Home":
    st.subheader("Bem-vindo!")
    st.write("Selecione uma opção no menu para começar.")
