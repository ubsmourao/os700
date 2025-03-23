# chat.py
from supabase import create_client, Client
import streamlit as st
from datetime import datetime

# Obtenha suas credenciais do Supabase a partir dos secrets do Streamlit
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Cria o cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_chat_table():
    """
    Em Supabase, a criação de tabelas geralmente é feita pelo dashboard ou via migrations.
    Essa função é um placeholder para documentar que a tabela 'chat_messages' deve existir.
    A tabela deve conter:
      - id: INTEGER, chave primária, autoincrement
      - remetente: TEXT
      - destinatario: TEXT
      - mensagem: TEXT
      - timestamp: TEXT
    """
    pass

def salvar_mensagem(remetente, destinatario, mensagem):
    """
    Salva uma mensagem na tabela 'chat_messages' do Supabase.
    Retorna a resposta da inserção ou None em caso de erro.
    """
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    data = {
        "remetente": remetente,
        "destinatario": destinatario,
        "mensagem": mensagem,
        "timestamp": timestamp
    }
    try:
        response = supabase.table("chat_messages").insert(data).execute()
        return response
    except Exception as e:
        st.error(f"Erro ao salvar mensagem: {e}")
        return None

def ler_mensagens(filtro_usuario=None):
    """
    Retorna o histórico de mensagens da tabela 'chat_messages'.
    Se filtro_usuario for fornecido, retorna as mensagens onde o remetente ou destinatario
    é igual a esse usuário.
    """
    try:
        if filtro_usuario:
            # A função or_ permite filtrar mensagens em que o usuário é remetente ou destinatario.
            query_filter = f"remetente.eq.{filtro_usuario},destinatario.eq.{filtro_usuario}"
            response = supabase.table("chat_messages").select("*").or_(query_filter).order("id", desc=False).execute()
        else:
            response = supabase.table("chat_messages").select("*").order("id", desc=False).execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao ler mensagens: {e}")
        return []

def chat_usuario_page(username):
    """
    Página de chat para o usuário.
    Exibe a conversa (mensagens enviadas e recebidas) e permite enviar novas mensagens.
    """
    st.subheader("Chat com Suporte")
    historico = ler_mensagens(filtro_usuario=username)
    if historico:
        for msg in historico:
            if msg["remetente"] == username:
                st.markdown(f"**Você ({msg['timestamp']}):** {msg['mensagem']}")
            else:
                st.markdown(f"**Suporte ({msg['timestamp']}):** {msg['mensagem']}")
    else:
        st.write("Nenhuma mensagem encontrada.")
    
    user_input = st.text_input("Digite sua mensagem:", key="chat_input_usuario")
    if st.button("Enviar", key="enviar_usuario"):
        if user_input:
            salvar_mensagem(remetente=username, destinatario="admin", mensagem=user_input)
            st.success("Mensagem enviada!")
            # Em vez de forçar rerun, oferecemos um botão de atualizar
    if st.button("Atualizar Conversa", key="atualizar_usuario"):
        st.experimental_rerun()  # Caso seu ambiente permita, isso atualiza a página

def chat_admin_page():
    """
    Página de chat para o administrador.
    Permite filtrar por usuário e enviar respostas.
    """
    st.subheader("Chat - Administrador")
    filtro = st.text_input("Filtrar por usuário (deixe vazio para todas):", key="chat_filtro")
    if filtro:
        historico = ler_mensagens(filtro_usuario=filtro)
    else:
        historico = ler_mensagens()
    
    if historico:
        for msg in historico:
            st.markdown(f"**{msg['remetente']} ({msg['timestamp']}):** {msg['mensagem']}")
    else:
        st.write("Nenhuma mensagem encontrada.")
    
    resposta = st.text_input("Responder:", key="chat_input_admin")
    if st.button("Enviar Resposta", key="enviar_admin"):
        if resposta and filtro:
            salvar_mensagem(remetente="admin", destinatario=filtro, mensagem=resposta)
            st.success("Resposta enviada!")
    if st.button("Atualizar Conversa", key="atualizar_admin"):
        st.experimental_rerun()