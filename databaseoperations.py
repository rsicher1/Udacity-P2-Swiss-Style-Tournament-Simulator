#!/usr/bin/env python

import psycopg2

class DatabaseOperations:
  ''' Includes tournament-related postgres database operations '''

  def __init__(self):
    self.connectToDb()

  def connectToDb(self):
    self.db = psycopg2.connect("dbname=tournament")
    self.connection = self.db.cursor()

  def deletePlayers(self):
    self.connection.execute("delete from player")
    self.db.commit()  

  def deleteSpecificPlayers(self, playerIds):
    self.connection.execute("delete from player where player_id in %s", (playerIds,))
    self.db.commit()  

  def deleteTournament(self, tournamentId):
    self.connection.execute("delete from tournament where id = %s", (tournamentId,))
    self.db.commit()

  def deleteAllTournamentMatches(self, tournamentId):
    self.connection.execute("delete from match where tournament_id = %s", (tournamentId,))
    self.db.commit()

  def deleteSpecificTournamentRoundsMatches(self, tournamentId, roundNbrs):
    self.connection.execute("delete from match where tournament_id = %s and round_nbr in %s", (tournamentId, roundNbrs))
    self.db.commit()

  def deleteTournamentSpecificRoundMatches(self, tournamentId, roundNbr, matchNbrs):
    self.connection.execute("delete from match where tournament_id = %s and round_nbr = %s and match_nbr in %s", (tournamentId, roundNbr, matchNbrs))
    self.db.commit()

  def deleteAllTournamentRoundsByePlayers(self, tournamentId):
    self.connection.execute("delete from tournament_round_bye_player where tournament_id = %s", (tournamentId,))
    self.db.commit()

  def deleteSpecficTournamentRoundsByePlayers(self, tournamentId, roundNbrs):
    self.connection.execute("delete from tournament_round_bye_player where tournament_id = %s and round_nbr in %s", (tournamentId, roundNbrs))
    self.db.commit()

  def deleteAllTournamentRoundsHistoricalStandings(self, tournamentId):
    self.connection.execute("delete from historical_standing where tournament_id = %s", (tournamentId,))
    self.db.commit()

  def deleteSpecficTournamentRoundsHistoricalStandings(self, tournamentId, roundNbrs):
    self.connection.execute("delete from historical_standing where tournament_id = %s and round_nbr in %s", (tournamentId, roundNbrs))
    self.db.commit()

  def deleteFullTournamentRegister(self, tournamentId):
    self.connection.execute("delete from tournament_register where tournament_id = %s", (tournamentId,))
    self.db.commit()

  def deleteSpecificTournamentRegisteredPlayers(self, playerIds):
    self.connection.execute("delete from tournament_register where tournament_id = %s and player_id in %s", (tournamentId, playerIds))
    self.db.commit()

  def registerTournament(self, tournamentName):
    self.connection.execute("insert into tournament (name) values (%s) returning id", (tournamentName,))
    self.db.commit()
    return self.connection.fetchone()[0]

  def registerPlayer(self, playerName):
    self.connection.execute("insert into player (name) values (%s) returning id", (playerName,))
    self.db.commit()
    return self.connection.fetchone()[0]

  def registerTournamentPlayer(self, tournamentId, playerId, seedNbr):
    self.connection.execute("insert into tournament_register (tournament_id, player_id) values (%s, %s)", (tournamentId, playerId))
    self.db.commit()

  def registerTournamentHistoricalStandings(self, tournamentId, roundNbr):
    self.connection.execute('''
      insert into historical_standing
      select
        tournament_id,
        %s as round_nbr,
        player_rank,
        actual_player_rank,
        player_id,
        wins,
        losses,
        ties,
        points,
        opponent_points
      from
        current_standings
      where
        tournament_id = %s
      ''', (roundNbr, tournamentId))
    self.db.commit()

  def tournamentInfo(self, tournamentId):
    self.connection.execute('''
      select
        id,
        name
      from
        tournament
      where 
        id = %s
      ''', (tournamentId,))
    return self.connection.fetchone()

  def tournamentPlayerInfo(self, tournamentId):
    self.connection.execute('''
      select
        player_id,
        player_name
      from 
        tournament_player_info
      where 
        tournament_id = %s
      ''', (tournamentId,))
    return self.connection.fetchall()

  def tournamentPreviousRoundPlayerMatches(self, tournamentId):
    self.connection.execute('''
      select 
        winner_player_id,
        loser_player_id
      from 
        match
      where 
        tournament_id = %s
      ''', (tournamentId,))
    return self.connection.fetchall()

  def tournamentTotalPlayerCount(self, tournamentId):
    self.connection.execute('''
      select 
        coalesce((
          select 
            count(*) 
          from 
            tournament_register 
          where 
            tournament_id = %s)
        ,0)
      ''', (tournamentId,))
    return self.connection.fetchone()[0]

  def tournamentTotalRoundCount(self, tournamentId):
    self.connection.execute('''
      select 
        ceil(count(*) * 0.5) 
      from 
        tournament_register 
      where 
        tournament_id = %s
      ''', (tournamentId,))
    return self.connection.fetchone()[0]

  def tournamentCurrentStandings(self, tournamentId):
    self.connection.execute('''
      select
        player_rank,
        actual_player_rank,
        player_id,
        player_name,
        wins,
        losses,
        ties,
        points,
        opponent_points
      from
        current_standings
      where
        tournament_id = %s
      order by 
        player_rank
      ''', (tournamentId,))
    return self.connection.fetchall()

  def registerTournamentMatchResult(self, tournamentId, roundNbr, matchNbr, winnerPlayerId, loserPlayerId, tieFlag=False):
    self.connection.execute("insert into match (tournament_id, round_nbr, match_nbr, winner_player_id, loser_player_id, tie_flag) values (%s, %s, %s, %s, %s, %s)", (tournamentId, roundNbr, matchNbr, winnerPlayerId, loserPlayerId, tieFlag))
    self.db.commit()

  def tournamentRoundMatchResults(self, tournamentId, roundNbr):
    self.connection.execute('''
      select
        match_nbr,
        winner_player_id,
        winner_player_name,
        loser_player_id,
        loser_player_name,
        tie_flag
      from
        match_results
      where
        tournament_id = %s
        and round_nbr = %s
      ''',(tournamentId, roundNbr))
    return self.connection.fetchall()

  def registerTournamentRoundByePlayer(self, tournamentId, roundNbr, playerRank, playerId):
    self.connection.execute("insert into tournament_round_bye_player (tournament_id, round_nbr, player_rank, player_id) values (%s, %s, %s, %s)", (tournamentId, roundNbr, playerRank, playerId))
    self.db.commit()

  def tournamentTopPlayerWithNoByeRound(self, tournamentId):
    self.connection.execute('''
      select
        player_rank,
        player_id,
        player_name
      from
        tournament_top_player_with_no_bye_round
      where
        tournament_id = %s
      ''',(tournamentId,))
    return self.connection.fetchone()

  def closeDbConnection(self):
    if not self.connection is None and not self.connection.closed:
      self.connection.close()
