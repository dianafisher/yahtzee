import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from google.appengine.ext import ndb

from models import User, Score, GameHistoryForm, \
    StringMessage, UserForm, UserForms, HighScoresForm

from game import Game, GameForm, GameForms

from roll import Roll, RollDiceForm, RollResultForm
from roll import ScoreRollResultForm, RerollDiceForm
from scorecard import CategoryType, ScoreCard, ScoreRollForm
from scorecard import ScoreCardRequestForm, ScoreCardForm

from utils import get_by_urlsafe

"""
yahtzee.py - Create and configure the game API.

"""
__author__ = 'diana.fisher@gmail.com (Diana Fisher)'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Resource Containers

USER_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),
    email=messages.StringField(2))

NEW_GAME_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1, required=True))

GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1))

USER_GAMES_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1))

ROLL_DICE_REQUEST = endpoints.ResourceContainer(
    RollDiceForm,
    urlsafe_game_key=messages.StringField(1),)

SCORE_ROLL_REQUEST = endpoints.ResourceContainer(
    ScoreRollForm,
    urlsafe_roll_key=messages.StringField(1),)

REROLL_DICE_REQUEST = endpoints.ResourceContainer(
    RerollDiceForm,
    urlsafe_roll_key=messages.StringField(1),)

SCORECARD_REQUEST = endpoints.ResourceContainer(
    ScoreCardRequestForm,
    urlsafe_game_key=messages.StringField(1),)

HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# @endpoints.api( name='yahtzee',
#                 version='v1',
#                 allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
#                 scopes=[EMAIL_SCOPE])


@endpoints.api(name='yahtzee', version='v1')
class YahtzeeApi(remote.Service):
    """Yahtzee API v0.1"""

    # Create user
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=UserForm,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        # return StringMessage(message='User {} created!'.format(
        #         request.user_name))
        return user.to_form()

    #Get user rankings
    @endpoints.method(response_message=UserForms,
                      path='user/ranking',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
      """Return all Users ranked by their high score"""
      users = User.query().fetch()
      users = sorted(users, key=lambda x:x.high_score, reverse=True)
      return UserForms(users=[user.to_form() for user in users])

    # Get all users
    @endpoints.method(response_message=UserForms,
                      path='user/list',
                      name='get_users',
                      http_method='GET')
    def get_users(self, request):
        """Returns the list of all users."""
        return UserForms(users=[user.to_form() for user in User.query()])

    # Create new game for user
    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        print 'new game requested for user ', request.user_name
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')

        game = Game.new_game(user.key)
        score_card = ScoreCard.new_scorecard(user.key, game.key)
        return game.to_form()

    # Get user active games
    @endpoints.method(request_message=USER_GAMES_REQUEST,
                      response_message=GameForms,
                      path='user/games',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns the active games for a user."""

        # Query for a user with this user name.
        user = User.query(User.name == request.user_name).get()
        if not user:
            message = ('User {} not found!').format(request.user_name)
            raise endpoints.NotFoundException(message)
        # Query for all active games for this user.
        games = Game.query(Game.user == user.key).filter(
            Game.game_over == False)
        return GameForms(games=[game.to_form() for game in games])

    # Cancel game
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Delete an active game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game and not game.game_over:
            game.key.delete()
            return StringMessage(message='Game with key: {} deleted.'.
                                 format(request.urlsafe_game_key))
        elif game and game.game_over:
            raise endpoints.BadRequestException('Game is already over!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    # Roll Dice
    @endpoints.method(request_message=ROLL_DICE_REQUEST,
                      response_message=RollResultForm,
                      path='game/{urlsafe_game_key}/roll',
                      name='roll_dice',
                      http_method='PUT')
    def roll_dice(self, request):
        """Roll dice.  This is the first roll of a turn."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.game_over:
            raise endpoints.NotFoundException('Game already over')

        # if game.has_unscored_roll:
        #     raise endpoints.ConflictException('Cannot roll again until current roll has been scored.  Please score current roll.')

        user = User.query(User.name == request.user_name).get()
        roll = Roll.new_roll(user.key, game.key)

        # Add the roll to the game history.
        entry = (1, roll.dice)
        game.history.append(entry)
        game.has_unscored_roll = True
        game.put()

        return roll.to_form()

    # Get Game History
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistoryForm,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET'
                      )
    def get_game_history(self, request):
        """Returns the roll and score history for a game."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')

        return GameHistoryForm(history=str(game.history))

    # Roll Dice again (in a single turn)
    @endpoints.method(request_message=REROLL_DICE_REQUEST,
                      response_message=RollResultForm,
                      path='roll/{urlsafe_roll_key}/retry',
                      name='reroll_dice',
                      http_method='PUT')
    def reroll_dice(self, request):
        """
        Roll dice again after first roll of a turn.  
        An array of integers indiciting the dice to 'keep' from the previous roll must be provided.
        A value of '0' indicates the die at that index should be replaced.
        A value of '1' indicates the die at that index should be kept.

        Example A: [0,1,1,0,0] means the dice at index 1 and 2 should be kept, all others replaced.
        Example B: [0,0,0,0,0] means all dice should be replaced.
        """

        roll = get_by_urlsafe(request.urlsafe_roll_key, Roll)
        if not roll:
            raise endpoints.NotFoundException('Roll not found')
        if roll.count == 3:
            raise endpoints.ConflictException(
                'Cannot roll more than 3 times in a single turn.  Please score roll instead.')

        keepers = request.keepers
        if len(keepers) != 5:
          raise endpoints.ConflictException('Keepers array must have five elements (0 or 1).')

        return roll.reroll(request.keepers)

    # Calculate the score for the specified roll
    @endpoints.method(request_message=SCORE_ROLL_REQUEST,
                      response_message=ScoreCardForm,
                      path='roll/{urlsafe_roll_key}/score',
                      name='score_roll',
                      http_method='PUT')
    def score_roll(self, request):
        """
        Calculates the score for the roll specified.
        Required Params: url safe key for the Roll and the category to score the roll in.
        """
        roll = get_by_urlsafe(request.urlsafe_roll_key, Roll)
        if not roll:
            raise endpoints.NotFoundException('Roll not found')

        category_type = request.category_type
        print 'category_type:', category_type

        game = roll.game.get()
        user = roll.user.get()

        # Get the user's score card for this game.
        scorecard = ScoreCard.query(
            ndb.AND(ScoreCard.user == user.key, ScoreCard.game == game.key)).get()

        # print 'scorecard: ', scorecard
        current_score = scorecard.category_scores[str(category_type)]
        # current_score = roll.current_score_for_category(category_type)
        # print 'current_score:', current_score

        """The YAHTZEE category is the only category which can be scored more than once. 
           So check the category type and whether or not the category had already been scored.
        """
        if category_type is not 'YAHZTEE' and current_score > -1:
            message = ('{} category already contains a score.  Please select a different score category.').format(
                str(category_type))
            raise endpoints.ConflictException(message)

        # Calculate the score for this roll based on the category selected.
        score = scorecard.calculate_score_for_category(
            roll.dice, category_type)

        # Create a score entry for the game history.
        entry = (str(category_type), score)
        # Add the entry to the game history.
        game.history.append(entry)

        # Update the scorecard with the calculated score.
        scorecard.category_scores[str(category_type)] = score
        
        roll.isScored = True
        roll.put()

        # Save the updated scorecard values.
        scorecard.put()

        # Check to see if the game is over.
        game_over = scorecard.check_full()
        print 'game_over = ', game_over

        # If the game is now over, calculate the final score.
        if game_over:
            # Set game over flag on the game
            game.game_over = True

            final_score = scorecard.calculate_final_score()
            print 'final score:', final_score

            # Set the new high score for the user
            user.add_score(final_score)          

        # Save the changes made to game
        game.put()

        # Save the changes made to the user
        user.put()

        return scorecard.to_form()

    # Get user's scorecard
    @endpoints.method(request_message=SCORECARD_REQUEST,
                      response_message=ScoreCardForm,
                      path='game/{urlsafe_game_key}/scorecard',
                      name='score_card',
                      http_method='GET')
    def score_card(self, request):
        """Returns the user's scorecard for the game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')

        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')

        scorecard = ScoreCard.query(
            ndb.AND(ScoreCard.user == user.key, ScoreCard.game == game.key)).get()
        print 'scorecard', scorecard
        return scorecard.to_form()

    # Get high scores
    @endpoints.method(request_message=HIGH_SCORES_REQUEST,
                      response_message=HighScoresForm,
                      path='high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """
        Returns a list of high scores in descending order.
        Optional Parameter: number_of_results to limit the number of results returned.
        """
        users = User.query().fetch()
        users = sorted(users, key=lambda x:x.high_score, reverse=True)
        return HighScoresForm(scores=[user.high_score for user in users])

# registers API
api = endpoints.api_server([YahtzeeApi])
