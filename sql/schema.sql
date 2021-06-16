CREATE TABLE IF NOT EXISTS Vectors(
    id integer primary key,
    vector double precision[] not null,
    bucket varchar(128) not null 
);