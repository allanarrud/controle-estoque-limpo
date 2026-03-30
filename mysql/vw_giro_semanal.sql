USE monte_sinai;

CREATE OR REPLACE VIEW vw_giro_semanal AS
SELECT
    s.codigo_produto AS codigo,
    p.produto,
    p.unidade_medida,
    YEAR(s.data_saida) AS ano,
    WEEK(s.data_saida, 1) AS semana,
    SUM(s.quantidade) AS total_saida_semana
FROM saidas s
JOIN produtos p
    ON s.codigo_produto = p.codigo
GROUP BY
    s.codigo_produto,
    p.produto,
    p.unidade_medida,
    YEAR(s.data_saida),
    WEEK(s.data_saida, 1);
    
SELECT *
FROM vw_giro_semanal
ORDER BY ano DESC, semana DESC, total_saida_semana DESC;