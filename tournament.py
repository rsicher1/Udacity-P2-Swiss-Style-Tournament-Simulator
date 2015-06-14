#!/usr/bin/env python

import math
import random

import round

class Tournament:
  ''' Includes tournament related data and operations '''

  def __init__(self, name, dbo, qualifiedPlaces = 3):
    self.name = name
    self.dbo = dbo
    self.id = self.registerInDb()
    self.rounds = []
    self.previousRoundsPlayedMatches = []
    self.qualifiedPlaces = qualifiedPlaces

    self.started = False
    self.currentRoundNbr = None
    self.players = []
    self.totalPlayerCount = 0
    self.totalPlayerCountOdd = False
    self.possiblePlayerMatchCombinations = None
    self.totalRoundCount = 0

  def registerInDb(self):
    return self.dbo.registerTournament(self.name)

  def registerPlayer(self, playerId):
    self.registerPlayerInDb(playerId)
    self.players = self.getTournamentPlayerInfoFromDb()
    self.totalPlayerCount = self.calculateTotalPlayerCount()

  def registerPlayerInDb(self, playerId):
    self.dbo.registerTournamentPlayer(self.id, playerId)

  def simulate(self):
    self.started = True
    self.players = self.getTournamentPlayerInfoFromDb()
    self.totalPlayerCount = self.calculateTotalPlayerCount()
    self.totalPlayerCountOdd = self.determineTotalPlayerCountOdd()
    self.possiblePlayerMatchCombinations = self.determineInitialPossiblePlayerMatchCombinations()
    self.totalRoundCount = self.calculateTotalRoundCount()

    self.outputName()
    self.simulateRounds()
    self.closeDbConnection()

  def getTournamentPlayerInfoFromDb(self):
    return self.dbo.tournamentPlayerInfo(self.id)

  def calculateTotalPlayerCount(self):
    return len(self.players)

  def determineTotalPlayerCountOdd(self):
    return self.totalPlayerCount % 2 != 0

  def determineInitialPossiblePlayerMatchCombinations(self):
    playerIds = [player[0] for player in self.players]
    if self.totalPlayerCountOdd:
      return self.determineInitialPossiblePlayerMatchCombinationsWithOddNumberOfPlayers(playerIds)
    else:
      return list(self.generatePossiblePlayerMatchCombinations(playerIds))

  # Need to add extra dummy player id (None) to playerIds list in order for generatePossiblePlayerMatchCombinations
  # to work correctly. Combinations with None playerId are filtered out after running.
  def determineInitialPossiblePlayerMatchCombinationsWithOddNumberOfPlayers(self, playerIds):
    playerIds.append(None)
    possiblePlayerMatchCombinationsOdd = list(self.generatePossiblePlayerMatchCombinations(playerIds))

    return [[match for match in possiblePlayerMatchCombinationOdd if not any(matchPlayer == None for matchPlayer in match)] for possiblePlayerMatchCombinationOdd in possiblePlayerMatchCombinationsOdd]

  # recursive function which determines all possible combinations of pairings for a list of playerIds
  def generatePossiblePlayerMatchCombinations(self, playerIds):
    if len(playerIds) <= 1:
      yield playerIds
      return

    firstPlayerId = playerIds[0]
    for i in range(1, len(playerIds)):
      playerMatch = (firstPlayerId, playerIds[i])
      for remainingPlayerMatchCombinations in self.generatePossiblePlayerMatchCombinations(playerIds[1:i] + playerIds[i+1:]):
        yield [playerMatch] + remainingPlayerMatchCombinations

  def calculateTotalRoundCount(self):
      return int(math.ceil((self.totalPlayerCount + 7.0 * self.qualifiedPlaces)/5.0))

  def simulateRounds(self):
    self.currentRoundNbr = 1
    while self.currentRoundNbr <= self.totalRoundCount:
      self.simulateRound()
      self.currentStandings = self.getCurrentStandingsFromDb()
      self.registerHistoricalStandingsInDb()

      self.outputCurrentStandings()
      self.currentRoundNbr += 1

  def simulateRound(self):
    rnd = round.Round(self.dbo, self.id, self.currentRoundNbr)
    if self.currentRoundFirstRound():
      self.simulateFirstRound(rnd)
    else:
      self.simulateSecondOrGreaterRound(rnd)
    rnd.simulateMatches(self.players, self.previousRoundsPlayedMatches)
    self.addRoundToTournament(rnd)
    rnd.outputRound(self.totalRoundCount, self.totalPlayerCountOdd)

  # chooses a random bye player (if there are an odd number of players) and random combination of player  
  # matches for the round
  def simulateFirstRound(self, rnd):
    if self.totalPlayerCountOdd:
      randomPlayer = self.chooseRandomTournamentPlayer()
      randomPlayerDetail = (None, randomPlayer[0], randomPlayer[1])
      rnd.setRoundByePlayer(randomPlayerDetail)
      rnd.registerRoundByePlayerInDb()
    rnd.setInitialRoundPossiblePlayerMatchCombinations(self.possiblePlayerMatchCombinations)
    if self.totalPlayerCountOdd:
      rnd.filterOutRoundPossiblePlayerMatchCombinationsWithRoundByePlayer()
    randomRoundPossiblePlayerMatchCombination = rnd.chooseRandomRoundPossiblePlayerMatchCombination()
    rnd.setPlayerMatchCombination(randomRoundPossiblePlayerMatchCombination)

  def currentRoundFirstRound(self):
    return self.currentRoundNbr == 1

  def chooseRandomTournamentPlayer(self):
    return random.choice(self.players)

  def outputName(self):
    print "{0}".format(self.name)

  def closeDbConnection(self):
    self.dbo.closeDbConnection()

  # chooses the tournament top bye player with no bye round (if there are an odd number of players) and 
  # the player match combination which minimize the difference between rankings and does not include any
  # previously played matches
  def simulateSecondOrGreaterRound(self, rnd):
    if self.totalPlayerCountOdd:
      topPlayerWithNoByeRound = self.getTopPlayerWithNoByeRoundFromDb()
      rnd.setRoundByePlayer(topPlayerWithNoByeRound)
      rnd.registerRoundByePlayerInDb()
    rnd.setTournamentPreviousRoundsPlayedMatches(self.previousRoundsPlayedMatches)
    self.filterOutPossiblePlayerMatchCombinationsWithPreviousRoundsPlayedMatches()
    rnd.setInitialRoundPossiblePlayerMatchCombinations(self.possiblePlayerMatchCombinations)
    if self.totalPlayerCountOdd:
      rnd.filterOutRoundPossiblePlayerMatchCombinationsWithRoundByePlayer()
    rnd.setTournamentPreviousRoundStandings(self.currentStandings)
    rnd.determineRoundPossiblePlayerMatchCombinationQuality()
    bestRoundPossiblePlayerMatchCombination = rnd.determineBestRoundPossiblePlayerMatchCombination()
    sortedBestRoundPossiblePlayerMatchCombination = rnd.sortBestRoundPlayerMatchCombinationByTournamentCurrentPlayerRanks(bestRoundPossiblePlayerMatchCombination)
    rnd.setPlayerMatchCombination(sortedBestRoundPossiblePlayerMatchCombination)

  def getTopPlayerWithNoByeRoundFromDb(self):
    return self.dbo.tournamentTopPlayerWithNoByeRound(self.id)

  def filterOutPossiblePlayerMatchCombinationsWithPreviousRoundsPlayedMatches(self):
    self.possiblePlayerMatchCombinations = [possiblePlayerMatchCombination for possiblePlayerMatchCombination in self.possiblePlayerMatchCombinations if not any((match[0] == previousRoundsPlayedMatch[0] or match[1] == previousRoundsPlayedMatch[0]) and (match[0] == previousRoundsPlayedMatch[1] or match[1] == previousRoundsPlayedMatch[1]) for previousRoundsPlayedMatch in self.previousRoundsPlayedMatches for match in possiblePlayerMatchCombination)]

  def addRoundToTournament(self, rnd):
    self.rounds.append(rnd)

  def getCurrentStandingsFromDb(self):
    return self.dbo.tournamentCurrentStandings(self.id)

  def registerHistoricalStandingsInDb(self):
    self.dbo.registerTournamentHistoricalStandings(self.id, self.currentRoundNbr)

  def outputCurrentStandings(self):
    self.outputCurrentStandingsHeader()
    self.outputCurrentStandingsDetail()

  def outputCurrentStandingsHeader(self):
    print "\nRank\tPID\tName\tW\tL\tT\tPoints\tOMP"

  def outputCurrentStandingsDetail(self):
    for standing in self.currentStandings:
      standingOutput = ""
      for standingField in standing[1:]:
        standingOutput += str(standingField) + "\t"
      print standingOutput

  def deleteRegisteredPlayers(self, playerIds = None):
    if playerIds == None:
      self.deleteFullTournamentRegisterFromDb()
    else:
      self.deleteSpecificRegisteredPlayerFromDb(playerIds)
    self.players = self.getTournamentPlayerInfoFromDb()
    self.totalPlayerCount = self.calculateTotalPlayerCount()

  def deleteFullTournamentRegisterFromDb(self):
    self.dbo.deleteFullTournamentRegister(self.id)

  def deleteSpecificRegisteredPlayersFromDb(self, playerIds):
    self.dbo.deleteSpecificTournamentRegisteredPlayers(self.id,playerIds)

  def deleteTournament(self):
    self.deleteRounds()
    self.deleteFullTournamentFromDb()  
    self = None

  def deleteRounds(self, roundNbrs = None):
    for rnd in self.rounds:
      if roundNbrs is None or rnd.nbr in roundNbrs:
        rnd.deleteMatches()
        self.rounds.remove(rnd)
        
    if not roundNbrs is None:
      self.deleteSpecificRoundsFromDb(roundNbrs)

  def deleteSpecificRoundsFromDb(self, roundNbrs):
    self.deleteSpecificRoundsMatchesFromDb(roundNbrs)
    self.deleteSpecificRoundsByePlayersFromDb(roundNbrs)
    self.deleteSpecificRoundsHistoricalStandingsFromDb(roundNbrs)

  def deleteSpecificRoundsMatchesFromDb(self, roundNbrs):
    self.dbo.deleteSpecificTournamentRoundsMatches(self.id, roundNbrs)

  def deleteSpecificRoundsByePlayersFromDb(self, roundNbrs):
    self.dbo.deleteSpecificTournamentRoundsByePlayers(self.id, roundNbrs)

  def deleteSpecificRoundsHistoricalStandingsFromDb(self, roundNbrs):
    self.dbo.deleteSpecificTournamentRoundsHistoricalStandings(self.id, roundNbrs)

  def deleteMatches(self, roundNbr, matchNbrs):
    for rnd in self.rounds:
      if rnd.nbr == roundNbr:
        rnd.deleteMatches(matchNbrs)
        break

  def deleteFullTournamentFromDb(self):
    self.deleteAllMatchesFromDb()
    self.deleteAllRoundsByePlayersFromDb()
    self.deleteAllRoundsHistoricalStandingsFromDb()
    self.deleteFullRegisterFromDb()
    self.deleteTournamentFromDb()

  def deleteAllMatchesFromDb(self):
    self.dbo.deleteAllTournamentMatches(self.id)

  def deleteAllRoundsByePlayersFromDb(self):
    self.dbo.deleteAllTournamentRoundsByePlayers(self.id)

  def deleteAllRoundsHistoricalStandingsFromDb(self):
    self.dbo.deleteAllTournamentRoundsHistoricalStandings(self.id)

  def deleteFullRegisterFromDb(self):
    self.dbo.deleteFullTournamentRegister(self.id)

  def deleteTournamentFromDb(self):
    self.dbo.deleteTournament(self.id)

  def deleteSpecificRegisteredPlayers(self, playerIds):
    self.dbo.deleteSpecificTournamentRegisteredPlayers(playerIds)

