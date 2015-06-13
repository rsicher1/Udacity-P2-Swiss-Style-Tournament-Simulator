SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'tournament'
  AND pid <> pg_backend_pid();

drop database tournament;

create database tournament;

\c tournament;

create table player (
  id serial primary key,
  name text
);

create table tournament (
  id serial primary key,
  name text
);

create table tournament_register (
  id serial primary key,
  tournament_id int references tournament(id),
  player_id int references player(id)
);

create table match (
  id serial primary key,
  tournament_id int references tournament(id),
  round_nbr int not null,
  match_nbr int not null,
  winner_player_id int references player(id),
  loser_player_id int references player(id),
  tie_flag boolean not null
);

create table tournament_round_bye_player (
  id serial primary key,
  tournament_id int references tournament(id),
  round_nbr int not null,
  player_rank int null,
  player_id int references player(id)
);

create table historical_standing (
  tournament_id int references tournament(id),
  round_nbr int not null,
  player_rank int not null,
  actual_player_rank int not null,
  player_id int references player(id),
  wins int not null,
  losses int not null,
  ties int not null,
  points numeric not null,
  opponent_points numeric not null
);

create view tournament_player_info as
select
  tr.tournament_id,
  p.id as player_id,
  p.name as player_name
from
  tournament_register tr
  inner join player p on tr.player_id = p.id;

create view current_records as
select
  tr.tournament_id,
  tr.player_id,
  coalesce((select count(*) 
    from match m 
    where m.tournament_id = tr.tournament_id
    and m.winner_player_id = tr.player_id
    and m.tie_flag = false), 0) 
    + coalesce((select 1
    from tournament_round_bye_player tb
    where tb.tournament_id = tr.tournament_id
    and tb.player_id = tr.player_id), 0) as wins,
  coalesce((select count(*) 
    from match m 
    where m.tournament_id = tr.tournament_id
    and m.loser_player_id = tr.player_id
    and m.tie_flag = false),0) as losses,
  coalesce((select count(*) 
    from match m 
    where m.tournament_id = tr.tournament_id
    and (m.winner_player_id = tr.player_id
    or m.loser_player_id = tr.player_id)
    and m.tie_flag = true),0) as ties
from
  tournament_register tr
order by
  tr.tournament_id;

create view current_standings as
select
  a.tournament_id,
  a.tournament_name,
  row_number() over (partition by a.tournament_id order by a.points desc, a.opponent_points desc, a.player_id) as player_rank,
  rank() over (partition by a.tournament_id order by a.points desc, a.opponent_points desc) as actual_player_rank,
  a.player_id,
  a.player_name,
  a.wins,
  a.losses,
  a.ties,
  a.points,
  a.opponent_points
from
  (select
    cr.tournament_id,
    t.name as tournament_name,
    cr.player_id,
    p.name as player_name,
    cr.wins,
    cr.losses,
    cr.ties,
    (cr.wins + (cr.ties * .5)) as points,
    coalesce(
      (select 
          sum(cr2.wins + (cr2.ties * .5)) 
      from 
        current_records cr2 
      where 
        cr2.player_id in 
          (select distinct 
            m.winner_player_id 
          from 
            match m 
          where 
            m.loser_player_id = cr.player_id
            and m.tournament_id = cr.tournament_id
          union 
          select distinct 
            m.loser_player_id 
          from 
            match m 
          where 
            m.winner_player_id = cr.player_id
            and m.tournament_id = cr.tournament_id)),0.0) as opponent_points
  from
    current_records cr
    inner join tournament t on t.id = cr.tournament_id
    inner join player p on p.id = cr.player_id) a
order by
  a.tournament_id,
  player_rank;


create view tournament_top_player_with_no_bye_round as
select
  cs.tournament_id,
  cs.player_rank,
  cs.player_id,
  p.name as player_name
from
  current_standings cs
  inner join player p on p.id = cs.player_id
where
  not exists (select 1 from tournament_round_bye_player tb where tb.tournament_id = cs.tournament_id and tb.player_id = cs.player_id)
order by 
  cs.tournament_id,
  cs.player_rank;


