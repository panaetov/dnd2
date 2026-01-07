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
    master_join_link TEXT NOT NULL,
    master_avatar_url TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS characters (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    external_id TEXT UNIQUE NOT NULL,

    name TEXT NOT NULL,

    color TEXT NOT NULL DEFAULT '#0000ff',

    game_id integer NOT NULL REFERENCES games(id),
    join_link TEXT NOT NULL,

    avatar_url TEXT NOT NULL,
    race TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS maps (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    game_id int UNIQUE NOT NULL REFERENCES games(id),
    url TEXT NOT NULL,
    x_center integer DEFAULT 50,
    y_center integer DEFAULT 50,
    zoom float DEFAULT 1
);


insert into masters (external_id) values ('alexey');

insert into games (external_id, name, master_id, master_join_link) values ('123', 'Game #1', 1, 'qwe');

insert into characters (external_id, name, game_id, join_link, avatar_url, race) values
('player-1', 'Arnold', 1, 'rty', 'https://storage.yandexcloud.net/dnd2/player1.jpg', 'elf');

insert into maps (game_id, url) values (1, 'https://storage.yandexcloud.net/dnd2/map.png');
