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

This API supports a single-player version of Yahzee.  Yahtzee is a dice game made by Milton Bradley.  The objective of the game is to score the most points by rolling five dice to make certain combinations.  The dice can be rolled up to three times in a turn to try to make various scoring combinations.  A game consists of thirteen turns.  After each turn the player chooses which scoring category is to be used for that turn.  Once a category has been used in the game, it cannot be used again.  The scoring categories have varying point values, some of which are fixed values and others where the score depends on the value of the dice.  A Yahtzee is five-of-a-kind and scores 50 points; the highest of any category.  The goal is to score the most points.

A scorecard is provided for the user for each game.  It contains 13 different category boxes and in each turn, after the third roll, the player must choose one of these categories. The score entered in the box depends on how well the five dice match the scoring rule for the category.  The scorecard categories are divided into two sections: the upper section and the lower section.

In the upper section there are six boxes. The score in each of these boxes is determined by adding the total number of dice matching that box.  If a player scores a total of 63 or more points in these six boxes, a bonus of 35 is added to the upper section score.

The lower section contains a number of poker-themed categories with specific point values.

If a category is chosen but the dice do not match the requirements of the category the player scores 0 in that category. 

A Yahtzee occurs when all five dice are the same. If a player throws a Yahtzee but the Yahtzee category has already been used, special rules apply.  If the player throws a Yahtzee and has already filled the Yahtzee box with a score of 50, they score a Yahtzee bonus and get an extra 100 points. However, if they throw a Yahtzee and have filled the Yahtzee category with a score of 0, they do not get a Yahtzee bonus.  This API does not support Joker rules for Yahtzee bonuses. [*](https://en.wikipedia.org/wiki/Yahtzee#Rules)

##Files Included:
 - yahztee.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
- **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email
    - Returns: UserForm with new user details.
    - Description: Creates a new User.  user_name must be provided and must be unique.
    - Exceptions: A ConflictException will be raised if a User with that user_name already exists.

- **get_users**
    - Path: 'user'
    - Method: GET
    - Parameters: None
    - Returns: UserForms
    - Description: Returns all Users in the database.
    - Exceptions: None

- **get_user**
    - Path: 'user/{urlsafe_user_key}'
    - Method: GET
    - Parameters: urlsafe_user_key
    - Returns: UserForm.
    - Description: Returns the information for a specific User.
    - Exceptions: A NotFoundException will be raised if the User is not found. 

- **create_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game for the user.
    - Exceptions: A NotFoundException will be raised if the User is not found. 

- **get_games**
    - Path: 'game'
    - Method: GET
    - Parameters: None
    - Returns: GameForms
    - Description: Returns all Games in the database.
    - Exceptions: None

- **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of the Game.
    - Exceptoins: A NotFoundException will be raised if the Game is not found.

- **cancel_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage confirming deletion of game.
    - Description: Deletes the game.
    - Exceptions: A BadRequestException will be raised if the game is already over.  A NotFoundException will be raised if the Game is not found.

- **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: StringMessage containing game history.
    - Description: Returns the turn history of a game as a stringified dictionary.  The keys of the dictionary are the turn numbers and the values consist of a list of rolls for each turn.  Each roll is represented as a tuple of roll number and the list of dice values in that roll.  Finally, the category selected and the score calculated for the turn is appened to the list as a tuple.
    - Exceptions: A NotFoundException will be raised if the Game is not found.

- **get_high_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: number_of_results (optional)
    - Returns: HighScoreForm.
    - Description: Returns scores in the database sorted in decreasing order.

- **get_scorecard**
    - Path: 'game/{urlsafe_game_key}/scorecard'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: ScoreCardForm
    - Description: Returns the scorecard for the game.
    - Exceptions: A NotFoundException will be raised if the Game is not found or the Scorecard for the game is not found.

- **get_user_games**
    - Path: 'user/games'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms with 1 or more GameForm inside.
    - Description: Returns all of the User's active games.
    - Exceptions:

- **get_user_rankings**
    - Path: 'user/ranking'
    - Method: GET
    - Parameters: None
    - Returns: UserForms
    - Description: Returns all users ranked by their high score.

- **create_turn**
    - Path: 'game/{urlsafe_game_key}/turn'
    - Method: POST
    - Paramters: urlsafe_game_key
    - Returns: TurnForm
    - Description:
    - Exceptions: 

- **roll_again**
- **score_turn**




##Models Included:
- **User**
    - Stores unique user_name and (optional) email address.
    - Keeps track of total_played

- **Game**
    - Stores unique game states.  Associated with User model via KeyProperty user_name

- **Turn**
    - Stores each roll of the five dice.
    - Associated with Game model via KeyProperty game

- **Scorecard**
    - Stores the score earned for each category.

- **Score**
    - Records completed games.  Associated with User model via KeyProperty user_name

##Forms Included:
- **HighScoresForm**
    - Contains the score.
- **GameForm**
    - Representation of a Game's state.
- **GameForms**
    - Container for one or more GameForm
- **GameHistoryForm**
- **ScorecardForm**
    - Representation of the user's scorecard for the game.
- **ScoreTurnForm**
- **TurnForm**
    - Representation of a Turn.
- **UserForm**
    - Representation of a User.  Includes the User's high score.
- **UserForms**
    - Container for one or more UserForm.
