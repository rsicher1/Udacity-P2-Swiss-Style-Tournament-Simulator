-- Tournament database will not drop with other sessions using it
SELECT 
    pg_terminate_backend(pg_stat_activity.pid)
FROM 
    pg_stat_activity
WHERE 
    pg_stat_activity.datname = 'tournament'
    AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS tournament;

CREATE DATABASE tournament;

-- Want to connect to tournament database when executing subsequent queries
\c tournament;

CREATE TABLE player (
    id SERIAL PRIMARY KEY,
    name TEXT
);

CREATE TABLE tournament (
    id SERIAL PRIMARY KEY,
    name TEXT
);

-- Ensures players can register for multiple tournaments
CREATE TABLE tournament_register (
    id SERIAL PRIMARY KEY,
    tournament_id INT REFERENCES tournament(id),
    player_id INT REFERENCES player(id)
);

/*
    If tie_flag is true - the match ended in a tie - winner_player_id and loser_player_id do not hold 
    the actual winning and losing player Ids
*/
CREATE TABLE match (
    id SERIAL PRIMARY KEY,
    tournament_id INT REFERENCES tournament(id),
    round_nbr INT NOT NULL,
    match_nbr INT NOT NULL,
    winner_player_id INT REFERENCES player(id),
    loser_player_id INT REFERENCES player(id),
    tie_flag BOOLEAN NOT NULL
);

/*
    Stores tournament rounds' bye players for historical review. Also used to determine the top ranked
    bye player in each tournament round who hasn't yet had a bye during a tournament simulation
*/
CREATE TABLE tournament_round_bye_player (
    id SERIAL primary key,
    tournament_id INT REFERENCES tournament(id),
    round_nbr INT NOT NULL,
    player_rank INT NULL,
    player_id INT REFERENCES player(id)
);

-- Stores tournament rounds' historical standings for review. 
CREATE TABLE historical_standing (
    id SERIAL PRIMARY KEY,
    tournament_id INT REFERENCES tournament(id),
    round_nbr INT NOT NULL,
    player_rank INT NOT NULL,
    actual_player_rank INT NOT NULL,
    player_id INT REFERENCES player(id),
    wins INT NOT NULL,
    losses INT NOT NULL,
    ties INT NOT NULL,
    points NUMERIC NOT NULL,
    opponent_points NUMERIC NOT NULL
);

-- Returns tournament players' information for use in match outputs
CREATE VIEW tournament_player_info AS
SELECT
    tr.tournament_id,
    p.id AS player_id,
    p.name AS player_name
FROM
    tournament_register tr
    INNER JOIN player p ON tr.player_id = p.id;

/*
    Returns tournament players' current records (wins, losses, ties) for use in the current_standings 
    view
*/
CREATE VIEW current_records AS
SELECT
    tr.tournament_id,
    tr.player_id,
    COALESCE(
        (SELECT 
            COUNT(1) 
        FROM 
            match m 
        WHERE 
            m.tournament_id = tr.tournament_id
            AND m.winner_player_id = tr.player_id
            AND m.tie_flag = false)
    , 0) + COALESCE(
        (SELECT 1
            FROM tournament_round_bye_player tb
        WHERE 
            tb.tournament_id = tr.tournament_id
            AND tb.player_id = tr.player_id), 0) AS wins,
    COALESCE(
        (SELECT 
            COUNT(1) 
        FROM 
            match m 
        WHERE 
            m.tournament_id = tr.tournament_id
            AND m.loser_player_id = tr.player_id
            AND m.tie_flag = false),0) AS losses,
    COALESCE(
        (SELECT 
            COUNT(1) 
        FROM 
            match m 
        WHERE 
            m.tournament_id = tr.tournament_id
            AND (m.winner_player_id = tr.player_id
            OR m.loser_player_id = tr.player_id)
            AND m.tie_flag = true),0) AS ties
FROM
    tournament_register tr
ORDER BY
    tr.tournament_id;

/*
    Returns tournament players' current standings. Caculates players' points (wins + ties * 0.5) and 
    opponent match points (wins + ties * 0.5 for each previously played player). player_rank differs
    from actual_player_rank in that player_rank ensures each player always has a predictable unique ranking
    in each tournament round whereas actual_player_rank respresents players' actual rank in each tournament 
    round. The former is used for match combinations. The latter is used for the actual players' standings
*/
CREATE VIEW current_standings AS
SELECT
    a.tournament_id,
    a.tournament_name,
    ROW_NUMBER() OVER (PARTITION BY a.tournament_id ORDER BY a.points DESC, a.opponent_points DESC, a.player_id) AS player_rank,
    RANK() OVER (PARTITION BY a.tournament_id ORDER BY a.points DESC, a.opponent_points DESC) AS actual_player_rank,
    a.player_id,
    a.player_name,
    a.wins,
    a.losses,
    a.ties,
    a.points,
    a.opponent_points
FROM
    (SELECT
        cr.tournament_id,
        t.name AS tournament_name,
        cr.player_id,
        p.name AS player_name,
        cr.wins,
        cr.losses,
        cr.ties,
        (cr.wins + cr.ties * .5) AS points,
        COALESCE(
            (SELECT 
                SUM(cr2.wins + cr2.ties * .5) 
            FROM 
                current_records cr2 
            WHERE 
                cr2.player_id IN
                    (SELECT DISTINCT 
                        m.winner_player_id 
                    FROM 
                        match m 
                    WHERE 
                        m.loser_player_id = cr.player_id
                        AND m.tournament_id = cr.tournament_id
                    UNION 
                    SELECT DISTINCT 
                        m.loser_player_id 
                    FROM 
                        match m 
                    WHERE 
                        m.winner_player_id = cr.player_id
                        AND m.tournament_id = cr.tournament_id)),0.0) AS opponent_points
    FROM
        current_records cr
        INNER JOIN tournament t ON t.id = cr.tournament_id
        INNER JOIN player p ON p.id = cr.player_id) a
ORDER BY
    a.tournament_id,
    player_rank;

-- Returns tournaments' top ranked players who have not yet had a bye round during a tournament simulation
CREATE VIEW tournament_top_player_with_no_bye_round AS
SELECT
    cs.tournament_id,
    cs.player_rank,
    cs.player_id,
    p.name AS player_name
FROM
    current_standings cs
    INNER JOIN player p ON p.id = cs.player_id
WHERE
    NOT EXISTS (SELECT 1 FROM tournament_round_bye_player tb WHERE tb.tournament_id = cs.tournament_id AND tb.player_id = cs.player_id)
ORDER BY 
    cs.tournament_id,
    cs.player_rank;


