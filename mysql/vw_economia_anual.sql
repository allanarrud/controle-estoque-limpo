USE monte_sinai;

CREATE OR REPLACE VIEW vw_economia_anual AS
SELECT
    pf.codigo,
    pf.produto,
    pf.fornecedor,
    pf.preco,
    mb.menor_preco,

    -- diferença de preço por KG
    (pf.preco - mb.menor_preco) AS diferenca_preco_kg,

    -- diferença convertida para grama
    (pf.preco - mb.menor_preco) / 1000 AS diferenca_preco_g,

    ca.unidade_medida,
    ca.media_giro_semanal,
    ca.consumo_anual_estimado,

    -- economia anual CORRETA
    ROUND(
        ((pf.preco - mb.menor_preco) / 1000) * ca.consumo_anual_estimado,
        2
    ) AS economia_anual_potencial

FROM precos_fornecedores pf

JOIN vw_melhor_preco mb
    ON pf.codigo = mb.codigo

JOIN vw_consumo_anual_estimado ca
    ON pf.codigo = ca.codigo;
    
SELECT *
FROM vw_economia_anual
ORDER BY economia_anual_potencial DESC;