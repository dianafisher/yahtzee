"""
yahtzee.py - Create and configure the game API.

"""
__author__ = 'diana.fisher@gmail.com (Diana Fisher)'

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from google.appengine.ext import ndb

from models import User, Game, Score
from models import StringMessage, GameForm, GameForms, UserForm, UserForms

from roll import Roll, RollDiceForm, RollResultForm, ScoreRollForm, ScoreRollResultForm, RerollDiceForm

from scorecard import CategoryType, ScoreCard, ScoreCardRequestForm, ScoreCardForm

from utils import get_by_urlsafe

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

NEW_GAME_REQUEST = endpoints.ResourceContainer(user_name = messages.StringField(1, required=True))

USER_GAMES_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1))

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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# @endpoints.api( name='yahtzee',
#                 version='v1',
#                 allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
#                 scopes=[EMAIL_SCOPE])

@endpoints.api( name='yahtzee', version='v1' )
class YahtzeeApi(remote.Service):
    """Yahtzee API v0.1"""

# Users
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

    # Get users
    @endpoints.method(response_message=UserForms,
                      path='user/list',
                      name='get_users',
                      http_method='GET')
    def get_users(self, request):
      """Returns list of all users."""      
      return UserForms(users=[user.to_form() for user in User.query()])

# Game
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
                      http_method='POST')
    def get_user_games(self, request):
      # Query for a user with this user name.
      user = User.query(User.name == request.user_name).get()
      if not user:
          message = ('User {} not found!').format(request.user_name)
          raise endpoints.NotFoundException(message)
      # Query for all active games for this user.
      games = Game.query(Game.user == user.key).filter(Game.game_over == False)
      return GameForms(games=[game.to_form() for game in games])

# Roll Dice
    @endpoints.method(request_message=ROLL_DICE_REQUEST,
                      response_message=RollResultForm,
                      path='game/{urlsafe_game_key}/roll',
                      name='roll_dice',
                      http_method='PUT')
    def roll_dice(self, request):
        """Roll dice"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.game_over:
            raise endpoints.NotFoundException('Game already over')

        # if game.has_unscored_roll:
        #     raise endpoints.ConflictException('Cannot roll again until current roll has been scored.  Please score current roll.')
        
        game.has_unscored_roll = True
        game.put()

        user = User.query(User.name == request.user_name).get()
        roll = Roll.new_roll(user.key, game.key)

        return roll.to_form()

    @endpoints.method(request_message=REROLL_DICE_REQUEST,
                      response_message=RollResultForm,
                      path='roll/{urlsafe_roll_key}/retry',
                      name='reroll_dice',
                      http_method='PUT')
    def reroll_dice(self, request):
        """Method to roll dice again after first roll"""
                
        roll = get_by_urlsafe(request.urlsafe_roll_key, Roll)
        if not roll:
            raise endpoints.NotFoundException('Roll not found')
        if roll.count == 3:
            raise endpoints.ConflictException('Cannot roll more than 3 times in a single turn.  Please score roll instead.')

        return roll.reroll(request.keepers)


    @endpoints.method(request_message=SCORE_ROLL_REQUEST,
                      response_message=ScoreCardForm,
                      path='roll/{urlsafe_roll_key}/score',
                      name='score_roll',
                      http_method='PUT')
    def score_roll(self, request):
        """Score roll"""        
        roll = get_by_urlsafe(request.urlsafe_roll_key, Roll)
        if not roll:
            raise endpoints.NotFoundException('Roll not found')

        category_type = request.category_type
        # print 'roll', roll
        # user = roll.user.get()
        # print 'user', user
        # game = roll.game.get()
        # print 'game', game
        # # Get the user's scorecard for this game.
        # scorecard = ScoreCard.query(ndb.AND(ScoreCard.user == user.key, ScoreCard.game == game.key )).get()
        # print 'scorecard', scorecard

        current_score = roll.current_score_for_category(category_type)
        # print 'current_score:', current_score

        if current_score > -1:
          message = ('{} category already contains a score.  Please select a different score category.').format(str(category_type))
          # print message
          raise endpoints.ConflictException(message)

        return roll.calculate_score(category_type)

# Score Card
    @endpoints.method(request_message=SCORECARD_REQUEST,
                      response_message=ScoreCardForm,
                      path='game/{urlsafe_game_key}/scorecard',
                      name='score_card',
                      http_method='POST')
    def score_card(self, request):
      """Returns the user's scorecard for the game"""
      user = User.query(User.name == request.user_name).get()
      if not user:
        raise endpoints.NotFoundException('A User with that name does not exist!')

      game = get_by_urlsafe(request.urlsafe_game_key, Game)
      if not game:
        raise endpoints.NotFoundException('Game not found')

      scorecard = ScoreCard.query(ndb.AND(ScoreCard.user == user.key, ScoreCard.game == game.key )).get()
      print 'scorecard', scorecard
      return scorecard.to_form()
        

# registers API
api = endpoints.api_server([YahtzeeApi])         