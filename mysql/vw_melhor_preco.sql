USE monte_sinai;

CREATE OR REPLACE VIEW vw_melhor_preco AS
SELECT
    codigo,
    produto,
    MIN(preco) AS menor_preco
FROM precos_fornecedores
GROUP BY codigo, produto;

SELECT *
FROM vw_melhor_preco
ORDER BY menor_preco ASC;