create table accounts (
    id serial primary key,
    name varchar(50) not null,
    balance int not null
);

insert into accounts (name, balance) values ('test1', 1000), ('test2', 1000);