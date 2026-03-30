USE monte_sinai;

CREATE OR REPLACE VIEW vw_previsao_estoque AS
SELECT
    p.codigo,
    p.produto,
    p.unidade_medida,

    -- estoque atual
    e.total_entradas - COALESCE(s.total_saidas, 0) AS estoque_atual,

    -- média diária
    COALESCE(m.media_diaria, 0) AS media_diaria,

    -- dias restantes
    CASE
        WHEN COALESCE(m.media_diaria, 0) = 0 THEN NULL
        ELSE ROUND((e.total_entradas - COALESCE(s.total_saidas, 0)) / m.media_diaria, 1)
    END AS dias_restantes,

    -- data estimada de ruptura
    CASE
        WHEN COALESCE(m.media_diaria, 0) = 0 THEN NULL
        ELSE DATE_ADD(CURDATE(), INTERVAL 
            ROUND((e.total_entradas - COALESCE(s.total_saidas, 0)) / m.media_diaria)
        DAY)
    END AS data_ruptura,

    -- ALERTA: comprar 7 dias antes de acabar
    CASE
        WHEN COALESCE(m.media_diaria, 0) = 0 THEN NULL
        ELSE DATE_SUB(
            DATE_ADD(CURDATE(), INTERVAL 
                ROUND((e.total_entradas - COALESCE(s.total_saidas, 0)) / m.media_diaria)
            DAY),
            INTERVAL 7 DAY
        )
    END AS data_alerta_compra,

    -- status
    CASE
        WHEN COALESCE(m.media_diaria, 0) = 0 THEN 'SEM GIRO'
        WHEN ((e.total_entradas - COALESCE(s.total_saidas, 0)) / m.media_diaria) <= 7 THEN 'CRITICO'
        WHEN ((e.total_entradas - COALESCE(s.total_saidas, 0)) / m.media_diaria) <= 14 THEN 'ATENCAO'
        ELSE 'OK'
    END AS status

FROM (
    SELECT codigo_produto, SUM(quantidade) AS total_entradas
    FROM entradas
    GROUP BY codigo_produto
) e

JOIN produtos p ON p.codigo = e.codigo_produto

LEFT JOIN (
    SELECT codigo_produto, SUM(quantidade) AS total_saidas
    FROM saidas
    GROUP BY codigo_produto
) s ON p.codigo = s.codigo_produto

LEFT JOIN (
    SELECT 
        codigo_produto,
        ROUND(SUM(quantidade) / 30, 2) AS media_diaria
    FROM saidas
    WHERE data_saida >= CURDATE() - INTERVAL 30 DAY
    GROUP BY codigo_produto
) m ON p.codigo = m.codigo_produto;

SELECT *
FROM vw_previsao_estoque
ORDER BY dias_restantes ASC