import streamlit as st
import pandas as pd
import sqlalchemy
import time
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import base64
from wordcloud import WordCloud
from openpyxl import load_workbook
from openpyxl.styles import NamedStyle
from io import BytesIO

# configuração do site
st.set_page_config(page_title="Dashboard", layout='wide')

with open("styles.css") as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

# Configuração da conexão com o banco
DB_CONFIG = {
    "usuario": "postgres",
    "senha": "rzEe42WpuRgpwA3O",
    "host": "monstrously-dexterous-arachnid.data-1.use1.tembo.io",
    "porta": "5432",
    "nome_do_banco": "app"
}
engine = sqlalchemy.create_engine(
    f"postgresql+psycopg2://{DB_CONFIG['usuario']}:{DB_CONFIG['senha']}@{DB_CONFIG['host']}:{DB_CONFIG['porta']}/{DB_CONFIG['nome_do_banco']}",
    connect_args={"client_encoding": "utf8"}
)


query_params = st.query_params

id_escola = query_params.get("id_escola", [None])[0]  # Pega o primeiro valor da lista, se houver
id_escola = int(id_escola)

# query de status
status = """
select
	emp.status as "Status",
	count(emp.status) as "Quantidade"
from
	emprestimo emp
left outer join
	aluno aln on emp.id_aluno = aln.id
where
    aln.id_escola = %s
group by
	emp.status
"""

emprestimo_aluno = """
select
    aln.nome as "Nome",
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
where
    aln.id_escola = %s
group by
    aln.nome, ano, mes, l.titulo
order by
    ano, mes, quantidade_emprestimos desc;
"""

ranking_alunos = """
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
where
    aln.id_escola = %s
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
where
    id_escola = %s
"""

livros_m_emprestados = """
select
	l.titulo as "Título",
	count(e.id_livro) as "Quantidade"
from
	emprestimo e
left outer join
	livro l on e.id_livro = l.id
where
    e.id_escola = %s
group by
	l.titulo, e.id_livro
"""

qtd_emprestimo_mes = """
SELECT 
    EXTRACT(YEAR FROM data_emprestimo) AS "Ano",
    EXTRACT(MONTH FROM data_emprestimo) AS "Mês",
    COUNT(id) AS "Quantidade"
FROM 
    emprestimo
where
    id_escola = %s
GROUP BY 
    "Ano", "Mês"
ORDER BY 
    "Ano" DESC, "Mês" DESC;
"""

genero_m_emprestados = """
SELECT
    EXTRACT(YEAR FROM e.data_emprestimo) AS ano,
    EXTRACT(MONTH FROM e.data_emprestimo) AS mes,
    g.nome AS "Gênero",
    COUNT(g.id) AS "Quantidade"
FROM
    rel_livro_genero rlg
LEFT OUTER JOIN
    genero g ON rlg.id_genero = g.id
LEFT OUTER JOIN
    emprestimo e ON rlg.id_livro = e.id_livro
where
    e.id_escola = %s
GROUP BY
    ano, mes, g.nome
ORDER BY
    ano DESC, mes DESC, "Gênero";
"""

qtd_livros = """
select 
    sum(quantidade_livros) as quantidade 
from 
    livro l
where
    id_escola = %s
"""

qtd_livro_emprestado = """
select 
    sum(quantidade_emprestado) as quantidade 
from 
    livro l
where
    id_escola = %s
"""

livros_mais_emprestados_query = """
select
    l.titulo,
    count(e.id) as quantidade_emprestimos,
    extract(year from e.data_emprestimo) as ano,
    extract(month from e.data_emprestimo) as mes
from
    livro l
left join
    emprestimo e on l.id = e.id_livro
where
    l.id_escola = %s
group by
    l.titulo, ano, mes
order by
    ano, mes, quantidade_emprestimos desc
"""

livros_disponiveis = """
SELECT 
    l.titulo,
    l.isbn,
    l.quantidade_livros - l.quantidade_emprestado AS quantidade_disponivel
FROM 
    livro l
WHERE 
    l.quantidade_livros > l.quantidade_emprestado
    and
    l.id_escola = %s;
"""

livros_geral = """
SELECT 
    SUM(l.quantidade_emprestado) AS total_livros_emprestados,
    sum(l.quantidade_livros - l.quantidade_emprestado) as livros_disponiveis,
    sum(l.quantidade_livros) as total_geral
FROM 
    livro l
where
    l.id_escola = %s;
"""

quantidade_ano = """
SELECT 
    EXTRACT(YEAR FROM data_emprestimo) AS ano,
    COUNT(id) AS quantidade_emprestimos
FROM 
    emprestimo e
where
    id_escola = %s
GROUP BY 
    ano
ORDER BY 
    ano DESC;
"""

status_alunos = """
select 
	a.nome,
	l.titulo,
    a.telefone,
    e.data_emprestimo,
    e.data_prevista_entrega as data_prevista,
	e.status 
from 
	emprestimo e
left outer join
	aluno a on e.id = a.id 
left outer join
	livro l on e.id_livro = l.id 
where 
    e.id_escola = %s
order by
    e.status;
"""

acervo_geral = """
select
	titulo,
	isbn,
	data_publicacao,
	autor,
	quantidade_livros,
	quantidade_emprestado,
	localizacao_pratileira
from
	livro
"""

genero_total = """
SELECT
    EXTRACT(YEAR FROM e.data_emprestimo) AS ano,
    g.nome AS "Gênero",
    COUNT(g.id) AS "Quantidade"
FROM
    rel_livro_genero rlg
LEFT OUTER JOIN
    genero g ON rlg.id_genero = g.id
LEFT OUTER JOIN
    emprestimo e ON rlg.id_livro = e.id_livro
WHERE
    e.id_escola = %s
GROUP BY
    ano, g.nome
ORDER BY
    ano DESC, "Quantidade" DESC, "Gênero";
"""

livros_total = """
select
    l.titulo,
    count(e.id) as quantidade_emprestimos,
    extract(year from e.data_emprestimo) as ano,
    extract(month from e.data_emprestimo) as mes
from
    livro l
left join
    emprestimo e on l.id = e.id_livro
where
    l.id_escola = 1
group by
    l.titulo, ano, mes
order by
    ano, quantidade_emprestimos desc
"""

total_alunos = """
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
where
    aln.id_escola = %s
group by
    aln.nome, ano, mes
order by
    ano, quantidade_emprestimos desc;
"""


@st.cache_data
def execute_query(query, id_escola):
    return pd.read_sql_query(query, con=engine, params=(id_escola,))

# Transformação de query com o id_escola sendo passado
status = execute_query(status, id_escola)
emprestimo_aluno = execute_query(emprestimo_aluno, id_escola)
datas_emp = execute_query(datas_emp, id_escola)
genero_m_emprestados = execute_query(genero_m_emprestados, id_escola)
qtd_livros = execute_query(qtd_livros, id_escola)
qtd_livro_emprestado = execute_query(qtd_livro_emprestado, id_escola)
livros_m_emprestados = execute_query(livros_m_emprestados, id_escola)
ranking_alunos = execute_query(ranking_alunos, id_escola)
livros_mais_emprestados = execute_query(livros_mais_emprestados_query, id_escola)
qtd_emprestimo_mes = execute_query(qtd_emprestimo_mes, id_escola)
livros_disponiveis = execute_query(livros_disponiveis, id_escola)
livros_geral = execute_query(livros_geral, id_escola)
quantidade_ano = execute_query(quantidade_ano, id_escola)
status_alunos = execute_query(status_alunos, id_escola)
acervo_geral = execute_query(acervo_geral, id_escola)
genero_total = execute_query(genero_total, id_escola)
livros_total = execute_query(livros_total, id_escola)
total_alunos = execute_query(total_alunos, id_escola)


# rotulação dos meses
qtd_emprestimo_mes['Ano'] = qtd_emprestimo_mes['Ano'].astype(int)
qtd_emprestimo_mes['Mês'] = qtd_emprestimo_mes['Mês'].astype(int)
emprestimo_aluno['ano'] = emprestimo_aluno['ano'].astype(int)
qtd_emprestimo_mes['Data'] = pd.to_datetime(qtd_emprestimo_mes['Ano'].astype(str) + '-' + qtd_emprestimo_mes['Mês'].astype(str) + '-01', format='%Y-%m-%d')

emp_mes = qtd_emprestimo_mes.sort_values(by='Data', ascending=True)

# Mapeamento de meses
meses = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}
meses_2 = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

# Mapeando o número do mês para o nome do mês
emprestimo_aluno['mes'] = emprestimo_aluno['mes'].map(meses)
ranking_alunos['mes'] = ranking_alunos['mes'].map(meses)
livros_mais_emprestados['mes'] = livros_mais_emprestados['mes'].map(meses)
qtd_emprestimo_mes['Mês'] = qtd_emprestimo_mes['Mês'].map(meses)
emp_mes['Mês'] = emp_mes['Mês'].map(meses_2)
genero_m_emprestados['mes'] = genero_m_emprestados['mes'].map(meses)


# Função para converter o DataFrame para Excel
def convert_df_to_excel(df):
    # Criar um arquivo Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# dicionario do status   
dicionario = {
    'EM_DIA': 'Em dia',
    'EM_ATRASO': 'Em atraso'
}

# renomeando os status do empréstimo
status = status.replace(dicionario)


# Extraindo os valores da consulta
total_livros_emprestados = livros_geral['total_livros_emprestados'].iloc[0]
livros_disponiveis = livros_geral['livros_disponiveis'].iloc[0]
total_geral = livros_geral['total_geral'].iloc[0]

# criando o dataframe para o grafico de pizza
distribuicao_livros = pd.DataFrame({
    'Status': ['Livros Disponíveis', 'Livros Emprestados'],
    'Quantidade': [livros_disponiveis, total_livros_emprestados]
})    

# Cálculo do total de cada status
em_dia = status[status['Status'] == 'Em dia']['Quantidade'].sum()
em_atraso = status[status['Status'] == 'Em atraso']['Quantidade'].sum()

# Cálculo do acervo de livros disponiveis e emprestados
acervo_total = qtd_livros['quantidade'].sum()
emprestimos = qtd_livro_emprestado['quantidade'].sum()

# Converter a imagem para base64
image_path = "icone_download.svg"

# Função para ajustar o arquivo Excel gerado
def ajustar_excel(df):
    # Convertemos a coluna C de string para data usando pandas
    # # Aqui assumimos que a coluna C tem o nome "C" ou você pode usar df['C'] diretamente
    # df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce', dayfirst=True)  # 'dayfirst=True' se as datas forem no formato dia-mês-ano
        
    # Salvar o DataFrame como um arquivo Excel em memória
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    # Abrir o arquivo Excel gerado
    wb = load_workbook(output)
    ws = wb.active
            
    # Criar um estilo de data
    data_style = NamedStyle(name="data_style", number_format="DD-MM-YYYY")
            
    # Ajustar largura da coluna de datas (supondo que a data esteja na coluna A)
    ws.column_dimensions['A'].width = 20  # Ajustar a largura da coluna A
    ws.column_dimensions['B'].width = 20  # Ajustar a largura da coluna B
    ws.column_dimensions['C'].width = 20  # Ajustar a largura da coluna C
    ws.column_dimensions['D'].width = 25  # Ajustar a largura da coluna D
    ws.column_dimensions['E'].width = 20  # Ajustar a largura da coluna E
    ws.column_dimensions['F'].width = 25  # Ajustar a largura da coluna F
    ws.column_dimensions['G'].width = 20  # Ajustar a largura da coluna G
        
    # Aplicar o estilo de data para todas as células da coluna A
    for cell in ws['A']:
        cell.style = data_style
            
    for cell in ws['B']:
        cell.style = data_style
            
    for cell in ws['C']:
        cell.style = data_style
                        
    # Salvar o arquivo Excel com as modificações
    output.seek(0)
    wb.save(output)
    output.seek(0)
        
    return output

with open(image_path, 'rb') as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

def to_base64(file_data):
    return base64.b64encode(file_data).decode('utf-8')

def totalizador(label, valor, df, file_name):
    excel = ajustar_excel(df)
    excel_base64 = to_base64(excel.read())
    
    totalizador_imagem = f"""
        <div style="background: #8E58BF; padding: 2px; border-radius: 15px; width: 92%;  
                    display: flex; justify-content: space-between; align-items: center; text-align: left;
                    padding-left: 19px"> 
            <div style="flex: 3">
                <h3 style="font-size: 22px; color: white; font-weight: lighter;  position: relative; top: 11px">{label}</h3>
                <p style="font-size: 42px; color: white; font-weight: bold; position: relative; left: 5px; top: -8px">
                          {valor}</p>
            </div>
            <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_base64}" 
                download="{file_name}" 
                style="position: absolute; bottom: 0px; right: 12%; text-decoration: none;">
                <img src="data:image/svg+xml;base64,{encoded_image}" alt="Ícone de download" style="width: 100%; height: 40px;" />
        </a>
            </div>
        </div>
    """
    
    st.markdown(totalizador_imagem, unsafe_allow_html=True)


# totalizador do acervo geral e o botão de download
col1, col2, col3, col4 = st.columns([0.85, 2.4, 4, 1])
with col2:
    totalizador("Acervo geral", acervo_total, acervo_geral, "acervo_geral.xlsx")
    st.write("")
    st.write("")
    totalizador("Pessoas cadastradas", emprestimos, status_alunos, "emprestimos.xlsx")
    st.write("")
    st.write("")
    totalizador("Pessoas com livros emprestados", 7, acervo_geral, "pessoas_emprestadas.xlsx")
with col3:
    with st.container(height= 498,border=True):
        
        st.write("")
        # gráfico de pizza (distribuição dos livros)
        fig_status = px.pie(status, names='Status',
                values='Quantidade',
                hole=0.53,
                title='Livros emprestados',
                color='Status', 
                color_discrete_map={'Em dia': '#D9D9D9',
                                    'Em atraso': '#CA3336'},
                height= 444)
        
        # parâmetros do gráfico
        fig_status.update_layout(
            title=dict(
                font=dict(
                    size=25,
                    color="black"    # Tamanho da fonte do título
                    )        
                ),
            legend=dict(
                font=dict(
                    size=20,
                    color="black"# Tamanho da fonte da legenda (em pixels)
                )
            ),
            margin=dict(l=30, r=30, t=50, b=30)
        )

        # Sobrepondo o valor das fatias
        fig_status.update_traces(textposition='auto',
                            textfont=dict(size=20,
                                        color="white"))
        fig_status.update_layout(
        annotations=[
            {
                "font": {"size": 65, "color": "black"},
                "showarrow": False,
                "text": f"{em_dia + em_atraso}", 
                "x": 0.5,
                "y": 0.5
            }
        ]
        )
        
        fig_status.update_traces(
                        textfont=dict(size=30,
                                    color='black'),
                        hovertemplate = '<b>%{percent}</b><br>%{label}<extra></extra>',
                        hoverlabel = dict(
                            font_size = 18
                    ),
                    textinfo= 'value')
    
        st.plotly_chart(fig_status, use_container_width=True)
    
st.write("")
st.write("")

# #############
    
# Definir as opções de filtros (ano e mês)
ano_opcoes = emprestimo_aluno['ano'].unique()
mes_opcoes = emprestimo_aluno['mes'].unique()

st.divider()

# Lista com os meses
mes = mes_opcoes.tolist()

# Layout de filtros
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col3:
    # Filtro de ano
    st.markdown("<h2 style='font-size: 20px; font-weight: bold; margin-top: -18px; position: relative; padding-bottom: 5px;'>Selecione o ano:</h2>", unsafe_allow_html=True)
    ano_selecionado = st.selectbox('Selecione o ano', ano_opcoes, label_visibility='collapsed')
    st.write("")

with col4:
    # Filtro de mês com a opção de "Todos os meses"
    st.markdown("<h2 style='font-size: 20px; font-weight: bold; margin-top: -18px; position: relative; padding-bottom: 5px;'>Selecione o mês:</h2>", unsafe_allow_html=True)
    
    # Filtrar os meses com base no ano selecionado
    meses_disponiveis = emprestimo_aluno[emprestimo_aluno['ano'] == ano_selecionado]['mes'].unique().tolist()
    
    # Adiciona "Todos os meses" como opção
    mes_selecionado = st.multiselect("Selecione o mês", meses_disponiveis, label_visibility='collapsed', placeholder="Todos")
    st.write("")

# Filtragem do DataFrame com base nas seleções
if ano_selecionado and mes_selecionado:
    # Caso "Todos os meses" seja selecionado, não filtra por mês
    if "Todos os meses" in mes_selecionado:
        filtro = emprestimo_aluno[emprestimo_aluno['ano'] == ano_selecionado]
    else:
        filtro = emprestimo_aluno[(emprestimo_aluno['ano'] == ano_selecionado) & (emprestimo_aluno['mes'].isin(mes_selecionado))]
    

# Função para gerar os livros mais emprestados e a nuvem de palavras
@st.cache_data  # Usando cache para armazenar a saída dessa função
def gerar_nuvem_emprestimos(emprestimo_aluno, ano_selecionado, mes_selecionado):
    # Agrupando e filtrando os dados conforme o ano e mês selecionados
    emp_por_mes = emprestimo_aluno.groupby(['ano', 'mes', 'livro']).size().reset_index(name='total_emprestimo')
    emp_por_mes = emp_por_mes.sort_values(by='total_emprestimo', ascending=False)

    # Verificando se "Todos os meses" foi selecionado ou se nada foi selecionado
    if not mes_selecionado or "Todos os meses" in mes_selecionado:
        # Se "Todos os meses" for selecionado ou nada for selecionado, filtra apenas pelo ano
        livros_mais_emprestados_mes = emp_por_mes.loc[
            emp_por_mes['ano'] == ano_selecionado
        ]
    else:
        # Caso contrário, filtra pelo ano e pelos meses selecionados
        livros_mais_emprestados_mes = emp_por_mes.loc[
            (emp_por_mes['ano'] == ano_selecionado) & (emp_por_mes['mes'].isin(mes_selecionado))
        ]

    # Verificar se há livros para gerar a nuvem de palavras
    if livros_mais_emprestados_mes.empty:
        st.warning("Não há dados de empréstimos para os filtros selecionados.")
        return None, None

    # Agrupar por título de livro e contar o total de empréstimos
    livros_mais_emprestados_total = livros_mais_emprestados_mes.groupby('livro')['total_emprestimo'].sum().reset_index()

    # Criar o dicionário de livros e suas quantidades de empréstimos
    livros_freq = dict(zip(livros_mais_emprestados_total['livro'], livros_mais_emprestados_total['total_emprestimo']))

    # Verificar se o dicionário de frequência está vazio
    if not livros_freq:
        st.warning("Não há livros suficientes para gerar a nuvem de palavras.")
        return None, None

    # Gerar a nuvem de palavras
    wordcloud = WordCloud(width=2000,
                          height=800,
                          max_words=30,
                          background_color='white').generate_from_frequencies(livros_freq)
    
    return wordcloud, livros_mais_emprestados_mes

# Exemplo de como você pode chamar a função e exibir a nuvem de palavras no Streamlit
nuvem1, nuvem2, nuvem3 = st.columns([1, 6, 1])
with nuvem2:
    # Receber o resultado do cache
    wordcloud, livros_mais_emprestados_mes = gerar_nuvem_emprestimos(emprestimo_aluno, ano_selecionado, mes_selecionado)

    if not mes_selecionado:  # Verifica se a lista mes_selecionado está vazia (nenhum mês selecionado)
        st.subheader(f'Livros mais emprestados em {ano_selecionado}')
    else:
        st.subheader(f'Livros mais emprestados no período selecionado')
    
    # Gerando a visualização da nuvem de palavras
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.set_axis_off()
    st.pyplot(fig)
    st.write("")


# Emprestimos por mês/ano pelo ano selecionado
emp_mes_filtrado = emp_mes[emp_mes['Ano'] == ano_selecionado]

if mes_selecionado == 'Todos os meses':
    # Gráfico de barra (emprestimos por mes)
    fig1 = px.bar(emp_mes_filtrado,
                x='Mês',
                y='Quantidade', 
                title='Empréstimos anual/mensal',
                color_discrete_sequence=["#8E58BF"],
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
                    size=22,
                    color="black"  # Tamanho da fonte do eixo X
                )
            ),
            tickfont=dict(
                size=22,
                color="black"      # Tamanho da fonte dos rótulos do eixo X
            )
        ),
        yaxis=dict(
            title=dict(
                font=dict(
                    size=22,
                    color="black"  # Tamanho da fonte do título do eixo Y
                )
            ),
            tickfont=dict(
                size=22,
                color="black"      # Tamanho da fonte dos rótulos do eixo Y
            )
        )
    )    


    fig1.update_layout(
        width=800,  # Largura
        height=500  # Altura
    )

    fig1.update_layout(
        xaxis=dict(
            tickmode='array',  # Garantir que todos os ticks sejam mostrados
            tickvals=emp_mes['Mês'],  # Certifica que os meses são usados
        )
    )

    max_y1 = emp_mes_filtrado['Quantidade'].max()


    fig1.update_layout(
        yaxis=dict(
            range=[0, max_y1 * 1.1]  # Ajuste do limite superior (aumentando 10% do valor máximo)
        )
    )

    config={
        'displayModeBar': 'hover',  # A barra de ferramentas aparece ao passar o mouse
        'modeBarButtonsToRemove': [
            'zoom', 'pan', 'resetScale', 'hover', 'zoomIn', 'zoomOut', 'resetAxes', 
            'lasso2d', 'select2d', 'zoom2d', 'pan2d', 'orbitRotation', 'tableRotation', 
            'save', 'zoom2d', 'sendDataToCloud', 'toggleSpikelines', 'toggleHover', 
            'resetView', 'toggleFullscreen'  # Remove todos os botões, incluindo o de tela cheia
        ],
        'displaylogo': False,  # Remove o logo do Plotly da barra de ferramentas
        'modeBarButtonsToAdd': ['downloadImage']  # Adiciona apenas o botão de download
    }

    # sobrepondo as barras com os valores
    fig1.update_traces(textposition='outside',
                        textfont=dict(size=20,
                                    color='black'),
                        hovertemplate = '<b>%{label}</b><br>Quantidade: %{value}<extra></extra>',
                        hoverlabel = dict(
                        font_size = 20
                    ))

    # totalizador dos emprestimos anuais
    totalizador = quantidade_ano[quantidade_ano['ano'] == ano_selecionado]
    total_emprestimos = totalizador['quantidade_emprestimos'].sum()
    fig1.add_annotation(
        x=1,  # posição x (canto direito)
        y=1.25,  # posição y (canto superior)
        text=f"{total_emprestimos} empréstimos em {ano_selecionado}",
        showarrow=False,
        font=dict(size=24, color="black"),
        align="left",
        xref="paper",  # Usando coordenadas relativas ao espaço da figura
        yref="paper",  # Usando coordenadas relativas ao espaço da figura
        bgcolor="white"  # Fundo branco para destacar
    )
else:
    # Gráfico de barra (emprestimos por mes)
    fig1 = px.bar(emp_mes_filtrado,
                x='Mês',
                y='Quantidade', 
                title='Empréstimos mensal',
                color_discrete_sequence=["#8E58BF"],
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
                    size=22,
                    color="black"  # Tamanho da fonte do eixo X
                )
            ),
            tickfont=dict(
                size=22,
                color="black"      # Tamanho da fonte dos rótulos do eixo X
            )
        ),
        yaxis=dict(
            title=dict(
                font=dict(
                    size=22,
                    color="black"  # Tamanho da fonte do título do eixo Y
                )
            ),
            tickfont=dict(
                size=22,
                color="black"      # Tamanho da fonte dos rótulos do eixo Y
            )
        )
    )    


    fig1.update_layout(
        width=800,  # Largura
        height=500  # Altura
    )

    fig1.update_layout(
        xaxis=dict(
            tickmode='array',  # Garantir que todos os ticks sejam mostrados
            tickvals=emp_mes['Mês'],  # Certifica que os meses são usados
        )
    )

    max_y1 = emp_mes_filtrado['Quantidade'].max()


    fig1.update_layout(
        yaxis=dict(
            range=[0, max_y1 * 1.1]  # Ajuste do limite superior (aumentando 10% do valor máximo)
        )
    )

    config={
        'displayModeBar': 'hover',  # A barra de ferramentas aparece ao passar o mouse
        'modeBarButtonsToRemove': [
            'zoom', 'pan', 'resetScale', 'hover', 'zoomIn', 'zoomOut', 'resetAxes', 
            'lasso2d', 'select2d', 'zoom2d', 'pan2d', 'orbitRotation', 'tableRotation', 
            'save', 'zoom2d', 'sendDataToCloud', 'toggleSpikelines', 'toggleHover', 
            'resetView', 'toggleFullscreen'  # Remove todos os botões, incluindo o de tela cheia
        ],
        'displaylogo': False,  # Remove o logo do Plotly da barra de ferramentas
        'modeBarButtonsToAdd': ['downloadImage']  # Adiciona apenas o botão de download
    }

    # sobrepondo as barras com os valores
    fig1.update_traces(textposition='outside',
                        textfont=dict(size=20,
                                    color='black'),
                        hovertemplate = '<b>%{label}</b><br>Quantidade: %{value}<extra></extra>',
                        hoverlabel = dict(
                        font_size = 20
                    ))

    # totalizador dos emprestimos anuais
    totalizador = quantidade_ano[quantidade_ano['ano'] == ano_selecionado]
    total_emprestimos = totalizador['quantidade_emprestimos'].sum()
    fig1.add_annotation(
        x=1,  # posição x (canto direito)
        y=1.25,  # posição y (canto superior)
        text=f"{total_emprestimos} empréstimos em {ano_selecionado}",
        showarrow=False,
        font=dict(size=24, color="black"),
        align="left",
        xref="paper",  # Usando coordenadas relativas ao espaço da figura
        yref="paper",  # Usando coordenadas relativas ao espaço da figura
        bgcolor="white"  # Fundo branco para destacar
    )

# plotando o gráfico de barras (emprestimos por mês)
with st.container(border=True):
    st.plotly_chart(fig1, use_container_width=True, config=config)


# Verificando se mes_selecionado está vazio ou se "Todos os meses" foi selecionado
if mes_selecionado and mes_selecionado != 'Todos os meses':
    # Filtrando os dados com base nas seleções de ano e mês
    generos_filtrados = genero_m_emprestados[
        (genero_m_emprestados['ano'] == ano_selecionado) & 
        (genero_m_emprestados['mes'].isin(mes_selecionado))  # Usando .isin para múltiplos meses
    ]
    # Agregar por gênero somando as quantidades de empréstimos
    genero_total_filtrado = generos_filtrados.groupby('Gênero')['Quantidade'].sum().reset_index()
    genero_total_filtrado = genero_total_filtrado.sort_values(by='Quantidade', ascending=False)
    
    # Gerando o gráfico de barras
    fig2 = px.bar(genero_total_filtrado, x='Gênero', y='Quantidade',
                title=f'Empréstimos por gênero',
                color='Gênero',
                text='Quantidade')
    fig2.update_layout(
        title=dict(
            font=dict(
                size=26             # Tamanho da fonte do título
            )
        ),
        xaxis=dict(
            title=dict(
                font=dict(
                    size=22,
                    color="black"   # Tamanho da fonte do título do eixo X
                )
            ),
            tickfont=dict(
                size=22,
                color="black"
                                    # Tamanho da fonte dos rótulos do eixo X
            )
        ),
        yaxis=dict(
            title=dict(
                font=dict(
                    size=22,
                    color="black"   # Tamanho da fonte do título do eixo Y
                )
            ),
            tickfont=dict(
                size=22,
                color="black"       # Tamanho da fonte dos rótulos do eixo Y
            )
        ),
        legend=dict(
            font=dict(
                size=20,
                color="black"       # Tamanho da fonte da legenda
            )
        )
    )

    # sobrepondo as barras do gráfico de gêneros
    fig2.update_traces(textposition='outside',
                        textfont=dict(size=22,
                                    color='black'),
                        hovertemplate = '<b>%{label}</b><br>Quantidade: %{value}<extra></extra>',
                        hoverlabel = dict(
                            font_size = 18
                    ))

    max_y2 = genero_total_filtrado['Quantidade'].max()

    fig2.update_layout(
        xaxis=dict(
            tickmode='array',  # Garantir que todos os ticks sejam mostrados
            tickvals=genero_total['Gênero'],  # Certifica que os meses são usados
        )
    )

    fig2.update_layout(
        width=800,  # Largura
        height=500  # Altura
    )

    fig2.update_layout(
        yaxis=dict(
            range=[0, max_y2 * 1.1]  # Ajuste do limite superior (aumentando 10% do valor máximo)
        )
    )
    fig2.update_layout(
        legend=dict(
            title=dict(  # Texto do título da legenda
                font=dict(size=20)  # Tamanho da fonte do título
            ),
        )
    )
else:
    # Se "Todos os meses" foi selecionado ou nada foi selecionado, apenas filtra por ano
    generos_filtrados = genero_m_emprestados[genero_m_emprestados['ano'] == ano_selecionado]
 
    # Agregar por gênero somando as quantidades de empréstimos
    genero_total_filtrado = generos_filtrados.groupby('Gênero')['Quantidade'].sum().reset_index()
    genero_total_filtrado = genero_total_filtrado.sort_values(by='Quantidade', ascending=False)

    # Definir as cores personalizadas para o gráfico
    custom_colors = ['#BEA6FF', '#AF54E4', '#A18AC2', '#8E74D2',
                    '#751AAA', '#DCCEFF', '#A887FF', '#4E358E',
                    '#7B7097', '#824BA7']

    # Gerando o gráfico de barras
    fig2 = px.bar(genero_total_filtrado, x='Gênero', y='Quantidade',
                title=f'Empréstimos por gênero',
                color='Gênero',
                text='Quantidade')
    fig2.update_layout(
        title=dict(
            font=dict(
                size=26             # Tamanho da fonte do título
            )
        ),
        xaxis=dict(
            title=dict(
                font=dict(
                    size=22,
                    color="black"   # Tamanho da fonte do título do eixo X
                )
            ),
            tickfont=dict(
                size=22,
                color="black"
                                    # Tamanho da fonte dos rótulos do eixo X
            )
        ),
        yaxis=dict(
            title=dict(
                font=dict(
                    size=22,
                    color="black"   # Tamanho da fonte do título do eixo Y
                )
            ),
            tickfont=dict(
                size=22,
                color="black"       # Tamanho da fonte dos rótulos do eixo Y
            )
        ),
        legend=dict(
            font=dict(
                size=20,
                color="black"       # Tamanho da fonte da legenda
            )
        )
    )

    # sobrepondo as barras do gráfico de gêneros
    fig2.update_traces(textposition='outside',
                        textfont=dict(size=22,
                                    color='black'),
                        hovertemplate = '<b>%{label}</b><br>Quantidade: %{value}<extra></extra>',
                        hoverlabel = dict(
                            font_size = 18
                    ))

    max_y2 = genero_total_filtrado['Quantidade'].max()

    fig2.update_layout(
        xaxis=dict(
            tickmode='array',  # Garantir que todos os ticks sejam mostrados
            tickvals=genero_total['Gênero'],  # Certifica que os meses são usados
        )
    )

    fig2.update_layout(
        width=800,  # Largura
        height=500  # Altura
    )

    fig2.update_layout(
        yaxis=dict(
            range=[0, max_y2 * 1.1]  # Ajuste do limite superior (aumentando 10% do valor máximo)
        )
    )
    fig2.update_layout(
        legend=dict(
            title=dict(  # Texto do título da legenda
                font=dict(size=20)  # Tamanho da fonte do título
            ),
        )
    )

# plotando o grafico de barras (gêneros mais emprestados)
with st.container(border=True):
    st.plotly_chart(fig2, use_container_width=True, config=config)    
    
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
        background-color: #8E58BF;
        font-weight: bold;
    }
    /* Linhas com fundo branco e roxo claro alternado */
    tr:nth-child(odd) {
        background-color: #65558F17; /* Cinza claro */
    }
    tr:nth-child(even) {
        background-color: white; /* Branco */
    }
    </style>
    """,
    unsafe_allow_html=True
    )


# Tabelas de livros e alunos
bar1, bar2 = st.columns([2.6, 2])

# Total de livros pelo ano selecionado
livros_total_filtrado_ano = livros_total[livros_total['ano'] == ano_selecionado]
livros_total_filtrado_ano['mes'] = livros_total_filtrado_ano['mes'].map(meses)

with bar1:
    if 'Todos os meses' in mes_selecionado or not mes_selecionado:
        livros_total_filtrado = livros_total_filtrado_ano.rename(columns={
            'titulo': 'Título',
            'quantidade_emprestimos': 'N° empréstimos'
        })
        livros_total_filtrado = livros_total_filtrado.groupby('Título')['N° empréstimos'].sum().reset_index()
        livros_tabela = livros_total_filtrado
        livros_total_filtrado = livros_total_filtrado[['Título', 'N° empréstimos']].nlargest(10, 'N° empréstimos')
        livros_total_filtrado = livros_total_filtrado.to_html(index=False)        
        st.write("## Ranking de livros")
        st.markdown(f'<div class="center-table">{livros_total_filtrado}</div>', unsafe_allow_html=True)
        
        # Função para ajustar o arquivo Excel gerado
        def ajustar_excel(df):
            # Salvar o DataFrame em um arquivo Excel em memória (sem salvar no disco)
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            # Abrir o arquivo Excel gerado
            wb = load_workbook(output)
            ws = wb.active
            
            # Criar um estilo de data
            data_style = NamedStyle(name="data_style")
            
            # Ajustar largura da coluna de datas (supondo que a data esteja na coluna A)
            ws.column_dimensions['A'].width = 30  # Ajustar a largura da coluna A
            ws.column_dimensions['B'].width = 20  # Ajustar a largura da coluna B
            ws.column_dimensions['C'].width = 20  # Ajustar a largura da coluna C
                    
            # Aplicar o estilo de data para todas as células da coluna A
            for cell in ws['A']:
                cell.style = data_style
            
            for cell in ws['B']:
                cell.style = data_style
            
            for cell in ws['C']:
                cell.style = data_style
            
            # Salvar o arquivo Excel com as modificações
            output.seek(0)
            wb.save(output)
            output.seek(0)
            
            return output
        
        # Download dos livros
        excel = ajustar_excel(livros_tabela)
        st.download_button(
        label="Baixar relatório de empréstimos",
        data=excel,
        file_name='tabela_livros.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    else:
        # Caso contrário, filtra pelos meses selecionados
        livros_total_filtrado_mes_selecionado = livros_total_filtrado_ano[
            livros_total_filtrado_ano['mes'].isin(mes_selecionado)
        ]
        livros_total_filtrado_mes_selecionado = livros_total_filtrado_mes_selecionado.rename(columns={
            'titulo': 'Título',
            'quantidade_emprestimos': 'N° empréstimos'
        })
        
        # Somando os empréstimos para os meses selecionados
        livros_total_filtrado_mes_selecionado = livros_total_filtrado_mes_selecionado.groupby('Título')['N° empréstimos'].sum().reset_index()
        tabela_livros = livros_total_filtrado_mes_selecionado
        livros_total_filtrado_mes_selecionado = livros_total_filtrado_mes_selecionado.nlargest(10, 'N° empréstimos')  # Pega os top 10 livros
        livros_total_filtrado_mes_selecionado = livros_total_filtrado_mes_selecionado.to_html(index=False)
        st.write("## Ranking de livros")
        st.markdown(f'<div class="center-table">{livros_total_filtrado_mes_selecionado}</div>', unsafe_allow_html=True)
        
        # Função para ajustar o arquivo Excel gerado
        def ajustar_excel(df):
            # Salvar o DataFrame em um arquivo Excel em memória (sem salvar no disco)
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            # Abrir o arquivo Excel gerado
            wb = load_workbook(output)
            ws = wb.active
            
            # Criar um estilo de data
            data_style = NamedStyle(name="data_style")
            
            # Ajustar largura da coluna de datas (supondo que a data esteja na coluna A)
            ws.column_dimensions['A'].width = 30  # Ajustar a largura da coluna A
            ws.column_dimensions['B'].width = 20  # Ajustar a largura da coluna B
            ws.column_dimensions['C'].width = 20  # Ajustar a largura da coluna C
                    
            # Aplicar o estilo de data para todas as células da coluna A
            for cell in ws['A']:
                cell.style = data_style
            
            for cell in ws['B']:
                cell.style = data_style
            
            for cell in ws['C']:
                cell.style = data_style
            
            # Salvar o arquivo Excel com as modificações
            output.seek(0)
            wb.save(output)
            output.seek(0)
            
            return output
        
        # Download dos livros
        excel = ajustar_excel(tabela_livros)
        st.download_button(
        label="Baixar relatório de empréstimos",
        data=excel,
        file_name='tabela_livros.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Total de alunos filtrado pelo ano selecionado
print(total_alunos)
total_alunos_filtrado_ano_completo = total_alunos[total_alunos['ano'] == ano_selecionado]
total_alunos_filtrado_ano_completo['mes'] = total_alunos_filtrado_ano_completo['mes'].map(meses)
print(total_alunos_filtrado_ano_completo)

with bar2:
    # Verificando se foi selecionado "Todos os meses" ou nenhum mês foi selecionado
    if 'Todos os meses' in mes_selecionado or not mes_selecionado:
        # Caso "Todos os meses" ou nenhum mês tenha sido selecionado, mostrar os dados do ano completo
        total_alunos_filtrado = total_alunos_filtrado_ano_completo.rename(columns={
            'nome': 'Nome',
            'quantidade_emprestimos': 'N° empréstimos'
        })
        # Somando todos os empréstimos para o ano
        total_alunos_filtrado = total_alunos_filtrado.groupby('Nome')['N° empréstimos'].sum().reset_index()
        tabela_alunos = total_alunos_filtrado
        total_alunos_filtrado = total_alunos_filtrado.nlargest(10, 'N° empréstimos')  # Pega os top 10 alunos
        tabela_total_alunos = total_alunos_filtrado
        total_alunos_filtrado = total_alunos_filtrado.to_html(index=False, escape=False)
        st.write("## Ranking de alunos")
        st.markdown(f'<div class="center-table">{total_alunos_filtrado}</div>', unsafe_allow_html=True)
        
        # Função para ajustar o arquivo Excel gerado
        def ajustar_excel(df):
            # Salvar o DataFrame em um arquivo Excel em memória (sem salvar no disco)
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            # Abrir o arquivo Excel gerado
            wb = load_workbook(output)
            ws = wb.active
            
            # Criar um estilo de data
            data_style = NamedStyle(name="data_style")
            
            # Ajustar largura da coluna de datas (supondo que a data esteja na coluna A)
            ws.column_dimensions['A'].width = 20  # Ajustar a largura da coluna A
            ws.column_dimensions['B'].width = 20  # Ajustar a largura da coluna B
            ws.column_dimensions['C'].width = 20  # Ajustar a largura da coluna C
                    
            # Aplicar o estilo de data para todas as células da coluna A
            for cell in ws['A']:
                cell.style = data_style
            
            for cell in ws['B']:
                cell.style = data_style
            
            for cell in ws['C']:
                cell.style = data_style
            
            # Salvar o arquivo Excel com as modificações
            output.seek(0)
            wb.save(output)
            output.seek(0)
            
            return output
        
        excel = ajustar_excel(tabela_total_alunos)
        st.download_button(
            label="Baixar relatório de pessoas",
            data=excel,
            file_name='tabela_alunos.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
     )
            
    else:
        # Caso contrário, filtra pelos meses selecionados
        total_alunos_filtrado_mes_selecionado = total_alunos_filtrado_ano_completo[
            total_alunos_filtrado_ano_completo['mes'].isin(mes_selecionado)
        ]
        total_alunos_filtrado_mes_selecionado = total_alunos_filtrado_mes_selecionado.rename(columns={
            'nome': 'Nome',
            'quantidade_emprestimos': 'N° empréstimos'
        })
        # Somando os empréstimos para os meses selecionados
        total_alunos_filtrado_mes_selecionado = total_alunos_filtrado_mes_selecionado.groupby('Nome')['N° empréstimos'].sum().reset_index()
        tabela_alunos = total_alunos_filtrado_mes_selecionado
        total_alunos_filtrado_mes_selecionado = total_alunos_filtrado_mes_selecionado.nlargest(10, 'N° empréstimos')  # Pega os top 10 alunos
        total_alunos_filtrado_mes_selecionado = total_alunos_filtrado_mes_selecionado.to_html(index=False, escape=False)
        st.write(f"## Ranking de alunos")
        st.markdown(f'<div class="center-table">{total_alunos_filtrado_mes_selecionado}</div>', unsafe_allow_html=True)
    
        # Função para ajustar o arquivo Excel gerado
        def ajustar_excel(df):
            # Salvar o DataFrame em um arquivo Excel em memória (sem salvar no disco)
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            # Abrir o arquivo Excel gerado
            wb = load_workbook(output)
            ws = wb.active
            
            # Criar um estilo de data
            data_style = NamedStyle(name="data_style")
            
            # Ajustar largura da coluna de datas (supondo que a data esteja na coluna A)
            ws.column_dimensions['A'].width = 20  # Ajustar a largura da coluna A
            ws.column_dimensions['B'].width = 20  # Ajustar a largura da coluna B
            ws.column_dimensions['C'].width = 20  # Ajustar a largura da coluna C
                    
            # Aplicar o estilo de data para todas as células da coluna A
            for cell in ws['A']:
                cell.style = data_style
            
            for cell in ws['B']:
                cell.style = data_style
            
            for cell in ws['C']:
                cell.style = data_style
            
            # Salvar o arquivo Excel com as modificações
            output.seek(0)
            wb.save(output)
            output.seek(0)
            
            return output
    
        excel = convert_df_to_excel(tabela_alunos)
        st.download_button(
            label="Baixar relatório de pessoas",
            data=excel,
            file_name='tabela_alunos.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
