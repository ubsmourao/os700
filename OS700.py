import streamlit as st
import os
import logging
import pandas as pd
from streamlit_option_menu import option_menu

# Importacao dos modulos
from autenticacao import authenticate, add_user, is_admin, list_users
from chamados import add_chamado, list_chamados, list_chamados_em_aberto, finalizar_chamado, buscar_no_inventario_por_patrimonio
from inventario import show_inventory_list, cadastro_maquina, get_machines_from_inventory
from ubs import get_ubs_list
from setores import get_setores_list

# Configuracao do logging
logging.basicConfig(level=logging.INFO)

# Inicializacao das variaveis de sessao
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Configuracao da pagina
st.set_page_config(page_title="Gestao de Parque de Informatica", layout="wide")
logo_path = os.getenv("LOGO_PATH", "infocustec.png")
if os.path.exists(logo_path):
    st.image(logo_path, width=300)
else:
    st.warning("Logotipo nao encontrado.")

st.title("Gestao de Parque de Informatica - UBS ITAPIPOCA")

# Definicao do menu
if st.session_state.logged_in:
    if is_admin(st.session_state.username):
        menu_options = ["Home", "Abrir Chamado", "Chamados Tecnicos", "Inventario", "Estoque", "Administracao", "Relatorios", "Sair"]
    else:
        menu_options = ["Home", "Abrir Chamado", "Chamados Tecnicos", "Inventario", "Estoque", "Relatorios", "Sair"]
else:
    menu_options = ["Login"]

selected = option_menu("Menu", menu_options, orientation="horizontal")

# Funcoes do aplicativo

def login():
    st.subheader("Login")
    username = st.text_input("Usuario")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if not username or not password:
            st.error("Preencha todos os campos.")
        elif authenticate(username, password):
            st.success(f"Bem-vindo, {username}!")
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.error("Usuario ou senha incorretos.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Voce saiu.")

def home():
    st.subheader("Bem-vindo!")
    st.write("Selecione uma opcao no menu para comecar.")

def abrir_chamado():
    st.subheader("Abrir Chamado Tecnico")
    patrimonio = st.text_input("Numero de Patrimonio (opcional)")
    machine_info = None
    machine_type = None
    ubs_selecionada = None
    setor = None

    if patrimonio:
        machine_info = buscar_no_inventario_por_patrimonio(patrimonio)
        if machine_info:
            st.write(f"Maquina encontrada: {machine_info['tipo']} - {machine_info['marca']} {machine_info['modelo']}")
            st.write(f"UBS: {machine_info['localizacao']} | Setor: {machine_info['setor']}")
            ubs_selecionada = machine_info["localizacao"]
            setor = machine_info["setor"]
            machine_type = machine_info["tipo"]
        else:
            st.info("Patrimonio nao encontrado no inventario. A maquina sera cadastrada automaticamente.")
            default_ubs = st.selectbox("Selecione a UBS para cadastro automatico", get_ubs_list())
            default_setor = st.selectbox("Selecione o Setor para cadastro automatico", get_setores_list())
            default_tipo = "Nao informado"
            default_marca = "Nao informado"
            default_modelo = "Nao informado"
            from inventario import add_machine_to_inventory
            add_machine_to_inventory(default_tipo, default_marca, default_modelo, None, "Ativo", default_ubs, "Nao informado", patrimonio, default_setor)
            st.success("Maquina cadastrada automaticamente no inventario.")
            machine_info = buscar_no_inventario_por_patrimonio(patrimonio)
            if machine_info:
                machine_type = machine_info["tipo"]
                ubs_selecionada = machine_info["localizacao"]
                setor = machine_info["setor"]
            else:
                st.error("Erro ao recuperar os dados da maquina cadastrada.")
                st.stop()
    else:
        ubs_selecionada = st.selectbox("UBS", get_ubs_list())
        setor = st.selectbox("Setor", get_setores_list())
        machine_type = st.selectbox("Tipo de Maquina", ["Computador", "Impressora", "Outro"])

    if machine_type == "Computador":
        defect_options = [
            "Computador nao liga",
            "Computador lento",
            "Tela azul",
            "Sistema travando",
            "Erro de disco",
            "Problema com atualizacao",
            "Desligamento inesperado",
            "Problemas de internet",
            "Problema com Wi-Fi",
            "Sem conexao de rede",
            "Mouse nao funciona",
            "Teclado nao funciona"
        ]
    elif machine_type == "Impressora":
        defect_options = [
            "Impressora nao imprime",
            "Impressao borrada",
            "Toner vazio",
            "Troca de toner",
            "Papel enroscado",
            "Erro de conexao com a impressora"
        ]
    else:
        defect_options = [
            "Solicitacao de suporte geral",
            "Outros tipos de defeito"
        ]
    
    tipo_defeito = st.selectbox("Tipo de Defeito/Solicitacao", defect_options)
    problema = st.text_area("Descreva o problema ou solicitacao")
    
    if st.button("Abrir Chamado"):
        protocolo = add_chamado(st.session_state.username, ubs_selecionada, setor, tipo_defeito, problema, patrimonio=patrimonio)
        if protocolo:
            st.success(f"Chamado aberto com sucesso! Protocolo: {protocolo}")
        else:
            st.error("Erro ao abrir chamado.")

def chamados_tecnicos():
    st.subheader("Chamados Tecnicos")
    chamados = list_chamados()
    if chamados:
        st.dataframe(pd.DataFrame(chamados))
    else:
        st.write("Nenhum chamado tecnico encontrado.")

def inventario():
    st.subheader("Inventario")
    opcao = st.radio("Selecione uma opcao:", ["Listar Inventario", "Cadastrar Maquina"])
    if opcao == "Listar Inventario":
        from inventario import show_inventory_list
        show_inventory_list()
    else:
        from inventario import cadastro_maquina
        cadastro_maquina()

def estoque():
    from estoque import manage_estoque
    manage_estoque()

def administracao():
    st.subheader("Administracao")
    admin_option = st.selectbox("Opcoes de Administracao", [
        "Cadastro de Usuario",
        "Gerenciar UBSs",
        "Gerenciar Setores",
        "Lista de Usuarios"
    ])
    
    if admin_option == "Cadastro de Usuario":
        novo_user = st.text_input("Novo Usuario")
        nova_senha = st.text_input("Senha", type="password")
        admin_flag = st.checkbox("Administrador")
        if st.button("Cadastrar Usuario"):
            if add_user(novo_user, nova_senha, admin_flag):
                st.success("Usuario cadastrado com sucesso!")
            else:
                st.error("Erro ao cadastrar usuario ou usuario ja existe.")
    elif admin_option == "Gerenciar UBSs":
        from ubs import manage_ubs
        manage_ubs()
    elif admin_option == "Gerenciar Setores":
        from setores import manage_setores
        manage_setores()
    elif admin_option == "Lista de Usuarios":
        usuarios = list_users()
        if usuarios:
            st.table(usuarios)
        else:
            st.write("Nenhum usuario cadastrado.")

def relatorios():
    st.subheader("Relatorios")
    chamados = list_chamados()
    inventario_data = get_machines_from_inventory()
    if chamados:
        st.markdown("### Chamados Tecnicos")
        st.dataframe(pd.DataFrame(chamados))
    else:
        st.write("Nenhum chamado tecnico encontrado.")
    
    if inventario_data:
        st.markdown("### Inventario")
        st.dataframe(pd.DataFrame(inventario_data))
    else:
        st.write("Nenhum item de inventario encontrado.")
    # Adicione graficos e estatisticas conforme desejado

# Roteamento do menu
if selected == "Login":
    login()
elif selected == "Home":
    home()
elif selected == "Abrir Chamado":
    abrir_chamado()
elif selected == "Chamados Tecnicos":
    chamados_tecnicos()
elif selected == "Inventario":
    inventario()
elif selected == "Estoque":
    estoque()
elif selected == "Administracao":
    administracao()
elif selected == "Relatorios":
    relatorios()
elif selected == "Sair":
    logout()
