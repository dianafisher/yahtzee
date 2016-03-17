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

from models import User, Game, Score, ScoreCard, Roll
from models import StringMessage, NewGameForm, GameForm, RollDiceForm, RollResultForm

from utils import get_by_urlsafe

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)

ROLL_DICE_REQUEST = endpoints.ResourceContainer(
    RollDiceForm,
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
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
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
        return StringMessage(message='User {} created!'.format(
                request.user_name))

# Game
    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')

        game = Game.new_game(user.key)
        score_card = ScoreCard.new_scorecard(user.key, game.key)
        return game.to_form('Welcome to Yahtzee!')

# Roll Dice
    @endpoints.method(request_message=ROLL_DICE_REQUEST,
                      response_message=RollResultForm,
                      path='game/{urlsafe_game_key}',
                      name='roll_dice',
                      http_method='PUT')
    def roll_dice(self, request):
        """Roll dice"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.game_over:
            raise endpoints.NotFoundException('Game already over')

        user = User.query(User.name == request.user_name).get()
        roll = Roll.new_roll(user.key, game.key)

        return roll.to_form()

# registers API
api = endpoints.api_server([YahtzeeApi])         