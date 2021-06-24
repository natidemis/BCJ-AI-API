CREATE TABLE IF NOT EXISTS Vectors(
    id varchar(128) primary key,
    summary double precision[],
    descr double precision[],
    bucket varchar(128),
    dateUP varchar(128)
);