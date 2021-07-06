CREATE TABLE IF NOT EXISTS Vectors(
    id integer primary key,
    summary double precision[],
    descr double precision[],
    batch_id integer,
    dateUP varchar(128)
);