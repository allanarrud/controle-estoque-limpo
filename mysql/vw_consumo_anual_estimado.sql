USE monte_sinai;

CREATE OR REPLACE VIEW vw_consumo_anual_estimado AS
SELECT
    codigo,
    produto,
    unidade_medida,
    media_giro_semanal,
    ROUND(media_giro_semanal * 52, 2) AS consumo_anual_estimado
FROM vw_media_giro_semanal;

SELECT *
FROM vw_consumo_anual_estimado
ORDER BY consumo_anual_estimado DESC;