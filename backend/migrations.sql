CREATE TABLE IF NOT EXISTS masters (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    external_id TEXT UNIQUE NOT NULL
);



CREATE TABLE IF NOT EXISTS games (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    name TEXT NOT NULL,
    external_id TEXT UNIQUE NOT NULL,

    master_id integer NOT NULL REFERENCES masters(id),
    master_join_link TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS characters (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    external_id TEXT UNIQUE NOT NULL,

    name TEXT NOT NULL,

    game_id integer NOT NULL REFERENCES games(id),
    join_link TEXT NOT NULL,

    avatar_url TEXT NOT NULL,
    race TEXT NOT NULL
);


insert into masters (external_id) values ('alexey');

insert into games (external_id, master_id, master_join_link) values ('123', 1, 'qwe');

insert into characters (external_id, name, game_id, join_link, avatar_url, race) values
('player-1', 'Arnold', 1, 'rty', 'https://google.com', 'elf');
