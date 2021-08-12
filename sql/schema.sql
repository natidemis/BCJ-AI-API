CREATE TABLE IF NOT EXISTS Users(
    user_id varchar(128) primary key
);
CREATE TABLE IF NOT EXISTS Vectors(
    id bigint not null,
    user_id varchar(128) not null,
    embeddings double precision[] not null,
    batch_id bigint,
    primary key (id, user_id),
    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
            REFERENCES Users(user_id)
);
CREATE INDEX IF NOT EXISTS vectors_id on Vectors(id);
CREATE INDEX IF NOT EXISTS vectors_batch on Vectors(batch_id);
CREATE INDEX IF NOT EXISTS vector_unique on Vectors(id,user_id);
CREATE INDEX IF NOT EXISTS vectors_user_id on Vectors(user_id);
CREATE INDEX IF NOT EXISTS users_idx on Users(user_id)