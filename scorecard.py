from protorpc import messages
from google.appengine.ext import ndb

class ScoreCard(ndb.Model):
    """ScoreCard object"""
    user = ndb.KeyProperty(required=True, kind='User')
    game = ndb.KeyProperty(required=True, kind='Game')
    bonus_points = ndb.IntegerProperty(default=0)
    is_full = ndb.BooleanProperty(required=True, default=False)
    category_scores = ndb.PickleProperty(required=True)

    @classmethod
    def new_scorecard(cls, user, game):
        """Creates a new score card for a user"""
        score_card = ScoreCard(user=user, game=game)
        scores = {}
        scores['ACES'] = -1
        scores['TWOS'] = -1
        scores['THREES'] = -1
        scores['FOURS'] = -1
        scores['FIVES'] = -1
        scores['SIXES'] = -1
        scores['THREE_OF_A_KIND'] = -1
        scores['FOUR_OF_A_KIND'] = -1
        scores['FULL_HOUSE'] = -1
        scores['SMALL_STRAIGHT'] = -1
        scores['LARGE_STRAIGHT'] = -1
        scores['YAHTZEE'] = -1
        scores['CHANCE'] = -1
        score_card.category_scores = scores
        score_card.put()
        return score_card

    def to_form(self):
        return ScoreCardForm(            
            scores=str(self.category_scores),
            bonus_points = self.bonus_points,
            is_full = self.is_full
        )
            

class ScoreCardRequestForm(messages.Message):
    """Used to request the user's scorecard"""
    user_name = messages.StringField(1, required=True)    

class ScoreCardForm(messages.Message):
    """Used to return the user's scorecard"""    
    bonus_points = messages.IntegerField(1, required=True)
    scores = messages.StringField(2, required=True)
    is_full = messages.BooleanField(3, required=True)    