INSERT INTO entradas (data_entrada, codigo_produto, produto, unidade_medida, quantidade, observacao)
VALUES
('2026-03-19', 'ERV-001', 'AMORA BRANCA', 'g', 20000, 'Compra inicial'),
('2026-03-19', 'ERV-002', 'BOLDO', 'g', 15000, 'Compra inicial'),
('2026-03-19', 'UN-001', 'GARRAFA 500ML', 'un', 50, 'Compra inicial');

INSERT INTO saidas (data_saida, codigo_produto, produto, unidade_medida, quantidade, funcionario)
VALUES
('2026-03-19', 'ERV-001', 'AMORA BRANCA', 'g', 500, 'João'),
('2026-03-19', 'ERV-002', 'BOLDO', 'g', 200, 'Maria'),
('2026-03-19', 'UN-001', 'GARRAFA 500ML', 'un', 5, 'Carlos');