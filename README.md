### **Swiss-Style Tournament Simulator**

Simulates swiss-style tournaments using a PostgreSQL database to keep track of players and matches

#### Features
* Supports multiple tournaments
* Prevents rematches between tournament players
* Handles an odd number of tournament players, assigning a bye player in each round and creditting them with an automatic win. In the first round, the bye player that is chosen is random. In subsequent rounds, the bye player which is chosen is the top ranked player who has not yet had a bye.
* Supports ties
* Ranks tournament players according to points earned from wins and ties (# of Wins + # of Ties * 0.5).
* Supports Opponent Match Points (OMP) ranking (# of Wins + # of Ties * 0.5 for each previously played player)

#### Running The Application

##### Requirements:
You need Python installed on your system. For download/install instructions, refer to this guide:  

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[https://wiki.python.org/moin/BeginnersGuide/Download](https://wiki.python.org/moin/BeginnersGuide/Download)

You also need PostgreSQL installed on your system. For download/install instructions, refer to this guide:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[https://wiki.postgresql.org/wiki/Detailed_installation_guides](https://wiki.postgresql.org/wiki/Detailed_installation_guides)

To set up the application's database, use the logic in **tournament.sql**

##### In Terminal:
In a unix/osx shell or windows command prompt, execute the following commands:

Full Simulation
```sh
$ python main.py
```
Test Cases
```sh
$ python tournament_test.py
```

##### In Idle:

Full Simulation

* Open **main.py**

Test Cases
* Open **tournament_test.py**

Run The Module (Run > Run Module)