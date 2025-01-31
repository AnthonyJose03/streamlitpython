import sqlalchemy

DB_CONFIG = {
    "usuario": "postgres",
    "senha": "rzEe42WpuRgpwA3O",
    "host": "monstrously-dexterous-arachnid.data-1.use1.tembo.io",
    "porta": "5432",
    "nome_do_banco": "app",
}

engine = sqlalchemy.create_engine(
    f"postgresql+psycopg2://{DB_CONFIG['usuario']}:{DB_CONFIG['senha']}@{DB_CONFIG['host']}:{DB_CONFIG['porta']}/{DB_CONFIG['nome_do_banco']}",
    connect_args={"client_encoding": "utf8"},
)

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
where
    id_escola = %s
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
    l.id_escola = %s
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

pessoas_com_livro = """
WITH emprestimo AS (
    SELECT 
        aluno.id,
        aluno.nome as "Nome",
        aluno.telefone as "Telefone"
    FROM emprestimo
    LEFT JOIN aluno ON emprestimo.id_aluno = aluno.id
    where emprestimo.id_escola = %s
)
SELECT DISTINCT ON (id) id, "Nome", "Telefone"
FROM emprestimo
ORDER BY id;
"""

pessoas_cadastradas = """
select 
    id,
    nome as "Nome",
    telefone as "Telefone"
from 
    aluno a 
where 
    id_escola = %s
"""
