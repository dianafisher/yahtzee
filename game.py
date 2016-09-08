from protorpc import messages
from google.appengine.ext import ndb

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

    def to_form(self):
        """Returns a GameForm representation of the Game"""
        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        user_name=self.user.get().name,
                        game_over=self.game_over,
                        has_unscored_roll=self.has_unscored_roll)
        return form
    
    
class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    game_over = messages.BooleanField(2, required=True)
    user_name = messages.StringField(3, required=True)
    has_unscored_roll = messages.BooleanField(4, required=True)


class GameForms(messages.Message):
    """Form to return list of games"""
    games = messages.MessageField(GameForm, 1, repeated=True)        