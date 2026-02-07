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

    room_id TEXT NOT NULL,
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
    race TEXT NOT NULL,

    x int NULL,
    y int NULL,
    map_id integer NULL REFERENCES maps(id)
);


CREATE TABLE IF NOT EXISTS audio_files (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    name TEXT NOT NULL,
    external_id TEXT UNIQUE NOT NULL,

    game_id int NOT NULL REFERENCES games(id),
    url TEXT NOT NULL,
    duration_seconds int NOT NULL
);


CREATE TABLE IF NOT EXISTS video_files (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    name TEXT NOT NULL,
    external_id TEXT UNIQUE NOT NULL,

    game_id int NOT NULL REFERENCES games(id),
    url TEXT NOT NULL,
    duration_seconds int NOT NULL
);


CREATE TABLE IF NOT EXISTS maps (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    external_id TEXT UNIQUE NOT NULL,

    game_id int UNIQUE NOT NULL REFERENCES games(id),
    url TEXT NOT NULL,
    x_center integer DEFAULT 50,
    y_center integer DEFAULT 50,
    zoom float DEFAULT 1
);


CREATE TABLE IF NOT EXISTS items (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    external_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,

    game_id int NOT NULL REFERENCES games(id),

    map_id int NULL REFERENCES games(id),
    x int NULL,
    y int NULL,

    icon_url TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS fog_erace_points (
    created_at TIMESTAMPTZ DEFAULT NOW(),

    map_id int NULL REFERENCES games(id),
    x int NOT NULL,
    y int NOT NULL,

    radius int not NULL,
    CONSTRAINT fog_unique_x_y UNIQUE (x, y, map_id, radius)
);

insert into audio_files (external_id, name, game_id, url, duration_seconds) values
('audio-fight', 'fight', 1, 'https://storage.yandexcloud.net/dnd2/audio/fight.mp3', 60),
('audio-horror', 'horror', 1, 'https://storage.yandexcloud.net/dnd2/audio/horror.mp3', 60),
('audio-ambient', 'ambient', 1, 'https://storage.yandexcloud.net/dnd2/audio/ambient.mp3', 60),
('audio-fire', 'fire', 1, 'https://storage.yandexcloud.net/dnd2/audio/fire.mp3', 60);

insert into video_files (external_id, name, game_id, url, duration_seconds) values
('video-1', '1', 1, 'https://storage.yandexcloud.net/dnd2/video/1.mp4', 10),
('video-2', '2', 1, 'https://storage.yandexcloud.net/dnd2/video/2.mp4', 10),
('video-3', '3', 1, 'https://storage.yandexcloud.net/dnd2/video/3.mp4', 10),
('video-4', '4', 1, 'https://storage.yandexcloud.net/dnd2/video/4.mp4', 10);


insert into masters (external_id) values ('alexey');

insert into games (external_id, name, master_id, master_join_link) values ('123', 'Game #1', 1, 'qwe');

insert into characters (external_id, name, game_id, join_link, avatar_url, race) values
('player-1', 'Arnold', 1, 'rty', 'https://storage.yandexcloud.net/dnd2/player1.jpg', 'elf');

insert into maps (game_id, url) values (1, 'https://storage.yandexcloud.net/dnd2/map.png');

insert into items (game_id, external_id, name, icon_url) values (1, '1', 'Меч', 'https://images.vexels.com/media/users/3/273074/isolated/preview/496885a8007d7ce0df514a51798953a1-role-play-games-sword-icon.png');


insert into items (game_id, external_id, name, icon_url) values (1, '2', 'Копьё', 'https://t3.ftcdn.net/jpg/07/10/08/60/360_F_710086003_NfIuJb5QwLI6T60BxtI3xWj1TIYGCsiD.jpg');
