CREATE TABLE IF NOT EXISTS Vectors(
    id integer primary key,
    summary double precision[],
    descr double precision[],
    batch_id integer,
    dateUP varchar(128)
);

CREATE INDEX vectors_id on Vectors(id);
CREATE INDEX vectors_batch on Vectors(batch_id);