USE monte_sinai;

CREATE OR REPLACE VIEW vw_media_giro_semanal AS
SELECT
    codigo,
    produto,
    unidade_medida,
    ROUND(AVG(total_saida_semana), 2) AS media_giro_semanal,
    SUM(total_saida_semana) AS total_saida_periodo,
    COUNT(*) AS semanas_com_saida
FROM vw_giro_semanal
GROUP BY
    codigo,
    produto,
    unidade_medida;
    
SELECT *
FROM vw_media_giro_semanal
ORDER BY media_giro_semanal DESC;