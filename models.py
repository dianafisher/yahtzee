"""
models.py - This file contains the class definitions for the Datastore
entities used by the game.
"""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

class User(ndb.Model):
    """ User object """
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()

    def to_form(self):
        """Returns a UserForm representation of the User"""
        form = UserForm(urlsafe_key=self.key.urlsafe(),
                        user_name=self.name,
                        email=self.email)
        return form

class Game(ndb.Model):
    """ Game object """
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    history = ndb.PickleProperty(required=True)    
    has_unscored_roll = ndb.BooleanProperty(required=True)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        game = Game(user=user)
        game.history = []
        game.has_unscored_roll = False    
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        user_name=self.user.get().name,
                        message=message,
                        game_over=self.game_over,
                        has_unscored_roll=self.has_unscored_roll)
        return form    

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True        
        self.put()
        # # Add the game to the score 'board'
        # score = Score(user=self.user, date=date.today(), won=won,
        #               guesses=self.attempts_allowed - self.attempts_remaining)
        # score.put()

class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    rolls = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses)

# class Turn(ndb.Model):
#     """Turn object - Each turn consits of up to three rolls."""
#     user = ndb.KeyProperty(required=True, kind='User')
#     game = ndb.KeyProperty(required=True, kind='Game')
#     roll_count = ndb.IntegerProperty(required=True, default=0)
#     dice = ndb.PickleProperty(required=True)

#     @classmethod
#     def new_turn(cls, user, game):
#         """Creates a new turn"""
#         turn = Turn(user=user, game=game)
#         turn.dice = []
#         turn.put()
#         return turn

#     def roll_dice(self, keepers):
#         if self.roll_count == 3:
#             raise ValueError('Cannot roll dice more than three times in one turn')

#         for i in range(5):
#             value = random.choice(range(1, 7))
#             self.dice.append(value)
#             self.roll_count += 1
#             print value
    
#         self.put()

# Forms/Messages

class UserForm(messages.Message):
    """UserForm for outbound user information"""    
    urlsafe_key = messages.StringField(1, required=True)
    user_name = messages.StringField(2, required=True)
    email = messages.StringField(3, required=True)

class UserForms(messages.Message):
    """Used to get the list of all users"""
    users = messages.MessageField(UserForm, 1, repeated=True)

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)    
    game_over = messages.BooleanField(2, required=True)
    message = messages.StringField(3, required=True)
    user_name = messages.StringField(4, required=True)
    has_unscored_roll = messages.BooleanField(5, required=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)    


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.IntegerField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    rolls = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)    

