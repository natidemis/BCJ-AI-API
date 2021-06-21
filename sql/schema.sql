CREATE TABLE IF NOT EXISTS Vectors(
    id integer primary key,
    summary double precision[],
    descr double precision[],
    bucket varchar(128),
    dateUP date
);