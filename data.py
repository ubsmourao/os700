# data.py
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

def painel_chamados_tecnicos():
    st.subheader('Painel de Chamados Técnicos')
    # Exemplo de dados; em produção, substitua por list_chamados()
    chamados = [
        [1, 'Usuario1', 'UBS A', 'Setor 1', 'Problema X', 'Em andamento'],
        [2, 'Usuario2', 'UBS B', 'Setor 2', 'Problema Y', 'Finalizado']
    ]
    df = pd.DataFrame(chamados, columns=['ID', 'Usuário', 'UBS', 'Setor', 'Problema', 'Status'])
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    AgGrid(df, gridOptions=gb.build(), enable_enterprise_modules=True)
