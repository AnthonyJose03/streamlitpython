import streamlit as st
import pandas as pd
import sqlalchemy
import time

# configuração do site
st.set_page_config(page_title="Dados", layout='wide')

# Detalhes de conexão
usuario = 'postgres'
senha = 'rzEe42WpuRgpwA3O'
host = 'monstrously-dexterous-arachnid.data-1.use1.tembo.io'
porta = '5432'
nome_do_banco = 'postgres'

# Criação da conexão com o banco de dados
engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{nome_do_banco}', connect_args={"client_encoding": "utf8"})

# Função genérica para carregar dados com query personalizada
@st.cache_data(ttl=20)  # Atualiza os dados a cada 5 segundos automaticamente
def load_custom_query(query):
    df = pd.read_sql(query, engine)
    return df

consulta = """
SELECT * FROM Autores;
"""

consulta2 = """
SELECT * FROM Membros;
"""

consulta3 = """
SELECT * FROM Emprestimos;
"""

# Layout com 3 colunas
st.title("Atualização Dinâmica de Dados")
col1, col2, col3 = st.columns(3)

# Placeholders para atualizar os dados dinamicamente
placeholder1 = col1.empty()
placeholder2 = col2.empty()
placeholder3 = col3.empty()

# Atualização contínua
while True:
    # Carregar os dados das queries
    df1 = load_custom_query(consulta)
    df2 = load_custom_query(consulta2)
    df3 = load_custom_query(consulta3)

    # Atualizar as tabelas nos placeholders
    with placeholder1:
        st.table(df1)
    with placeholder2:
        st.table(df2)
    with placeholder3:
        st.table(df3)
    # Intervalo de atualização
    with st.spinner('Wait for it...'):
        time.sleep(60)  # Atualiza os dados a cada 60 segundos
