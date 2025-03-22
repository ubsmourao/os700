import streamlit as st
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from streamlit_option_menu import option_menu

# Importação dos módulos e funções
from autenticacao import authenticate, add_user, is_admin, list_users
from chamados import (
    add_chamado,
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

# Definição do menu conforme status de login e privilégios (sem opção separada para Finalizar Chamado)
if st.session_state.logged_in:
    if is_admin(st.session_state.username):
        menu_options = [
            "Home",
            "Abrir Chamado",
            "Chamados Técnicos",
            "Inventário",
            "Estoque",
            "Administração",
            "Relatórios",
            "Sair"
        ]
    else:
        menu_options = [
            "Home",
            "Abrir Chamado",
            "Chamados Técnicos",
            "Inventário",
            "Estoque",
            "Relatórios",
            "Sair"
        ]
else:
    menu_options = ["Login"]

selected = option_menu("Menu", menu_options, orientation="horizontal")

# --- Funções das páginas ---

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

def home_page():
    st.subheader("Bem-vindo!")
    st.write("Selecione uma opção no menu para começar.")

def abrir_chamado_page():
    st.subheader("Abrir Chamado Técnico")
    patrimonio = st.text_input("Número de Patrimônio (opcional)")
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
            st.error("Patrimônio não encontrado no inventário. Cadastre a máquina no inventário antes de abrir o chamado.")
            st.stop()
    else:
        ubs_selecionada = st.selectbox("UBS", get_ubs_list())
        setor = st.selectbox("Setor", get_setores_list())
        machine_type = st.selectbox("Tipo de Máquina", ["Computador", "Impressora", "Outro"])

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
    st.dataframe(df)
    
    # Finalização de chamado integrada na mesma página
    df_aberto = df[df["hora_fechamento"].isnull()]
    if df_aberto.empty:
        st.write("Não há chamados abertos para finalizar.")
    else:
        st.markdown("### Finalizar Chamado Técnico")
        chamado_id = st.selectbox("Selecione o ID do chamado para finalizar", df_aberto["id"].tolist())
        chamado = df_aberto[df_aberto["id"] == chamado_id].iloc[0]
        st.write(f"Problema: {chamado['problema']}")
        # Opções de solução diferenciadas conforme o tipo de defeito
        if "impressora" in chamado.get("tipo_defeito", "").lower():
            solucao_options = [
                "Limpeza e recalibração da impressora",
                "Substituição de cartucho/toner",
                "Verificação de conexão e drivers",
                "Reinicialização da impressora"
            ]
        else:
            solucao_options = [
                "Reinicialização do sistema",
                "Atualização de drivers/software",
                "Substituição de componente (ex.: HD, memória)",
                "Verificação de vírus/malware"
            ]
        solucao_selecionada = st.selectbox("Selecione a solução", solucao_options)
        solucao_complementar = st.text_area("Detalhes adicionais da solução (opcional)")
        solucao_final = solucao_selecionada + ((" - " + solucao_complementar) if solucao_complementar else "")
        
        # Seleção de peças utilizadas: multiselect com peças do estoque
        estoque_data = get_estoque()
        pieces_list = [item["nome"] for item in estoque_data] if estoque_data else []
        pecas_selecionadas = st.multiselect("Selecione as peças utilizadas (se houver)", pieces_list)
        
        if st.button("Finalizar Chamado"):
            if solucao_final:
                finalizar_chamado(chamado_id, solucao_final, pecas_usadas=pecas_selecionadas)
            else:
                st.error("Informe a solução para finalizar o chamado.")

def inventario_page():
    st.subheader("Inventário")
    opcao = st.radio("Selecione uma opção:", ["Listar Inventário", "Cadastrar Máquina"])
    if opcao == "Listar Inventário":
        show_inventory_list()
    else:
        cadastro_maquina()

def estoque_page():
    manage_estoque()

def administracao_page():
    st.subheader("Administração")
    admin_option = st.selectbox("Opções de Administração", [
        "Cadastro de Usuário",
        "Gerenciar UBSs",
        "Gerenciar Setores",
        "Lista de Usuários"
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
    st.subheader("Relatórios Completos")
    st.markdown("### Seleção de Período")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data Início")
    with col2:
        end_date = st.date_input("Data Fim")
    if start_date > end_date:
        st.error("Data Início não pode ser maior que Data Fim")
        return
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Filtra chamados pelo período (baseado em hora_abertura)
    chamados = list_chamados()
    if chamados:
        df_chamados = pd.DataFrame(chamados)
        df_chamados["hora_abertura_dt"] = pd.to_datetime(df_chamados["hora_abertura"], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        chamados_period = df_chamados[(df_chamados["hora_abertura_dt"] >= start_datetime) & (df_chamados["hora_abertura_dt"] <= end_datetime)]
        st.markdown("### Chamados Técnicos no Período")
        st.dataframe(chamados_period)
        
        working_times = []
        for idx, row in chamados_period.iterrows():
            if pd.notnull(row.get("hora_fechamento")):
                try:
                    abertura = datetime.strptime(row["hora_abertura"], '%d/%m/%Y %H:%M:%S')
                    fechamento = datetime.strptime(row["hora_fechamento"], '%d/%m/%Y %H:%M:%S')
                    tempo_util = calculate_working_hours(abertura, fechamento)
                    working_times.append(tempo_util.total_seconds())
                except Exception as e:
                    print(f"Erro ao calcular tempo para chamado {row.get('id')}: {e}")
        if working_times:
            media_segundos = sum(working_times) / len(working_times)
            horas = int(media_segundos // 3600)
            minutos = int((media_segundos % 3600) // 60)
            st.markdown(f"**Tempo médio de atendimento (horas úteis):** {horas}h {minutos}m")
            
            fig, ax = plt.subplots()
            ax.hist(working_times, bins=10, color='skyblue', edgecolor='black')
            ax.set_title("Distribuição dos Tempos de Atendimento (horas úteis, em segundos)")
            ax.set_xlabel("Tempo (segundos)")
            ax.set_ylabel("Frequência")
            st.pyplot(fig)
    else:
        st.write("Nenhum chamado técnico encontrado.")
    
    inventario_data = get_machines_from_inventory()
    if inventario_data:
        st.markdown("### Inventário")
        st.dataframe(pd.DataFrame(inventario_data))
    else:
        st.write("Nenhum item de inventário encontrado.")

def sair_page():
    logout()

# Mapeamento das páginas
pages = {
    "Login": login_page,
    "Home": home_page,
    "Abrir Chamado": abrir_chamado_page,
    "Chamados Técnicos": chamados_tecnicos_page,
    "Inventário": inventario_page,
    "Estoque": estoque_page,
    "Administração": administracao_page,
    "Relatórios": relatorios_page,
    "Sair": sair_page,
}

# Roteamento do menu
if selected in pages:
    pages[selected]()
else:
    st.write("Página não encontrada.")
