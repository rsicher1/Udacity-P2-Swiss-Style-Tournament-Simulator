#!/usr/bin/env python

import random


class Match:
    ''' Includes tournament match related data and operations '''

    def __init__(self, dbo, tournamentId, roundNbr, matchNbr, player1Id, player1Name, player2Id, player2Name):
        self.dbo = dbo
        self.tournamentId = tournamentId
        self.roundNbr = roundNbr
        self.nbr = matchNbr
        self.player1Id = player1Id
        self.player1Name = player1Name
        self.player2Id = player2Id
        self.player2Name = player2Name

        self.matchOutcome = None
        self.winnerPlayerId = None
        self.winnerPlayerName = None
        self.loserPlayerId = None
        self.loserPlayerName = None
        self.tieFlag = None

    # Chooses a random number between 0 and 1
    def playMatch(self):
        self.matchOutcome = random.random()

    # Based on matchOutcome instance variable, determines whether or not player1 or player2 won or lost or tied
    # when they played the match and sets instance variable appropriately based on the matchOutcome
    def registerMatchResult(self):
        if self.matchOutcome < .45:
            self.winnerPlayerId = self.player1Id
            self.winnerPlayerName = self.player1Name
            self.loserPlayerId = self.player2Id
            self.loserPlayerName = self.player2Name
            self.tieFlag = False
        elif self.matchOutcome >= .45 and self.matchOutcome < .9:
            self.winnerPlayerId = self.player2Id
            self.winnerPlayerName = self.player2Name
            self.loserPlayerId = self.player1Id
            self.loserPlayerName = self.player1Name
            self.tieFlag = False
        else:
            self.winnerPlayerId = self.player1Id
            self.winnerPlayerName = self.player1Name
            self.loserPlayerId = self.player2Id
            self.loserPlayerName = self.player2Name
            self.tieFlag = True

    def registerMatchAsPlayed(self, tournamentPreviousRoundsPlayedMatches):
        tournamentPreviousRoundsPlayedMatches.append((self.player1Id, self.player2Id))

    def registerMatchResultInDb(self):
        self.dbo.registerTournamentMatchResult(self.tournamentId, self.roundNbr, self.nbr, self.winnerPlayerId, self.loserPlayerId, self.tieFlag)

    def outputMatch(self):
        print "Match {0}: {1} vs. {2}".format(self.nbr, self.player1Name, self.player2Name)

    def outputMatchResult(self):
        if not self.tieFlag:
            print "Match {0}: {1} wins".format(self.nbr, self.winnerPlayerName)
        else:
            print "Match {0}: Tie".format(self.nbr)
