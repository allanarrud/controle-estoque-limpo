
SELECT
    codigo_produto,
    SUM(quantidade) AS total_saida_30d,
    COUNT(DISTINCT data_saida) AS dias_com_saida,
    ROUND(SUM(quantidade) / 30, 2) AS media_diaria_30d
FROM saidas
WHERE data_saida >= CURDATE() - INTERVAL 30 DAY
GROUP BY codigo_produto;