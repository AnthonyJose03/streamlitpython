import streamlit as st
import pandas as pd
import sqlalchemy

# configuração do site
st.set_page_config(page_title="Dados", layout='wide')

# Detalhes de conexão
usuario = 'postgres'
senha = 'postgres'
host = 'localhost'
porta = '5432'
nome_do_banco = 'pedido'

# Criação da conexão com o banco de dados
engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{nome_do_banco}', connect_args={"client_encoding": "utf8"})

# Carregando múltiplas tabelas com consultas específicas
query1 = """
SELECT
    cln.nome AS nome_cliente,
    tsp.nome AS nome_transportadora,
    vdd.nome AS nome_vendedor,
    pdd.valor
FROM
    pedido AS pdd
LEFT OUTER JOIN
    cliente cln ON pdd.idcliente = cln.idcliente
LEFT OUTER JOIN
    transportadora tsp ON pdd.idtransportadora = tsp.idtransportadora
LEFT OUTER JOIN
    vendedor vdd ON pdd.idvendedor = vdd.idvendedor
"""

query2 = """
select 
	cln.nome as cliente, 
	mcp.nome as municipio, 
	ncn.nome as nacionalidade 
from 
	cliente cln
left outer join
	municipio mcp on cln.idmunicipio = mcp.idmunicipio
left outer join
	nacionalidade ncn on cln.idnacionalidade = ncn.idnacionalidade
"""

query3 = """
select 
	pdt.nome as produto,
	fnc.nome as fornecedor,
	valor
from 
	produto pdt
left outer join
	fornecedor fnc on pdt.idfornecedor = fnc.idfornecedor
"""

df1 = pd.read_sql_query(query1, con=engine)
df2 = pd.read_sql_query(query2, con=engine)
df3 = pd.read_sql_query(query3, con=engine)

col1, col2, col3 = st.columns(3)

with col1:
    st.table(df1)
with col2:
    st.table(df2)
with col3:
    st.table(df3)
