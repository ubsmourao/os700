import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# Função de exibição do painel de chamados
def painel_chamados_tecnicos():
    st.subheader('Painel de Chamados Técnicos')

    # Dados de exemplo
    chamados = [
        [1, 'Usuário1', 'UBS A', 'Setor 1', 'Computador não liga', 'Em andamento'],
        [2, 'Usuário2', 'UBS B', 'Setor 2', 'Impressora não imprime', 'Finalizado'],
    ]
    df_chamados = pd.DataFrame(chamados, columns=[
        'ID', 'Usuário', 'UBS', 'Setor', 'Problema', 'Status'
    ])

    # Construir as opções da tabela
    gb = GridOptionsBuilder.from_dataframe(df_chamados)
    gb.configure_pagination(paginationAutoPageSize=True)  # Paginação automática
    gb.configure_side_bar()  # Barra lateral
    gridOptions = gb.build()

    # Exibir tabela com AgGrid
    AgGrid(df_chamados, gridOptions=gridOptions, enable_enterprise_modules=True)

# Chamar a função do painel
painel_chamados_tecnicos()
