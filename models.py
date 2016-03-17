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
                        game_over=self.game_over)
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
        elif (category_type is CategoryType.TWOS):
            # Total of twos only
            score = self.totalOf(2)
        elif (category_type is CategoryType.THREES):
            # Total of threes only
            score = self.totalOf(3)
        elif (category_type is CategoryType.FOURS):
            # Total of fours only
            score = self.totalOf(4)
        elif (category_type is CategoryType.FIVES):
            # Total of fives only
            score = self.totalOf(5)
        elif (category_type is CategoryType.SIXES):
            # Total of sixes only
            score = self.totalOf(6)
        elif (category_type is CategoryType.THREE_OF_A_KIND):
            # If there are three of a kind, the score is equal to the sum of all five dice.
            found = False
            for d in frequencies:
                if frequencies[d] >= 3:
                    found = True
                    break
            if found:
                score = sum(self.dice)                            
        elif (category_type is CategoryType.FOUR_OF_A_KIND):
            # If there are four of a kind, the score is equal to the sum of all five dice.
            found = False
            for d in frequencies:
                if frequencies[d] >= 4:
                    found = True
                    break
            if found:
                score = sum(self.dice)
        elif category_type is CategoryType.FULL_HOUSE:
            # A full house is worth 25 points.
            if 2 in frequencies.values() and 3 in frequencies.values():
                score = 25
        elif category_type is CategoryType.SMALL_STRAIGHT:
            # A small straight is worth 30 points.                        
            if {1,2,3,4} <= set(self.dice):
                score = 30
            elif {2,3,4,5} <= set(self.dice):
                score = 30
            elif {3,4,5,6} <= set(self.dice):
                score = 30

        elif category_type is CategoryType.LARGE_STRAIGHT:
            # A large straight is worth 40 points.
            if {1,2,3,4,5} <= set(self.dice):
                score = 40
            elif {2,3,4,5,6} <= set(self.dice):
                score = 40
        elif category_type is CategoryType.YAHTZEE:
            # Five of a kind.  A Yahtzee is worth 50 points.
            if 5 in frequencies.values():
                score = 50
        elif category_type is CategoryType.CHANCE:
            # Sum of all five dice.
            score = sum(self.dice)                   

        game = self.game.get()
        game.has_unscored_roll = False
        game.put()

        return ScoreRollResultForm(score=score)

    def totalOf(self, value):
        score = 0
        for d in self.dice:
            if d is value:
                score += d
        return score

# Forms/Messages

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
