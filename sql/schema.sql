CREATE TABLE IF NOT EXISTS Vectors(
    id varchar(128) primary key,
    summary double precision[],
    descr double precision[],
    batch_id varchar(128),
    dateUP varchar(128)
);