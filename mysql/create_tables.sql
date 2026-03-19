create table produtos (
	id int auto_increment primary key,
    codigo varchar(20) not null unique,
    produto varchar(100) not null,
    unidade_medida enum('g', 'un') not null,
    estoque_minimo decimal(10, 2) not null default 0,
    validade_dias int null,
    created_at timestamp default current_timestamp
);

create table entradas (
	id int auto_increment primary key,
    data_entrada date not null,
    codigo_produto varchar(20) not null,
    produto varchar(100) not null,
    unidade_medida enum('g', 'un') not null,
    quantidade decimal(10,2) not null,
    observacao varchar(255),
    created_at timestamp default current_timestamp,
    foreign key (codigo_produto) references produtos(codigo)
);

create table saidas (
	id int auto_increment primary key,
    data_saida date not null,
    codigo_produto varchar(20) not null,
    produto varchar(100) not null,
    unidade_medida enum('g', 'un') not null,
    quantidade decimal(10,2) not null,
    funcionario varchar(100),
    validade date null,
    created_at timestamp default current_timestamp,
    foreign key (codigo_produto) references produtos(codigo)
);