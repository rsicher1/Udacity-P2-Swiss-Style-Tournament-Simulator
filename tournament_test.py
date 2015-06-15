#!/usr/bin/env python
#
# Test cases for tournament.py

import databaseoperations
import tournament
import round


def testDeleteTournamentFromDb():
    dbo = databaseoperations.DatabaseOperations()
    t = tournament.Tournament("The Greatest And Best Tournament In The World... Tribute", dbo)
    tournamentInfo = dbo.tournamentInfo(t.id)
    if not tournamentInfo:
        raise ValueError("After registering a tournament, information about the tournament cannot be retrieved from the database")
    t.deleteTournament()
    tournamentInfo = dbo.tournamentInfo(t.id)
    if tournamentInfo:
        raise ValueError("After deleting the tournament, information about the tournament can still be retrieved from the database")
    print "1. After registering a tournament, it can be deleted from the database"
    dbo.closeDbConnection()


def testTournamentTotalPlayerCount():
    dbo = databaseoperations.DatabaseOperations()
    t = tournament.Tournament("The Greatest And Best Tournament In The World... Tribute", dbo)
    t.calculateTotalPlayerCount()
    if isinstance(t.totalPlayerCount, basestring):
        raise TypeError("After registering a tournament, totalPlayerCount should be a numeric value, not a string")
    if t.totalPlayerCount != 0:
        raise ValueError("After registering a tournament, totalPlayerCount should be 0")
    print "2. After registering a tournament, totalPlayerCount is 0"
    t.deleteTournament()
    dbo.closeDbConnection()


def testTournamentRegisterPlayer():
    dbo = databaseoperations.DatabaseOperations()
    t = tournament.Tournament("The Greatest And Best Tournament In The World... Tribute", dbo)
    playerId = dbo.registerPlayer("Markov Chaney")
    t.registerPlayer(playerId)
    if t.totalPlayerCount != 1:
        raise ValueError("After registering a tournament and a player, totalPlayerCount should be 1")
    print "3. After registering a tournament and a player, totalPlayerCount is 1"
    t.deleteTournament()
    dbo.deleteSpecificPlayers((playerId,))
    dbo.closeDbConnection()


def testTournamentRegisterAndDeletePlayers():
    dbo = databaseoperations.DatabaseOperations()
    t = tournament.Tournament("The Greatest And Best Tournament In The World... Tribute", dbo)
    player1Id = dbo.registerPlayer("Markov Chaney")
    t.registerPlayer(player1Id)
    player2Id = dbo.registerPlayer("John Malik")
    t.registerPlayer(player2Id)
    player3Id = dbo.registerPlayer("Mao Tsu-hsi")
    t.registerPlayer(player3Id)
    player4Id = dbo.registerPlayer("Atlanta Hope")
    t.registerPlayer(player4Id)
    t.calculateTotalPlayerCount()
    if t.totalPlayerCount != 4:
        raise ValueError("After registering a tournament and four players, totalPlayerCount should be 4")
    t.deleteRegisteredPlayers()
    if t.totalPlayerCount != 0:
            raise ValueError("After deleting all tournament players, totalPlayerCount should be 0")
    print "4. Tournament players can be registered and deleted"
    t.deleteTournament()
    dbo.deleteSpecificPlayers((player1Id, player2Id, player3Id, player4Id))
    dbo.closeDbConnection()


def testTournamentStandingsBeforeFirstRound():
    dbo = databaseoperations.DatabaseOperations()
    t = tournament.Tournament("The Greatest And Best Tournament In The World... Tribute", dbo)
    player1Id = dbo.registerPlayer("Melpomene Murray")
    t.registerPlayer(player1Id)
    player2Id = dbo.registerPlayer("Randy Schwartz")
    t.registerPlayer(player2Id)
    currentStandings = t.getCurrentStandingsFromDb()
    if len(currentStandings) < 2:
        raise ValueError("Players should appear in tournament standings even before they have played any matches")
    elif len(currentStandings) > 2:
        raise ValueError("Only players registered for tournament should appear in the standings")
    if len(currentStandings[0]) != 9:
        raise ValueError("Each currentStandings row should have nine columns")

    [(rank1, arank1, id1, name1, wins1, losses1, ties1, points1, omp1), (rank2, arank2, id2, name2, wins2, losses2, ties2, points2, omp2)] = currentStandings
    if wins1 != 0 or losses1 != 0 or ties1 != 0 or wins2 != 0 or losses2 != 0 or ties2 != 0:
        raise ValueError("Newly registered players should have 0 wins, losses, or ties")
    if set([name1, name2]) != set(["Randy Schwartz", "Melpomene Murray"]):
        raise ValueError("Registered tournament players' names should appear in standings even if they have not played any matches")
    print "5. Newly registered tournament players appear in standings even if they have not played any matches"
    t.deleteTournament()
    dbo.deleteSpecificPlayers((player1Id, player2Id))
    dbo.closeDbConnection()


def testTournamentStandingsAfterOneRound():
    dbo = databaseoperations.DatabaseOperations()
    t = tournament.Tournament("The Greatest And Best Tournament In The World... Tribute", dbo)
    player1Id = dbo.registerPlayer("Bruno Walton")
    t.registerPlayer(player1Id)
    player2Id = dbo.registerPlayer("Boots O'Neal")
    t.registerPlayer(player2Id)
    player3Id = dbo.registerPlayer("Cathy Burton")
    t.registerPlayer(player3Id)
    player4Id = dbo.registerPlayer("Diane Grant")
    t.registerPlayer(player4Id)

    t.players = t.getTournamentPlayerInfoFromDb()
    t.totalPlayerCount = t.calculateTotalPlayerCount()
    t.totalPlayerCountOdd = t.determineTotalPlayerCountOdd()
    t.possiblePlayerMatchCombinations = t.determineInitialPossiblePlayerMatchCombinations()
    t.totalRoundCount = t.calculateTotalRoundCount()

    t.currentRoundNbr = 1
    rnd = round.Round(t.dbo, t.id, t.currentRoundNbr)

    t.simulateFirstRound(rnd)

    rnd.simulateMatches(t.players, t.previousRoundsPlayedMatches)
    t.addRoundToTournament(rnd)

    currentStandings = t.getCurrentStandingsFromDb()

    total_wins = 0
    total_ties = 0
    total_losses = 0
    for (player_rank, actual_player_rank, player_id, player_name, wins, losses, ties, points, omp) in currentStandings:
        if (wins + losses + ties) != 1:
            raise ValueError("Each player should have 1 win, loss, or tie recorded after one tournament round")
        if wins == 1 and (losses >= 1 or ties >= 1):
            raise ValueError("Each match winner should have 1 win and 0 losses and ties recorded after one tournament round")
        elif losses == 1 and (wins >= 1 or ties >= 1):
            raise ValueError("Each match loser should have 1 loss and 0 wins and ties recorded after one tournament round")
        elif ties == 1 and (wins >= 1 or losses >= 1):
            raise ValueError("Each player who tied in a match should have 1 tie and 0 wins and losses recorded after one tournament round")

        total_wins += wins
        total_losses += losses
        total_ties += ties

    if total_wins > 2:
        raise ValueError("Total player wins should not exceed 2 after one tournament round")
    if total_losses > 2:
        raise ValueError("Total player losses should not exceed 2 after one tournament round")
    if total_wins == 1 and total_losses == 1 and total_ties != 2:
        raise ValueError("Total player ties should be 2 after one tournament round if only two players tied")
    if total_wins == 0 and total_losses == 0 and total_ties != 4:
        raise ValueError("Total player ties should be 4 after one tournament round if only all players tied")

    print "6. After one tournament round, the tournament standings are correct"
    t.deleteTournament()
    dbo.deleteSpecificPlayers((player1Id, player2Id, player3Id, player4Id))
    dbo.closeDbConnection()


def testBestPlayerMatchCombinationAfterOneRound():
    dbo = databaseoperations.DatabaseOperations()
    t = tournament.Tournament("The Greatest And Best Tournament In The World... Tribute", dbo)
    player1Id = dbo.registerPlayer("John Conner")
    t.registerPlayer(player1Id)
    player2Id = dbo.registerPlayer("Patrick Bateman")
    t.registerPlayer(player2Id)
    player3Id = dbo.registerPlayer("Don Draper")
    t.registerPlayer(player3Id)
    player4Id = dbo.registerPlayer("Louis CK")
    t.registerPlayer(player4Id)

    t.players = t.getTournamentPlayerInfoFromDb()
    t.totalPlayerCount = t.calculateTotalPlayerCount()
    t.totalPlayerCountOdd = t.determineTotalPlayerCountOdd()
    t.possiblePlayerMatchCombinations = t.determineInitialPossiblePlayerMatchCombinations()
    t.totalRoundCount = t.calculateTotalRoundCount()

    t.currentRoundNbr = 1
    rndOne = round.Round(t.dbo, t.id, t.currentRoundNbr)

    t.simulateFirstRound(rndOne)

    rndOne.simulateMatches(t.players, t.previousRoundsPlayedMatches)
    t.addRoundToTournament(rndOne)

    t.currentStandings = t.getCurrentStandingsFromDb()

    rndOneStandings = t.currentStandings

    rndOneRank1PlayerId = rndOneStandings[0][2]
    rndOneRank2PlayerId = rndOneStandings[1][2]
    rndOneRank3PlayerId = rndOneStandings[2][2]
    rndOneRank4PlayerId = rndOneStandings[3][2]

    t.currentRoundNbr += 1

    rndTwo = round.Round(t.dbo, t.id, t.currentRoundNbr)
    t.simulateSecondOrGreaterRound(rndTwo)

    rndTwoTournamentPreviousRoundsPlayedMatches = rndTwo.tournamentPreviousRoundsPlayedMatches

    rndTwoPlayerMatchCombination = rndTwo.playerMatchCombination

    [(rndTwoMatch1player1Id, rndTwoMatch1player2Id), (rndTwoMatch2player1Id, rndTwoMatch2player2Id)] = rndTwoPlayerMatchCombination[:2]

    defaultRndTwoMatches = [set((rndOneRank1PlayerId, rndOneRank2PlayerId)), set((rndOneRank3PlayerId, rndOneRank4PlayerId))]

    if any(set(rndTwoTournamentPreviousRoundsPlayedMatch) in defaultRndTwoMatches for rndTwoTournamentPreviousRoundsPlayedMatch in rndTwoTournamentPreviousRoundsPlayedMatches):
        if rndTwoMatch1player1Id != rndOneRank1PlayerId or rndTwoMatch1player2Id != rndOneRank3PlayerId or rndTwoMatch2player1Id != rndOneRank2PlayerId or rndTwoMatch2player2Id != rndOneRank4PlayerId:
            raise ValueError("If the first place player played the second place player in round one, in round two, the first place player should play the third place player, and the second place player should play the fourth place player")
    else:
        if rndTwoMatch1player1Id != rndOneRank1PlayerId or rndTwoMatch1player2Id != rndOneRank2PlayerId or rndTwoMatch2player1Id != rndOneRank3PlayerId or rndTwoMatch2player2Id != rndOneRank4PlayerId:
            raise ValueError("If the first place player did not play the second place player in round one, in round two, the first place player should play the second place player, and the third place player should play the fourth place player")

    print "7. The match combinations for round two are correct"
    t.deleteTournament()
    dbo.deleteSpecificPlayers((player1Id, player2Id, player3Id, player4Id))
    dbo.closeDbConnection()

if __name__ == '__main__':
    testDeleteTournamentFromDb()
    testTournamentTotalPlayerCount()
    testTournamentRegisterPlayer()
    testTournamentRegisterAndDeletePlayers()
    testTournamentStandingsBeforeFirstRound()
    testTournamentStandingsAfterOneRound()
    testBestPlayerMatchCombinationAfterOneRound()

    print "Success! All tests pass!"
