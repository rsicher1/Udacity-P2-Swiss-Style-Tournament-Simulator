#!/usr/bin/env python

import psycopg2


class DatabaseOperations:
    ''' Includes tournament related PostgreSQL database operations '''

    def __init__(self):
        self.connectToDb()

    def connectToDb(self):
        try:
            self.db = psycopg2.connect("dbname=tournament")
            self.connection = self.db.cursor()
        except psycopg2.Error as e:
            print e

    def deletePlayers(self):
        query = "DELETE FROM player"
        self.connection.execute(query)
        self.db.commit()

    def deleteSpecificPlayers(self, playerIds):
        query = "DELETE FROM player WHERE id IN %s"
        parameter = (playerIds,)
        self.connection.execute(query, parameter)
        self.db.commit()

    def deleteTournament(self, tournamentId):
        query = "DELETE FROM tournament WHERE id = %s"
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        self.db.commit()

    def deleteAllTournamentMatches(self, tournamentId):
        query = "DELETE FROM match WHERE tournament_id = %s"
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        self.db.commit()

    def deleteSpecificTournamentRoundsMatches(self, tournamentId, roundNbrs):
        query = "DELETE FROM match WHERE tournament_id = %s AND round_nbr IN %s"
        parameters = (tournamentId, roundNbrs)
        self.connection.execute(query, parameters)
        self.db.commit()

    def deleteTournamentSpecificRoundMatches(self, tournamentId, roundNbr, matchNbrs):
        query = "DELETE FROM match WHERE tournament_id = %s AND round_nbr = %s AND match_nbr IN %s"
        parameters = (tournamentId, roundNbr, matchNbrs)
        self.connection.execute(query, parameters)
        self.db.commit()

    def deleteAllTournamentRoundsByePlayers(self, tournamentId):
        query = "DELETE FROM tournament_round_bye_player WHERE tournament_id = %s"
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        self.db.commit()

    def deleteSpecficTournamentRoundsByePlayers(self, tournamentId, roundNbrs):
        query = "DELETE FROM tournament_round_bye_player WHERE tournament_id = %s AND round_nbr IN %s"
        parameters = (tournamentId, roundNbrs)
        self.connection.execute(query, parameters)
        self.db.commit()

    def deleteAllTournamentRoundsHistoricalStandings(self, tournamentId):
        query = "DELETE FROM historical_standing WHERE tournament_id = %s"
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        self.db.commit()

    def deleteSpecficTournamentRoundsHistoricalStandings(self, tournamentId, roundNbrs):
        query = "DELETE FROM historical_standing WHERE tournament_id = %s AND round_nbr IN %s"
        parameters = (tournamentId, roundNbrs)
        self.connection.execute(query, parameters)
        self.db.commit()

    def deleteFullTournamentRegister(self, tournamentId):
        query = "DELETE FROM tournament_register WHERE tournament_id = %s"
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        self.db.commit()

    def deleteSpecificTournamentRegisteredPlayers(self, tournamentId, playerIds):
        query = "DELETE FROM tournament_register WHERE tournament_id = %s AND player_id IN %s"
        parameters = (tournamentId, playerIds)
        self.connection.execute(query, parameters)
        self.db.commit()

    def registerTournament(self, tournamentName):
        query = "INSERT INTO tournament (name) VALUES (%s) RETURNING id"
        parameter = (tournamentName,)
        self.connection.execute(query, parameter)
        self.db.commit()
        return self.connection.fetchone()[0]

    def registerPlayer(self, playerName):
        query = "INSERT INTO player (name) VALUES (%s) RETURNING id"
        parameter = (playerName,)
        self.connection.execute(query, parameter)
        self.db.commit()
        return self.connection.fetchone()[0]

    def registerTournamentPlayer(self, tournamentId, playerId):
        query = "INSERT INTO tournament_register (tournament_id, player_id) VALUES (%s, %s)"
        parameters = (tournamentId, playerId)
        self.connection.execute(query, parameters)
        self.db.commit()

    def registerTournamentHistoricalStandings(self, tournamentId, roundNbr):
        query = '''
            INSERT INTO historical_standing(tournament_id, round_nbr, player_rank, actual_player_rank, player_id,
                wins, losses, ties, points, opponent_points)
            SELECT
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
            FROM
                current_standings
            WHERE
                tournament_id = %s
            '''
        parameters = (roundNbr, tournamentId)
        self.connection.execute(query, parameters)
        self.db.commit()

    def tournamentInfo(self, tournamentId):
        query = '''
            SELECT
                id,
                name
            FROM
                tournament
            WHERE
                id = %s
            '''
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        return self.connection.fetchone()

    def tournamentPlayerInfo(self, tournamentId):
        query = '''
            SELECT
                player_id,
                player_name
            FROM
                tournament_player_info
            WHERE
                tournament_id = %s
            '''
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        return self.connection.fetchall()

    def tournamentPreviousRoundPlayerMatches(self, tournamentId):
        query = '''
            SELECT
                winner_player_id,
                loser_player_id
            FROM
                match
            WHERE
                tournament_id = %s
            '''
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        return self.connection.fetchall()

    def tournamentTotalPlayerCount(self, tournamentId):
        query = '''
            SELECT
                coalesce((
                    SELECT
                        count(*)
                    FROM
                        tournament_register
                    WHERE
                        tournament_id = %s)
                ,0)
            '''
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        return self.connection.fetchone()[0]

    def tournamentTotalRoundCount(self, tournamentId):
        query = '''
            SELECT
                ceil(count(*) * 0.5)
            FROM
                tournament_register
            WHERE
                tournament_id = %s
            '''
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        return self.connection.fetchone()[0]

    def tournamentCurrentStandings(self, tournamentId):
        query = '''
            SELECT
                player_rank,
                actual_player_rank,
                player_id,
                player_name,
                wins,
                losses,
                ties,
                points,
                opponent_points
            FROM
                current_standings
            WHERE
                tournament_id = %s
            ORDER BY
                player_rank
            '''
        parameter = (tournamentId,)
        self.connection.execute(query, parameter)
        return self.connection.fetchall()

    def registerTournamentMatchResult(self, tournamentId, roundNbr, matchNbr, winnerPlayerId, loserPlayerId, tieFlag=False):
        query = "INSERT INTO match (tournament_id, round_nbr, match_nbr, winner_player_id, loser_player_id, tie_flag) VALUES (%s, %s, %s, %s, %s, %s)"
        parameters = (tournamentId, roundNbr, matchNbr, winnerPlayerId, loserPlayerId, tieFlag)
        self.connection.execute(query, parameters)
        self.db.commit()

    def tournamentRoundMatchResults(self, tournamentId, roundNbr):
        query = '''
            SELECT
                match_nbr,
                winner_player_id,
                winner_player_name,
                loser_player_id,
                loser_player_name,
                tie_flag
            FROM
                match_results
            WHERE
                tournament_id = %s
                AND round_nbr = %s
            '''
        parameters = (tournamentId, roundNbr)
        self.connection.execute(query, parameters)
        return self.connection.fetchall()

    def registerTournamentRoundByePlayer(self, tournamentId, roundNbr, playerRank, playerId):
        query = "INSERT INTO tournament_round_bye_player (tournament_id, round_nbr, player_rank, player_id) VALUES (%s, %s, %s, %s)"
        parameters = (tournamentId, roundNbr, playerRank, playerId)
        self.connection.execute(query, parameters)
        self.db.commit()

    def tournamentTopPlayerWithNoByeRound(self, tournamentId):
        query = '''
            SELECT
                player_rank,
                player_id,
                player_name
            FROM
                tournament_top_player_with_no_bye_round
            WHERE
                tournament_id = %s
            '''
        parameter = (tournamentId, )
        self.connection.execute(query, parameter)
        return self.connection.fetchone()

    def closeDbConnection(self):
        if self.connection is not None and not self.connection.closed:
            try:
                self.connection.close()
            except psycopg2.Error as e:
                print e
