import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

from scorecard import ScoreCard, ScoreCardRequestForm, ScoreCardForm, CategoryType

# class CategoryType(messages.Enum):
#     """CategoryType -- enumeration value"""
#     ACES = 1
#     TWOS = 2
#     THREES = 3
#     FOURS = 4
#     FIVES = 5
#     SIXES = 6
#     THREE_OF_A_KIND = 7
#     FOUR_OF_A_KIND = 8
#     FULL_HOUSE = 9
#     SMALL_STRAIGHT = 10
#     LARGE_STRAIGHT = 11
#     YAHTZEE = 12
#     CHANCE = 13


class Roll(ndb.Model):
    """Roll object """
    user = ndb.KeyProperty(required=True, kind='User')
    game = ndb.KeyProperty(required=True, kind='Game')
    dice = ndb.PickleProperty(required=True)
    count = ndb.IntegerProperty(required=True, default=0)
    isScored = ndb.BooleanProperty(required=True, default=False)

    @classmethod
    def new_roll(cls, user, game):
        """Creates a new roll for a user"""
        roll = Roll(user=user,
                    game=game)

        roll.dice = []
        for i in range(5):
            value = random.choice(range(1, 7))
            roll.dice.append(value)
            print value

        roll.count = 1
        roll.put()
        return roll

    def reroll(self, keepers):
        """Rerolls the dice but keeps dice listed in keepers.  
        Keepers array contains 0 or 1 (replace, keep) for each die index."""
        print 'keepers', keepers
        print 'current dice', self.dice

        for i in range(5):
            if keepers[i] == 0:
                value = random.choice(range(1, 7))
                self.dice[i] = value
                print value

        self.count += 1
        self.put()
        return self.to_form()

    def current_score_for_category(self, category_type):
        game = self.game.get()
        user = self.user.get()

        # Get the user's score card for this game.
        scorecard = ScoreCard.query(
            ndb.AND(ScoreCard.user == user.key, ScoreCard.game == game.key)).get()
        print 'scorecard: ', scorecard
        return scorecard.category_scores[str(category_type)]

    def to_form(self):
        return RollResultForm(urlsafe_key=self.key.urlsafe(),
                              user_name=self.user.get().name,
                              dice=self.dice,
                              count=self.count,
                              isScored=self.isScored
                              )

    def calculate_score(self, category_type):

        game = self.game.get()
        user = self.user.get()

        # Get the user's score card for this game.
        scorecard = ScoreCard.query(
            ndb.AND(ScoreCard.user == user.key, ScoreCard.game == game.key)).get()

        game.has_unscored_roll = False
        game.put()

        # scorecard.category_scores[str(category_type)] = score
        # scorecard.put()

        print 'scorecard: ', scorecard

        scorecard.calculate_score_for_category(self.dice, category_type)

        print 'scorecard after scoring: ', scorecard
        self.isScored = True
        self.put()

        return scorecard.to_form()

    def totalOf(self, value):
        score = 0
        for d in self.dice:
            if d is value:
                score += d
        return score


class RollDiceForm(messages.Message):
    """Used to make a move in an existing game"""
    user_name = messages.StringField(1, required=True)


class RollResultForm(messages.Message):
    urlsafe_key = messages.StringField(1, required=True)
    user_name = messages.StringField(2, required=True)
    dice = messages.IntegerField(3, repeated=True)
    count = messages.IntegerField(4, required=True)
    isScored = messages.BooleanField(5, required=True)


class RerollDiceForm(messages.Message):
    """Used to reroll the dice but keep dice listed in keepers"""
    keepers = messages.IntegerField(1, repeated=True)


class ScoreRollForm(messages.Message):
    category_type = messages.EnumField('CategoryType', 1)


class ScoreRollResultForm(messages.Message):
    score = messages.IntegerField(1, required=True)
