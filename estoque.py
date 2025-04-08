import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_client import supabase

def get_estoque():
    """
    Retorna a lista de peças no estoque.
    Cada registro possui: id, nome, quantidade, descricao, nota_fiscal e data_adicao.
    """
    try:
        resp = supabase.table("estoque").select("*").execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"Erro ao recuperar estoque: {e}")
        return []

def add_peca(nome, quantidade, descricao="", nota_fiscal=None, data_adicao=None):
    """
    Adiciona uma peça ao estoque.
    - data_adicao: se não fornecida, usa a data/hora atual.
    - nota_fiscal: opcional.
    """
    try:
        if data_adicao is None:
            data_adicao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        data = {
            "nome": nome,
            "quantidade": quantidade,
            "descricao": descricao,
            "nota_fiscal": nota_fiscal,
            "data_adicao": data_adicao
        }
        supabase.table("estoque").insert(data).execute()
        st.success("Peça adicionada ao estoque com sucesso!")
    except Exception as e:
        st.error(f"Erro ao adicionar peça: {e}")

def update_peca(id_peca, new_values):
    """
    Atualiza os dados da peça identificada pelo id.
    """
    try:
        supabase.table("estoque").update(new_values).eq("id", id_peca).execute()
        st.success("Peça atualizada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao atualizar peça: {e}")

def delete_peca(id_peca):
    """
    Remove uma peça do estoque.
    """
    try:
        supabase.table("estoque").delete().eq("id", id_peca).execute()
        st.success("Peça excluída com sucesso!")
    except Exception as e:
        st.error(f"Erro ao excluir peça: {e}")

def dar_baixa_estoque(peca_nome, quantidade_usada=1):
    """
    Dá baixa no estoque: reduz a quantidade da peça 'peca_nome' pelo valor 'quantidade_usada'.
    Se a quantidade resultar negativa, ela é ajustada para zero.
    """
    try:
        resp = supabase.table("estoque").select("*").eq("nome", peca_nome).execute()
        if not resp.data:
            st.warning(f"Peça '{peca_nome}' não encontrada no estoque.")
            return
        item = resp.data[0]
        nova_quantidade = item.get("quantidade", 0) - quantidade_usada
        if nova_quantidade < 0:
            nova_quantidade = 0
        supabase.table("estoque").update({"quantidade": nova_quantidade}).eq("id", item["id"]).execute()
        st.success(f"Baixa efetuada: {peca_nome} agora possui {nova_quantidade} unidades.")
    except Exception as e:
        st.error(f"Erro ao dar baixa no estoque: {e}")

def manage_estoque():
    st.subheader("Gerenciar Estoque de Peças de Informática")
    action = st.selectbox("Ação", ["Listar", "Adicionar", "Editar", "Remover"])
    
    if action == "Listar":
        estoque_data = get_estoque()
        if estoque_data:
            for item in estoque_data:
                if item.get("data_adicao"):
                    try:
                        item["data_adicao"] = datetime.fromisoformat(item["data_adicao"]).strftime('%d/%m/%Y %H:%M:%S')
                    except:
                        pass
            st.dataframe(pd.DataFrame(estoque_data))
        else:
            st.write("Estoque vazio.")

    elif action == "Adicionar":
        nome = st.text_input("Nome da Peça")
        quantidade = st.number_input("Quantidade", min_value=0, step=1)
        descricao = st.text_area("Descrição (opcional)")
        nota_fiscal = st.text_input("Número da Nota Fiscal (opcional)")
        if st.button("Adicionar Peça"):
            if nome:
                add_peca(nome, quantidade, descricao, nota_fiscal)
            else:
                st.error("Insira o nome da peça.")

    elif action == "Editar":
        estoque_data = get_estoque()
        if estoque_data:
            df = pd.DataFrame(estoque_data)
            st.dataframe(df)
            id_peca = st.selectbox("Selecione o ID da peça para editar", df["id"].tolist())
            if id_peca:
                nome = st.text_input("Nome da Peça")
                quantidade = st.number_input("Quantidade", min_value=0, step=1)
                descricao = st.text_area("Descrição (opcional)")
                nota_fiscal = st.text_input("Número da Nota Fiscal (opcional)")
                if st.button("Atualizar Peça"):
                    new_values = {
                        "nome": nome,
                        "quantidade": quantidade,
                        "descricao": descricao,
                        "nota_fiscal": nota_fiscal
                    }
                    update_peca(id_peca, new_values)
        else:
            st.write("Estoque vazio para edição.")

    elif action == "Remover":
        estoque_data = get_estoque()
        if estoque_data:
            df = pd.DataFrame(estoque_data)
            st.dataframe(df)
            id_peca = st.selectbox("Selecione o ID da peça para remover", df["id"].tolist())
            if st.button("Remover Peça"):
                delete_peca(id_peca)
        else:
            st.write("Estoque vazio para remoção.")
