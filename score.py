from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

"""
score.py - This file contains the class definitions for the Datastore
entities used by the game.
"""


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