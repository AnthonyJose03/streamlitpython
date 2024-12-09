import streamlit as st
import pandas as pd
import sqlalchemy

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


consulta = """
SELECT * FROM Autores;
"""

consulta2 = """
SELECT * FROM Membros;
"""

df1 = pd.read_sql_query(consulta, con=engine)
df2 = pd.read_sql_query(consulta2, con=engine)

st.header("Criando Streamlit")

st.table(df1)
st.table(df2)