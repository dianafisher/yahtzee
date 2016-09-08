import endpoints
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

class ScoreCard(ndb.Model):
    """ScoreCard object"""
    user = ndb.KeyProperty(required=True, kind='User')
    game = ndb.KeyProperty(required=True, kind='Game')
    upper_section_total = ndb.IntegerProperty(default=0)
    bonus_points = ndb.IntegerProperty(default=0)
    is_full = ndb.BooleanProperty(required=True, default=False)
    category_scores = ndb.PickleProperty(required=True)
    total_score = ndb.IntegerProperty(default=0)
    yahzee_bonus_count = ndb.IntegerProperty(default=0)

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

    def calculate_score_for_category(self, dice, category):
        # Maintain a frequency table of dice values
        frequencies = {}
        for d in dice:
            if d in frequencies:
                count = frequencies[d]
                count += 1
                frequencies[d] = count
            else:
                frequencies[d] = 1

        score = 0
        if (category is CategoryType.ACES):
            # Total of ones only
            score = self.totalOf(1, dice)            
            
        elif (category is CategoryType.TWOS):
            # Total of twos only
            score = self.totalOf(2, dice)

        elif (category is CategoryType.THREES):
            # Total of threes only
            score = self.totalOf(3, dice)            

        elif (category is CategoryType.FOURS):
            # Total of fours only
            score = self.totalOf(4, dice)            

        elif (category is CategoryType.FIVES):
            # Total of fives only
            score = self.totalOf(5, dice)            

        elif (category is CategoryType.SIXES):
            # Total of sixes only
            score = self.totalOf(6, dice)            

        elif (category is CategoryType.THREE_OF_A_KIND):            
            # If there are three of a kind, the score is equal to the sum of all five dice.
            found = False
            for d in frequencies:
                if frequencies[d] >= 3:
                    found = True
                    break
            if found:
                score = sum(dice)        

        elif (category is CategoryType.FOUR_OF_A_KIND):            
            # If there are four of a kind, the score is equal to the sum of all five dice.
            found = False
            for d in frequencies:
                if frequencies[d] >= 4:
                    found = True
                    break
            if found:
                score = sum(dice)

        elif category is CategoryType.FULL_HOUSE:            
            # A full house is worth 25 points.
            if 2 in frequencies.values() and 3 in frequencies.values():
                score = 25

        elif category is CategoryType.SMALL_STRAIGHT:            
            # A small straight is worth 30 points.                                
            if {1,2,3,4} <= set(dice):
                score = 30
            elif {2,3,4,5} <= set(dice):
                score = 30
            elif {3,4,5,6} <= set(dice):
                score = 30

        elif category is CategoryType.LARGE_STRAIGHT:            
            # A large straight is worth 40 points.
            if {1,2,3,4,5} <= set(dice):
                score = 40
            elif {2,3,4,5,6} <= set(dice):
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
            score = sum(dice)     

        return score              

        # self.category_scores[str(category)] = score        

        # """ If a player scores a total of 63 or more points in the 
        # upper section, a bonus of 35 points is added to the upper section score. """
                
        # self.upper_section_total = self.calculateUpperSectionTotal()  

        # if self.upper_section_total >= 63:
        #     self.bonus_points = 35  
                
        # """Check to see if the game is now over"""
        # self.is_full = self.check_is_full()

        # """Calculate the total score"""
        # self.total_score = self.calculate_total_score()
        
        # # Save the updated scorecard values.
        # self.put()

    def calculateUpperSectionTotal(self):
        """Calculates total of scores in upper section.  
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

    def check_is_full(self):        
        for key in self.category_scores:            
            if self.category_scores[key] == -1:
                return False
        return True

    def calculate_total_score(self):
        total = 0
        for key in self.category_scores:
                total += self.category_scores[key]
        
        total += self.bonus_points
        return total

    def totalOf(self, value, dice):
        score = 0
        for d in dice:
            if d is value:
                score += d
        return score

    def to_form(self):
        return ScoreCardForm(            
            upper_section_total=self.upper_section_total,
            bonus_points = self.bonus_points,
            category_scores=str(self.category_scores),            
            is_full = self.is_full
        )
            

class ScoreCardRequestForm(messages.Message):
    """Used to request the user's scorecard"""
    user_name = messages.StringField(1, required=True)    

class ScoreCardForm(messages.Message):
    """Used to return the user's scorecard"""    
    upper_section_total = messages.IntegerField(1, required=True)
    bonus_points = messages.IntegerField(2, required=True)
    category_scores = messages.StringField(3, required=True)
    is_full = messages.BooleanField(4, required=True)    

class ScoreRollForm(messages.Message):
    category_type = messages.EnumField('CategoryType', 1)
    using_joker_rules = messages.BooleanField(2)


