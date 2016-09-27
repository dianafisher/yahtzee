import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

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

class Game(ndb.Model):
    """ Game object """
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    history = ndb.PickleProperty(required=True)
    has_incomplete_turn = ndb.BooleanProperty(required=True)
    turn_count = ndb.IntegerProperty(required=True, default=0)

    upper_section_total = ndb.IntegerProperty(default=0)
    bonus_points = ndb.IntegerProperty(default=0)
    category_scores = ndb.PickleProperty(required=True)
    final_score = ndb.IntegerProperty(default=0)
    yahtzee_bonus_count = ndb.IntegerProperty(default=0)

    dice = ndb.PickleProperty(required=True)        
    roll_count = ndb.IntegerProperty(required=True, default=0)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        game = Game(user=user)
        game.history = {}
        game.turn_count = 0
        game.has_incomplete_turn = False
        game.dice = []

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
        game.category_scores = scores

        game.put()
        return game

    def to_form(self):
        """Returns a GameForm representation of the Game"""
        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        user_name=self.user.get().name,
                        game_over=self.game_over,
                        turn_count=self.turn_count,
                        has_incomplete_turn=self.has_incomplete_turn,
                        upper_section_total=self.upper_section_total,
                        bonus_points=self.bonus_points,
                        category_scores=str(self.category_scores),
                        yahtzee_bonus_count=self.yahtzee_bonus_count,
                        final_score = self.final_score,
                        dice=self.dice,
                        roll_count=self.roll_count,
                        history=str(self.history))
        return form

    def can_roll(self):
        return self.roll_count > 0

    def roll_again(self, keepers):
        self.roll_count += 1
        # Choose a random number between 1 and 6 for each die that is not marked as a 'keeper'
        for i in range(5):
            if keepers[i] == 0:
                value = random.choice(range(1, 7))
                self.dice[i] = value
                print value
        
        # Update the game history.        
        entry = (self.roll_count, self.dice)
        if self.turn_count not in self.history :
            self.history[self.turn_count] = []        
        self.history[self.turn_count].append(entry)

        # Save changes
        self.put()

        # Return GameForm
        return self.to_form()

    def roll_dice(self):    
        """Rolls the dice for a new turn.  Must score any previous turn before calling this method."""        
        self.roll_count += 1
        # This method marks the beginning of a new turn.
        self.turn_count += 1    
        self.has_incomplete_turn = True

        # Choose a random number between 1 and 6 for each die       
        for i in range(5):
            value = random.choice(range(1, 7))
            self.dice.append(value)
            print value
       
        # Update the game history.
        entry = (self.roll_count, self.dice)           
        if self.turn_count not in self.history :
            self.history[self.turn_count] = []        
        self.history[self.turn_count].append(entry)

        # Save changes
        self.put()

        # Return GameForm
        return self.to_form()


    def score_roll(self, category):
        frequencies = {}
        for d in self.dice:
            if d in frequencies:
                count = frequencies[d]
                count += 1
                frequencies[d] = count
            else:
                frequencies[d] = 1
    
        score = 0
        if (category is CategoryType.ACES):
            # Total of ones only
            score = self.totalOf(1)            

        elif (category is CategoryType.TWOS):
            # Total of twos only
            score = self.totalOf(2)

        elif (category is CategoryType.THREES):
            # Total of threes only
            score = self.totalOf(3)

        elif (category is CategoryType.FOURS):
            # Total of fours only
            score = self.totalOf(4)

        elif (category is CategoryType.FIVES):
            # Total of fives only
            score = self.totalOf(5)

        elif (category is CategoryType.SIXES):
            # Total of sixes only
            score = self.totalOf(6)

        elif (category is CategoryType.THREE_OF_A_KIND):
            # If there are three of a kind, the score is equal to the sum of
            # all five dice.
            found = False
            for d in frequencies:
                if frequencies[d] >= 3:
                    found = True
                    break
            if found:
                score = sum(self.dice)

        elif (category is CategoryType.FOUR_OF_A_KIND):
            # If there are four of a kind, the score is equal to the sum of all
            # five dice.
            found = False
            for d in frequencies:
                if frequencies[d] >= 4:
                    found = True
                    break
            if found:
                score = sum(self.dice)

        elif category is CategoryType.FULL_HOUSE:
            # A full house is worth 25 points.
            if 2 in frequencies.values() and 3 in frequencies.values():
                score = 25

        elif category is CategoryType.SMALL_STRAIGHT:
            # A small straight is worth 30 points.
            if {1, 2, 3, 4} <= set(self.dice):
                score = 30
            elif {2, 3, 4, 5} <= set(self.dice):
                score = 30
            elif {3, 4, 5, 6} <= set(self.dice):
                score = 30

        elif category is CategoryType.LARGE_STRAIGHT:
            # A large straight is worth 40 points.
            if {1, 2, 3, 4, 5} <= set(self.dice):
                score = 40
            elif {2, 3, 4, 5, 6} <= set(self.dice):
                score = 40

        elif category is CategoryType.YAHTZEE:
            # Five of a kind.  A YAHTZEE is worth 50 points.

            # Check to make sure all dice are the same.
            is_Yahztee = (5 in frequencies.values())

            """If the user rolls YAHTZEE and has already filled in the 
            YAHZTEE box with 50, they get a 100-point bonus.
            If they have already filled in the YAHTZEE box with 0, 
            they do not get a bonus."""

            # Has a score already been entered for the YAHTZEE category?
            current_score = self.category_scores[str(category)]
            if current_score == -1:
                # No score has been entered yet, so score normally.
                if is_Yahztee:
                    score = 50
                else:
                    score = 0

            elif current_score == 50:
                """A score of 50 has already been entered, 
                so increase the YAHTZEE bonus conut."""
                self.yahzee_bonus_count += 1

        elif category is CategoryType.CHANCE:
            # Sum of all five dice.
            score = sum(self.dice)

        self.category_scores[str(category)] = score

        # Mark the turn complete
        self.has_incomplete_turn = False
        # Reinitialize items for next turn.
        self.roll_count = 0
        self.dice = []
        # Save game
        self.put()

        return self.to_form()


    def calculateUpperSectionTotal(self):
        """Returns total of scores in upper section.  
        Ignores values less than zero."""

        total = 0
        if self.category_scores['ACES'] != -1:
            total += self.category_scores['ACES']
        if self.category_scores['TWOS'] != -1:
            total += self.category_scores['TWOS']
        if self.category_scores['THREES'] != -1:
            total += self.category_scores['THREES']
        if self.category_scores['FOURS'] != -1:
            total += self.category_scores['FOURS']
        if self.category_scores['FIVES'] != -1:
            total += self.category_scores['FIVES']
        if self.category_scores['SIXES'] != -1:
            total += self.category_scores['SIXES']

        return total        

    def totalOf(self, value):
        """
        Returns the sum of dice of a given value.
        For example, if dice = [1,3,5,3,4] and value = 3, 
        then 6 (3+3) is returned.
        """
        score = 0
        for d in self.dice:
            if d is value:
                score += d
        return score

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
    upper_section_total = messages.IntegerField(6, required=True)
    bonus_points = messages.IntegerField(7, required=True)
    category_scores = messages.StringField(8, required=True)
    yahtzee_bonus_count = messages.IntegerField(9, required=True)
    final_score = messages.IntegerField(10, required=True)
    dice = messages.IntegerField(11, repeated=True)
    roll_count = messages.IntegerField(12, required=True)
    history = messages.StringField(13, required=True) 

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

class ScoreRollForm(messages.Message):
    category_type = messages.EnumField('CategoryType', 1)        
