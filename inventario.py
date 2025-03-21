# inventario.py
import streamlit as st
import pandas as pd
from supabase_client import supabase

def add_machine_to_inventory(tipo, marca, modelo, numero_serie, status, localizacao, propria_locada, patrimonio, setor):
    try:
        # Verifica duplicidade
        resp = supabase.table("inventario").select("numero_patrimonio").eq("numero_patrimonio", patrimonio).execute()
        if resp.data:
            st.error(f"Máquina com patrimônio {patrimonio} já existe.")
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
            "setor": setor
        }
        supabase.table("inventario").insert(data).execute()
        st.success("Máquina adicionada com sucesso!")
    except Exception as e:
        st.error("Erro ao adicionar máquina.")
        print(f"Erro no inventario: {e}")

def get_machines_from_inventory():
    try:
        resp = supabase.table("inventario").select("*").execute()
        return resp.data
    except Exception as e:
        st.error("Erro ao recuperar inventário.")
        print(f"Erro: {e}")
        return []

def list_chamados_por_patrimonio(patrimonio):
    try:
        resp = supabase.table("chamados").select("*").eq("patrimonio", patrimonio).execute()
        return resp.data
    except Exception as e:
        st.error("Erro ao listar chamados.")
        print(f"Erro: {e}")
        return []

def show_inventory_list():
    st.subheader("Lista de Inventário")
    machines = get_machines_from_inventory()
    if machines:
        df = pd.DataFrame(machines)
        st.dataframe(df)
    else:
        st.write("Nenhum item encontrado.")

def add_maintenance_history(patrimonio, descricao):
    if not descricao:
        st.error("Informe a descrição da manutenção.")
        return
    try:
        supabase.table("historico_manutencao").insert({
            "numero_patrimonio": patrimonio,
            "descricao": descricao,
            "data_manutencao": "now()"
        }).execute()
        st.success("Histórico adicionado.")
    except Exception as e:
        st.error("Erro ao adicionar manutenção.")
        print(f"Erro: {e}")

def show_maintenance_history(patrimonio):
    try:
        resp_hist = supabase.table("historico_manutencao").select("descricao, data_manutencao").eq("numero_patrimonio", patrimonio).execute()
        resp_pecas = supabase.table("pecas_usadas").select("peca_nome, data_uso").execute()
        if resp_hist.data:
            st.write("Histórico de Manutenção:")
            st.dataframe(pd.DataFrame(resp_hist.data))
        else:
            st.write("Nenhum histórico encontrado.")
        if resp_pecas.data:
            st.write("Peças Usadas:")
            st.dataframe(pd.DataFrame(resp_pecas.data))
    except Exception as e:
        st.error("Erro ao recuperar histórico.")
        print(f"Erro: {e}")
