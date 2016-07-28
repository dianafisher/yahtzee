import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

from scorecard import ScoreCard, ScoreCardRequestForm, ScoreCardForm

class CategoryType(messages.Enum):
    """CategoryType -- enumeration value"""
    ACES = 1
    TWOS = 2
    THREES = 3
    FOURS = 4
    FIVES = 5    
    SIXES = 6
    THREE_OF_A_KIND = 7
    FOUR_OF_A_KIND = 8
    FULL_HOUSE = 9
    SMALL_STRAIGHT = 10
    LARGE_STRAIGHT = 11
    YAHTZEE = 12
    CHANCE = 13

class Roll(ndb.Model):
    """Roll object """
    user = ndb.KeyProperty(required=True, kind='User')
    game = ndb.KeyProperty(required=True, kind='Game')
    dice = ndb.PickleProperty(required=True)
    count = ndb.IntegerProperty(required=True, default=0)    

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
        """Rerolls the dice but keeps dice listed in keepers"""
        print 'keepers', keepers
        self.dice = []
        for i in range(5):
            value = random.choice(range(1, 7))
            self.dice.append(value)
            print value

        self.count += 1
        self.put()
        return self.to_form()

    def to_form(self):
        return RollResultForm(urlsafe_key=self.key.urlsafe(),
                            user_name=self.user.get().name,
                            dice=self.dice,                            
                            count=self.count
                            )
    
    def calculate_score(self, category_type):

        game = self.game.get()
        user = self.user.get()
        
        # Get the user's score card for this game.
        scorecard = ScoreCard.query(ndb.AND(ScoreCard.user == user.key, ScoreCard.game == game.key )).get()        

        # Maintain a frequency table of dice values
        frequencies = {}
        for d in self.dice:
            if d in frequencies:
                count = frequencies[d]
                count += 1
                frequencies[d] = count
            else:
                frequencies[d] = 1

        score = 0
        if (category_type is CategoryType.ACES):
            # Total of ones only
            score = self.totalOf(1)
            category = str(CategoryType.ACES)
            
        elif (category_type is CategoryType.TWOS):
            # Total of twos only
            score = self.totalOf(2)
            category = str(CategoryType.TWOS)

        elif (category_type is CategoryType.THREES):
            # Total of threes only
            score = self.totalOf(3)
            category = str(CategoryType.THREES)

        elif (category_type is CategoryType.FOURS):
            # Total of fours only
            score = self.totalOf(4)
            category = str(CategoryType.FOURS)

        elif (category_type is CategoryType.FIVES):
            # Total of fives only
            score = self.totalOf(5)
            category = str(CategoryType.FIVES)

        elif (category_type is CategoryType.SIXES):
            # Total of sixes only
            score = self.totalOf(6)
            category = str(CategoryType.SIXES)

        elif (category_type is CategoryType.THREE_OF_A_KIND):
            category = str(CategoryType.THREE_OF_A_KIND)
            # If there are three of a kind, the score is equal to the sum of all five dice.
            found = False
            for d in frequencies:
                if frequencies[d] >= 3:
                    found = True
                    break
            if found:
                score = sum(self.dice)        

        elif (category_type is CategoryType.FOUR_OF_A_KIND):
            category = str(CategoryType.FOUR_OF_A_KIND)
            # If there are four of a kind, the score is equal to the sum of all five dice.
            found = False
            for d in frequencies:
                if frequencies[d] >= 4:
                    found = True
                    break
            if found:
                score = sum(self.dice)

        elif category_type is CategoryType.FULL_HOUSE:
            category = str(CategoryType.FULL_HOUSE)
            # A full house is worth 25 points.
            if 2 in frequencies.values() and 3 in frequencies.values():
                score = 25

        elif category_type is CategoryType.SMALL_STRAIGHT:
            category = str(CategoryType.SMALL_STRAIGHT)
            # A small straight is worth 30 points.                        
            if {1,2,3,4} <= set(self.dice):
                score = 30
            elif {2,3,4,5} <= set(self.dice):
                score = 30
            elif {3,4,5,6} <= set(self.dice):
                score = 30

        elif category_type is CategoryType.LARGE_STRAIGHT:
            category = str(CategoryType.LARGE_STRAIGHT)
            # A large straight is worth 40 points.
            if {1,2,3,4,5} <= set(self.dice):
                score = 40
            elif {2,3,4,5,6} <= set(self.dice):
                score = 40

        elif category_type is CategoryType.YAHTZEE:
            category = str(CategoryType.YAHTZEE)
            # Five of a kind.  A Yahtzee is worth 50 points.
            if 5 in frequencies.values():
                score = 50

        elif category_type is CategoryType.CHANCE:
            category = str(CategoryType.CHANCE)
            # Sum of all five dice.
            score = sum(self.dice)                   
        
        game.has_unscored_roll = False
        game.put()

        scorecard.category_scores[category] = score
        print 'updated scorecard', scorecard
        scorecard.put()

        return ScoreRollResultForm(score=score)

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

class RerollDiceForm(messages.Message):
    """Used to reroll the dice but keep dice listed in keepers"""
    keepers = messages.IntegerField(1, repeated=True)

class ScoreRollForm(messages.Message):
    category_type = messages.EnumField('CategoryType', 1)         

class ScoreRollResultForm(messages.Message):
    score = messages.IntegerField(1, required=True)
