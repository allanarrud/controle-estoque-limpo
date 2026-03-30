SELECT 
    p.codigo,
    p.produto,
    p.unidade_medida,
    COALESCE(e.total_entradas, 0) AS total_entradas,
    COALESCE(s.total_saidas, 0) AS total_saidas,
    COALESCE(e.total_entradas, 0) - COALESCE(s.total_saidas, 0) AS estoque_atual
FROM produtos p
LEFT JOIN (
    SELECT codigo_produto, SUM(quantidade) AS total_entradas
    FROM entradas
    GROUP BY codigo_produto
) e ON p.codigo = e.codigo_produto
LEFT JOIN (
    SELECT codigo_produto, SUM(quantidade) AS total_saidas
    FROM saidas
    GROUP BY codigo_produto
) s ON p.codigo = s.codigo_produto;