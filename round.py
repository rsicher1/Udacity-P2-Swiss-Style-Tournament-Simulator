#!/usr/bin/env python

import math
import random
import copy

import match

class Round:

  def __init__(self, dbo, tournamentId, roundNbr):
    self.dbo = dbo
    self.tournamentId = tournamentId
    self.nbr = roundNbr
    self.matches = []

    self.roundByePlayerRank = None
    self.roundByePlayerId = None
    self.roundByePlayerName = None

    self.roundPossiblePlayerMatchCombinations = None
    self.tournamentPreviousRoundsPlayedMatches = None
    self.tournamentPreviousRoundStandings = None
    self.playerMatchCombination = None

  def setRoundByePlayer(self, roundByePlayer):
    self.roundByePlayerRank = roundByePlayer[0]
    self.roundByePlayerId = roundByePlayer[1]
    self.roundByePlayerName = roundByePlayer[2]

  def registerRoundByePlayerInDb(self):
    self.dbo.registerTournamentRoundByePlayer(self.tournamentId, self.nbr, self.roundByePlayerRank, self.roundByePlayerId)

  def setInitialRoundPossiblePlayerMatchCombinations(self, tournamentPossiblePlayerMatchCombinations):
    self.roundPossiblePlayerMatchCombinations = copy.deepcopy(tournamentPossiblePlayerMatchCombinations)

  def filterOutRoundPossiblePlayerMatchCombinationsWithRoundByePlayer(self):
    self.roundPossiblePlayerMatchCombinations = [roundPossiblePlayerMatchCombination for roundPossiblePlayerMatchCombination in self.roundPossiblePlayerMatchCombinations if not any(matchPlayer == self.roundByePlayerId for match in roundPossiblePlayerMatchCombination for matchPlayer in match)]

  def chooseRandomRoundPossiblePlayerMatchCombination(self):
    return random.choice(self.roundPossiblePlayerMatchCombinations)

  def setTournamentPreviousRoundsPlayedMatches(self, tournamentPreviousRoundsPlayedMatches):
    self.tournamentPreviousRoundsPlayedMatches = copy.deepcopy(tournamentPreviousRoundsPlayedMatches)

  def setTournamentPreviousRoundStandings(self, tournamentPreviousRoundStandings):
    self.tournamentPreviousRoundStandings = tournamentPreviousRoundStandings

  def determineRoundPossiblePlayerMatchCombinationQuality(self):
    for roundPossiblePlayerMatchCombination in self.roundPossiblePlayerMatchCombinations:
      roundPossiblePlayerMatchCombinationQuality = 0
      for match in roundPossiblePlayerMatchCombination:
        matchPlayer1Rank = 0
        matchPlayer2Rank = 0
        for tournamentPreviousRoundStanding in self.tournamentPreviousRoundStandings:
          if tournamentPreviousRoundStanding[2] == match[0]:
            matchPlayer1Rank = tournamentPreviousRoundStanding[0]
          elif tournamentPreviousRoundStanding[2] == match[1]:
            matchPlayer2Rank = tournamentPreviousRoundStanding[0]

          if matchPlayer1Rank != 0 and matchPlayer2Rank != 0:
            break
        roundPossiblePlayerMatchCombinationQuality += math.pow(matchPlayer1Rank - matchPlayer2Rank, 2)
    
      roundPossiblePlayerMatchCombination.append(roundPossiblePlayerMatchCombinationQuality)

  def determineBestRoundPossiblePlayerMatchCombination(self):
    bestRoundPossiblePlayerMatchCombination = min(self.roundPossiblePlayerMatchCombinations, key = lambda roundPossiblePlayerMatchCombination: roundPossiblePlayerMatchCombination[-1])
    return bestRoundPossiblePlayerMatchCombination

  def sortBestRoundPlayerMatchCombinationByTournamentCurrentPlayerRanks(self, bestRoundPossiblePlayerMatchCombination):
    bestRoundPossiblePlayerMatchCombination = copy.deepcopy(bestRoundPossiblePlayerMatchCombination)
    bestRoundPossiblePlayerMatchCombinationSorted = []
    for tournamentPreviousRoundStanding in self.tournamentPreviousRoundStandings:
      matchIndex = 0
      while bestRoundPossiblePlayerMatchCombination and matchIndex < len(bestRoundPossiblePlayerMatchCombination) - 1:
        match = bestRoundPossiblePlayerMatchCombination[matchIndex]
        if match[0] == tournamentPreviousRoundStanding[2] or match[1] == tournamentPreviousRoundStanding[2]:
          if match[0] == tournamentPreviousRoundStanding[2]:
            bestRoundPossiblePlayerMatchCombinationSorted.append(match)
          elif match[1] == tournamentPreviousRoundStanding[2]:
            bestRoundPossiblePlayerMatchCombinationSorted.append((match[1], match[0]))
          
          bestRoundPossiblePlayerMatchCombination.remove(match)
          break

        matchIndex += 1

    bestRoundPossiblePlayerMatchCombinationSorted.append(bestRoundPossiblePlayerMatchCombination[-1])    

    return bestRoundPossiblePlayerMatchCombinationSorted

  def setPlayerMatchCombination(self, roundPossiblePlayerMatchCombination):
    self.playerMatchCombination = roundPossiblePlayerMatchCombination

  def simulateMatches(self, players, tournamentPreviousRoundsPlayedMatches):
    self.createMatches(players)
    self.playMatches()
    self.registerMatchesResults()
    self.registerPlayedMatches(tournamentPreviousRoundsPlayedMatches)
    self.registerMatchesResultsInDb()

  def createMatches(self, players):
    matchNbr = 1
    extendedPlayerMatchCombination = []
    for match in self.playerMatchCombination:
      if isinstance(match, (list, tuple)):
        player1Name, player2Name = self.getMatchPlayerNames(match, players)
        matchDetail = (matchNbr, match[0], player1Name, match[1], player2Name)
        match = self.createMatch(matchDetail)
        self.addMatchToRound(match)

        matchNbr += 1

  def createMatch(self, mtch):
    matchNbr = mtch[0]
    player1Id = mtch[1]
    player1Name = mtch[2]
    player2Id = mtch[3]
    player2Name = mtch[4]
    return match.Match(self.dbo, self.tournamentId, self.nbr, matchNbr, player1Id, player1Name, player2Id, player2Name)

  def getMatchPlayerNames(self, match, players):
    player1Name = None
    player2Name = None
    for player in players:
      if player[0] == match[0]:
        player1Name = player[1]
      elif player[0] == match[1]:
        player2Name = player[1]

      if not player1Name is None and not player2Name is None:
        break

    return player1Name, player2Name

  def addMatchToRound(self, match):
    self.matches.append(match)

  def playMatches(self):
    for match in self.matches:
      match.playMatch()

  def registerPlayedMatches(self, tournamentPreviousRoundsPlayedMatches):
    for match in self.matches:
      match.registerMatchAsPlayed(tournamentPreviousRoundsPlayedMatches)

  def registerMatchesResults(self):
    for match in self.matches:
      match.registerMatchResult()

  def registerMatchesResultsInDb(self):
    for match in self.matches:
      match.registerMatchResultInDb()

  def outputRound(self, tournamentTotalRoundCount, tournamentTotalPlayerCountOdd):
    print
    self.outputRoundHeader(tournamentTotalRoundCount)
    print
    if tournamentTotalPlayerCountOdd:
      self.outputRoundByePlayer()
      print
    self.outputRoundMatches()
    print
    self.outputRoundMatchResults()

  def outputRoundHeader(self, tournamentTotalRoundCount):
    print "Round {0} of {1}:".format(self.nbr, tournamentTotalRoundCount)

  def outputRoundByePlayer(self):
    print "Bye Player: {0}".format(self.roundByePlayerName)

  def outputRoundMatches(self):
    for match in self.matches:
      match.outputMatch()

  def outputRoundMatchResults(self):
    for match in self.matches:
      match.outputMatchResult()

  def deleteMatches(self, matchNbrs = None):
    for match in self.matches:
      if matchNbrs is None or match.nbr in matchNbrs:
        self.matches.remove(match)
    if not matchNbrs is None:
      self.deleteTournamentSpecificRoundMatchesFromDb(matchNbrs)

  def deleteTournamentSpecificRoundMatchesFromDb(self, matchNbrs):
    self.dbo.deleteTournamentSpecificRoundMatches(self.tournamentId, self.nbr, matchNbrs)
    