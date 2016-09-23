from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

class Game(ndb.Model):
    """ Game object """
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    history = ndb.PickleProperty(required=True)
    has_incomplete_turn = ndb.BooleanProperty(required=True)
    turn_count = ndb.IntegerProperty(required=True, default=0)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        game = Game(user=user)
        game.history = {}
        game.turn_count = 0
        game.has_incomplete_turn = False
        game.put()
        return game

    def to_form(self):
        """Returns a GameForm representation of the Game"""
        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        user_name=self.user.get().name,
                        game_over=self.game_over,
                        turn_count=self.turn_count,
                        has_incomplete_turn=self.has_incomplete_turn)
        return form

    def end_game(self, score):        
        self.game_over = True
        self.put()

        # Update the user
        # Get the user
        user = self.user.get()
        # Set the new high score for the user
        user.add_score(score)
        # Save changes made to user
        user.put()

        # Add the game to the score board.
        score = Score(user=self.user, date=date.today(), score=score)
        score.put()
    
    
class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)    
    score = ndb.IntegerProperty(required=True)    

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name,
                         date=str(self.date), 
                         score=self.score)


# Forms

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    game_over = messages.BooleanField(2, required=True)
    user_name = messages.StringField(3, required=True)
    turn_count = messages.IntegerField(4, required=True)
    has_incomplete_turn = messages.BooleanField(5, required=True)


class GameForms(messages.Message):
    """Form to return list of games"""
    games = messages.MessageField(GameForm, 1, repeated=True)        


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    score = messages.IntegerField(3, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class HighScoresForm(messages.Message):
    scores = messages.IntegerField(1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)

class GameHistoryForm(messages.Message):
    history = messages.StringField(1, required=True)    