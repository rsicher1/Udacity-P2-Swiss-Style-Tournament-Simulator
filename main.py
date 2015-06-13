#!/usr/bin/env python

import databaseoperations
import tournament

if "__main__":
  dbo = databaseoperations.DatabaseOperations()

  playerIds = []
  playerIds.append(dbo.registerPlayer("Ross S"))
  playerIds.append(dbo.registerPlayer("Hill L"))
  playerIds.append(dbo.registerPlayer("Marc V"))
  playerIds.append(dbo.registerPlayer("Ross B"))
  playerIds.append(dbo.registerPlayer("Andy R"))
  playerIds.append(dbo.registerPlayer("Peter R"))
  playerIds.append(dbo.registerPlayer("Dave G"))
#  playerIds.append(dbo.registerPlayer("Mary S"))

  tournament = tournament.Tournament("The Greatest And Best Tournament In The World... Tribute", dbo)

  for playerId in playerIds:
    tournament.registerPlayerInDb(playerId)

  tournament.simulate()