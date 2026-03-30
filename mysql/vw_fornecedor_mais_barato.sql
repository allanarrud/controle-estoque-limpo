USE monte_sinai;

CREATE OR REPLACE VIEW vw_fornecedor_mais_barato AS
SELECT
    p.codigo,
    p.produto,
    p.fornecedor,
    p.preco AS menor_preco
FROM precos_fornecedores p
JOIN vw_melhor_preco m
    ON p.codigo = m.codigo
   AND p.preco = m.menor_preco;
   
SELECT *
FROM vw_fornecedor_mais_barato;