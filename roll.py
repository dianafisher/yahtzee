import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

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
    
    def to_form(self):
        return RollResultForm(urlsafe_key=self.key.urlsafe(),
                              user_name=self.user.get().name,
                              dice=self.dice,
                              count=self.count,
                              isScored=self.isScored
                              )
    

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


class ScoreRollResultForm(messages.Message):
    score = messages.IntegerField(1, required=True)
