CREATE TABLE IF NOT EXISTS statistics (mission_id INTEGER NOT NULL, player_ucid TEXT NOT NULL, slot TEXT NOT NULL, side INTEGER DEFAULT 0, kills INTEGER DEFAULT 0, pvp INTEGER DEFAULT 0, deaths INTEGER DEFAULT 0, ejections INTEGER DEFAULT 0, crashes INTEGER DEFAULT 0, teamkills INTEGER DEFAULT 0, kills_planes INTEGER DEFAULT 0, kills_helicopters INTEGER DEFAULT 0, kills_ships INTEGER DEFAULT 0, kills_sams INTEGER DEFAULT 0, kills_ground INTEGER DEFAULT 0, deaths_pvp INTEGER DEFAULT 0, deaths_planes INTEGER DEFAULT 0, deaths_helicopters INTEGER DEFAULT 0, deaths_ships INTEGER DEFAULT 0, deaths_sams INTEGER DEFAULT 0, deaths_ground INTEGER DEFAULT 0, takeoffs INTEGER DEFAULT 0, landings INTEGER DEFAULT 0, hop_on TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'), hop_off TIMESTAMP, PRIMARY KEY (mission_id, player_ucid, slot, hop_on));
CREATE INDEX IF NOT EXISTS idx_statistics_player_ucid ON statistics(player_ucid);
CREATE TABLE IF NOT EXISTS squadrons (id SERIAL PRIMARY KEY, name TEXT NOT NULL, description TEXT NULL, role BIGINT NULL, image_url TEXT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS idx_squadrons_name ON squadrons (name);
CREATE TABLE IF NOT EXISTS squadron_members (squadron_id INTEGER NOT NULL, player_ucid TEXT NOT NULL, PRIMARY KEY (squadron_id, player_ucid));
