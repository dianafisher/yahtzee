# Yahtzee

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.

##Game Description:

[Source](https://en.wikipedia.org/wiki/Yahtzee)

Yahtzee is a dice game made by Milton Bradley.  The objective of the game is to score the most points by rolling five dice to make certain combinations.  The dice can be rolled up to three times in a turn to try to make various scoring combinations.  A game consists of thirteen rounds.  After each round the player chooses which scoring category is to be used for that round.  Once a category has been used in the game, it cannot be used again.  The scoring categories have varying point values, some of which are fixed values and others where the score depends on the value of the dice.  A YAHTZEE is five-of-a-kind and scores 50 points; the highest of any category.  The winner is the player who scores the most points.

#### Game Play

Each player is given 13 turns in all to score. In each turn the dice can be rolled up to three times. The player is not required to roll dice for exactly three times. If they have achieved a combination earlier, they can call it and pass the turn to next player. There are a total of 13 possible combinations and each combination can only be used once so once a player has called for a combination and used it, it can not be used to score in later turns.

The scorecard contains two sections: an upper section and a lower section.

Players can make 35 points bonus if they score a total of 63 or more in the upper section.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
- **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User.  user_name must be provided and must be unique.
    - Exceptions: A ConfictException will be raised if a User with that user_name already exists.
- 
