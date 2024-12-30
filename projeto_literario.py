import streamlit as st
import pandas as pd
import sqlalchemy
import time
import plotly.express as px

# configuração do site
st.set_page_config(page_title="Dashboard", layout='wide')

with open("styles.css") as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

# Detalhes de conexão
usuario = 'postgres'
senha = 'rzEe42WpuRgpwA3O'
host = 'monstrously-dexterous-arachnid.data-1.use1.tembo.io'
porta = '5432'
nome_do_banco = 'youx'

# Criação da conexão com o banco de dados
engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{nome_do_banco}', connect_args={"client_encoding": "utf8"})

# query de status
status_aluno = """
select
	emp.status,
	count(emp.status) as quantidade
from
	emprestimo emp
left outer join
	aluno aln on emp.id_aluno = aln.id
group by
	emp.status
"""

qtd_emp_aluno_por_mes = """
select
    aln.nome,
   	l.titulo as livro,
    count(e.id) as quantidade_emprestimos,
    extract(year from e.data_emprestimo) as ano,
    extract(month from e.data_emprestimo) as mes
from
    emprestimo e
left outer join
    aluno aln on e.id_aluno = aln.id
left outer join
	livro l on e.id_livro = l.id
group by
    aln.nome, ano, mes, l.titulo
order by
    ano, mes, quantidade_emprestimos desc;
"""

emp_aluno2 = """
select
    aln.nome,
    count(e.id) as quantidade_emprestimos,
    extract(year from e.data_emprestimo) as ano,
    extract(month from e.data_emprestimo) as mes
from
    emprestimo e
left outer join
    aluno aln on e.id_aluno = aln.id
left outer join
	livro l on e.id_livro = l.id
group by
    aln.nome, ano, mes
order by
    ano, mes, quantidade_emprestimos desc;
"""

datas_emp = """
select 
	data_emprestimo, 
	data_prevista_entrega , 
	data_entrega 
from 
	emprestimo e 
"""

livros_m_emprestados = """
select
	l.titulo as titulo,
	count(e.id_livro) as quantidade
from
	emprestimo e
left outer join
	livro l on e.id_livro = l.id
group by
	l.titulo, e.id_livro
"""

qtd_emprestimo_mes = """
SELECT 
    EXTRACT(YEAR FROM data_emprestimo) AS ano,
    EXTRACT(MONTH FROM data_emprestimo) AS mes,
    COUNT(id) AS quantidade_emprestimos
FROM 
    emprestimo
GROUP BY 
    ano, mes
ORDER BY 
    ano DESC, mes DESC;
"""

genero_m_emprestados = """
select
	g.nome as genero,
	count(g.nome) as quantidade
from
	rel_livro_genero rlg
left outer join
	genero g on rlg.id_livro = g.id
group by
	g.nome
"""

qtd_livros = """
select sum(quantidade_livros) as quantidade from livro l 
"""

qtd_livro_emprestado = """
select sum(quantidade_emprestado) as quantidade from livro l 
"""

livros_mais_emprestados_query = """
select
    l.titulo,
    count(e.id) as quantidade_emprestimos,
    extract(year from e.data_emprestimo) as ano,
    extract(month from e.data_emprestimo) as mes
from
    emprestimo e
left outer join
    livro l on e.id_livro = l.id
group by
    l.titulo, ano, mes
order by
    ano, mes, quantidade_emprestimos desc
"""

# transformação de query
status = pd.read_sql_query(status_aluno, con=engine)
emp_aluno = pd.read_sql_query(qtd_emp_aluno_por_mes, con=engine)
datas_emp = pd.read_sql_query(datas_emp, con=engine)
genero_m_emprestados = pd.read_sql_query(genero_m_emprestados, con=engine)
qtd_livros = pd.read_sql_query(qtd_livros, con=engine)
qtd_livro_emprestado = pd.read_sql_query(qtd_livro_emprestado, con=engine)
livros_m_emprestados = pd.read_sql_query(livros_m_emprestados, con=engine)
emp_aluno2 = pd.read_sql_query(emp_aluno2, con=engine)
livros_mais_emprestados = pd.read_sql_query(livros_mais_emprestados_query, con=engine)
qtd_emprestimo_mes = pd.read_sql_query(qtd_emprestimo_mes, con=engine)


qtd_emprestimo_mes['ano'] = qtd_emprestimo_mes['ano'].astype(int)
qtd_emprestimo_mes['mes'] = qtd_emprestimo_mes['mes'].astype(int)
emp_aluno['ano'] = emp_aluno['ano'].astype(int)
qtd_emprestimo_mes['data'] = pd.to_datetime(qtd_emprestimo_mes['ano'].astype(str) + '-' + qtd_emprestimo_mes['mes'].astype(str) + '-01', format='%Y-%m-%d')


df = qtd_emprestimo_mes.sort_values(by='data', ascending=True)
# Mapeamento de meses
meses = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# Mapeando o número do mês para o nome do mês
emp_aluno['mes'] = emp_aluno['mes'].map(meses)
emp_aluno2['mes'] = emp_aluno2['mes'].map(meses)
livros_mais_emprestados['mes'] = livros_mais_emprestados['mes'].map(meses)
qtd_emprestimo_mes['mes'] = qtd_emprestimo_mes['mes'].map(meses)
df['mes'] = df['mes'].map(meses)

# Agrupar por mês e livro, contar os empréstimos
col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
with col4:
    ano_selecionado = st.selectbox('Selecione o ano', emp_aluno['ano'].unique())
with col5:
    mes_selecionado = st.selectbox('Selecione o mês', emp_aluno['mes'].unique())
   





dicionario = {
    'Finalizado': 'Em dia',
    'Em andamento': 'Em atraso'
}

status = status.replace(dicionario)


st.write("# Conexão Literária")
st.write("## Status dos livros emprestados")


# renomeando as colunas
status = status.rename(columns={
    'status': 'Status',
    'quantidade': 'Quantidade'
})
emp_aluno = emp_aluno.rename(columns={
    'nome': 'Nome'
})
genero_m_emprestados = genero_m_emprestados.rename(columns={
    'genero': 'Gênero',
    'quantidade': 'Quantidade'
})
livros_m_emprestados = livros_m_emprestados.rename(columns={
    'titulo': 'Título',
    'quantidade': 'Quantidade'
})
qtd_emprestimo_mes = qtd_emprestimo_mes.rename(columns={
    'mes': 'Mês',
    'quantidade_emprestimos': 'Quantidade',
    'ano': 'Ano'
})
df = df.rename(columns={
    'mes': 'Mês',
    'quantidade_emprestimos': 'Quantidade',
    'ano': 'Ano',
    'data': 'Data'
})
# livros_m_emprestados = livros_m_emprestados.sort_values(by='Quantidade', ascending=False)
# print(livros_m_emprestados)

fig = px.pie(status, names='Status',
             values='Quantidade',
             title='Status do Emprestimo',
             color='Status',
             color_discrete_map={'Em dia':'#65558F',
                                 'Em atraso':'#483D8B'})
fig.update_traces(textfont_size=20)
# tamanho da legenda
fig.update_layout(
    legend=dict(
        font=dict(
            size=15  # Tamanho da fonte da legenda (em pixels)
        )
    )
)

# Calcular o total de cada status
em_dia = status[status['Status'] == 'Em dia']['Quantidade'].sum()
pendente = status[status['Status'] == 'Pendente']['Quantidade'].sum()
em_atraso = status[status['Status'] == 'Em atraso']['Quantidade'].sum()
em_dia_real = em_dia+pendente

# Calcular o acervo de livros disponiveis e emprestados
qtd_livros = qtd_livros.reset_index()
qtd_livro_emprestado = qtd_livro_emprestado.reset_index()
qtd_livros = qtd_livros['quantidade']
qtd_livro_emprestado = qtd_livro_emprestado['quantidade']
disponiveis = qtd_livros-qtd_livro_emprestado

# colunas do grafico de pizza
col1, col2, col3 = st.columns([6, 2, 2])
with col1:
    with st.container(border=True):
        st.plotly_chart(fig)
with col2:
    container = st.container(border=True)
    container.metric(label="**Total em dia**", value=em_dia_real)
    container.metric(label="**Total em atraso**", value=em_atraso)
with col3:
    container2 = st.container(border=True)
    container2.metric(label="**Total de livros**", value=qtd_livros)
    container2.metric(label="**Livros disponiveis**", value=disponiveis)
    container2.metric(label="**Livros emprestados**", value=qtd_livro_emprestado)
 


# Gráfico de barra (emprestimo por mes)
fig1 = px.bar(df,
              x='Mês', 
              y='Quantidade', 
              title='Meses com mais emprestimo',
              color_discrete_sequence=["#65558F"],
              text='Quantidade')
fig1.update_layout(
    title=dict(
        font=dict(
            size=24,
            color="black"      # Tamanho da fonte do título
        )
    ),
    xaxis=dict(
        title=dict(
            font=dict(
                size=18,
                color="black"  # Tamanho da fonte do eixo X
            )
        ),
        tickfont=dict(
            size=16,
            color="black"      # Tamanho da fonte dos rótulos do eixo X
        )
    ),
    yaxis=dict(
        title=dict(
            font=dict(
                size=18,
                color="black"  # Tamanho da fonte do título do eixo Y
            )
        ),
        tickfont=dict(
            size=16,
            color="black"      # Tamanho da fonte dos rótulos do eixo Y
        )
    )
)    
fig1.update_traces(textposition='outside',
                    textfont=dict(size=18,
                                  color='black'))

st.divider()
st.plotly_chart(fig1)

# Cores do gráfico
custom_colors = ['#BEA6FF', '#AF54E4', '#A18AC2', '#8E74D2',
                 '#751AAA', '#DCCEFF', '#A887FF', '#4E358E',
                 '#7B7097', '#824BA7']
# Gráfico de barra (gêneros mais emprestados)
fig2 = px.bar(genero_m_emprestados, x='Gênero',
              y='Quantidade',
              title='Ranking de gêneros mais emprestados',
              color_discrete_sequence=custom_colors,
              color='Gênero',
              text='Quantidade')
fig2.update_layout(
    title=dict(
        font=dict(
            size=24             # Tamanho da fonte do título
        )
    ),
    xaxis=dict(
        title=dict(
            font=dict(
                size=18,
                color="black"   # Tamanho da fonte do título do eixo X
            )
        ),
        tickfont=dict(
            size=16,
            color="black"
                                # Tamanho da fonte dos rótulos do eixo X
        )
    ),
    yaxis=dict(
        title=dict(
            font=dict(
                size=18,
                color="black"   # Tamanho da fonte do título do eixo Y
            )
        ),
        tickfont=dict(
            size=16,
            color="black"       # Tamanho da fonte dos rótulos do eixo Y
        )
    ),
    legend=dict(
        font=dict(
            size=14,
            color="black"       # Tamanho da fonte da legenda
        )
    )
)
fig2.update_traces(textposition='outside',
                    textfont=dict(size=18,
                                  color='black'))
st.divider()
# Gráfico de pizza
st.plotly_chart(fig2)    
st.divider()

# Estilização das tabelas
st.markdown(
    """
    <style>
    .center-table {
        display: flex;
        justify-content: left;
        align-items: left;
    }
    table {
        font-size: 20px;
        width: 75%; /* Ajuste o tamanho da tabela aqui */
        border-radius: 10px;
        border-collapse: collapse;
        border: 6px #080808;
        overflow: hidden;
    }
    th, td {
        text-align: left;
        border: 4px solid #ddd;
        padding: 8px;
    }
    th {
        color: white;
        background-color: #65558F;
        font-weight: bold;
    }
    /* Linhas com fundo branco e cinza alternado */
    tr:nth-child(odd) {
        background-color: #f2f2f2; /* Cinza claro */
    }
    tr:nth-child(even) {
        background-color: white; /* Branco */
    }
    </style>
    """,
    unsafe_allow_html=True
    )


bar1, bar2 = st.columns(2)
with bar1: 
    livros_mais_emprestados_filtrado =  livros_mais_emprestados[(livros_mais_emprestados['ano'] == ano_selecionado) & (livros_mais_emprestados['mes'] == mes_selecionado)]
    # Ranking dos livros mais emprestados
    livros_mais_emprestados_filtrado = livros_mais_emprestados_filtrado.rename(columns={
        'titulo': 'Título',
        'quantidade_emprestimos': 'n° emprestimos'
    })
    livros_mais_emprestados_filtrado = livros_mais_emprestados_filtrado[['Título', 'n° emprestimos']].nlargest(10, 'n° emprestimos')
    livros_mais_emprestados_filtrado = livros_mais_emprestados_filtrado.to_html(index=False)
    st.write("## Livros que mais foram emprestados")
    st.write("Mês:", mes_selecionado)
    st.markdown(f'<div class="center-table">{livros_mais_emprestados_filtrado}</div>', unsafe_allow_html=True)

with bar2:
    # Ranking dos alunos que mais pegaram livros
    emp_aluno_filtrado = emp_aluno2[(emp_aluno2['ano'] == ano_selecionado) & (emp_aluno2['mes'] == mes_selecionado)]
    emp_aluno_filtrado = emp_aluno_filtrado.rename(columns={
        'nome': 'Nome',
        'quantidade_emprestimos': 'n° emprestimos'
    })
    emp_aluno_filtrado = emp_aluno_filtrado[['Nome', 'n° emprestimos']].nlargest(10, 'n° emprestimos')
    emp_aluno_filtrado = emp_aluno_filtrado.to_html(index=False, escape=False)
    st.write("## Alunos com mais livros emprestados")
    st.write("Mês:", mes_selecionado)
    st.markdown(f'<div class="center-table">{emp_aluno_filtrado}</div>', unsafe_allow_html=True)
    
# Livro mais emprestado nos meses
# - agrupando por ano, mês e livro
emp_por_mes = emp_aluno.groupby(['ano', 'mes', 'livro']).size().reset_index(name='total_emprestimo')
# - ordenando pelo total de emprestimos 
emp_por_mes = emp_por_mes.sort_values(by='total_emprestimo', ascending=False)
print(emp_por_mes)
# - puxando o o primeiro index dos emprestimos ordenados
livro_mais_emprestado = emp_por_mes.loc[emp_por_mes['mes'] == mes_selecionado].iloc[0]

st.header("Livro mais emprestado do mês:")
st.subheader(f'Mês: {livro_mais_emprestado["mes"]}')
st.markdown(f'**Livro:**')

barr1, barr2, barr3 = st.columns([1, 3, 1])
with barr2:
    print(livro_mais_emprestado)
    st.markdown("""
        <div style="background-color: #f0f0f0; padding: 20px; border-radius: 10px; text-align: center; font-size: 30px;">
            <b>{}</b><br>
            <i>Total de Empréstimos: {}</i>
        </div>
    """.format(livro_mais_emprestado["livro"], livro_mais_emprestado["total_emprestimo"]), unsafe_allow_html=True)
