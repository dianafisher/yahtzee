import random
from protorpc import messages
from google.appengine.ext import ndb


class Turn(ndb.Model):
    """Turn object"""
    game = ndb.KeyProperty(required=True, kind='Game')
    number = ndb.IntegerProperty(required=True, default=0)
    dice = ndb.PickleProperty(required=True)
    roll_count = ndb.IntegerProperty(required=True, default=0)
    is_complete = ndb.BooleanProperty(required=True, default=False)

    @classmethod
    def new_turn(cls, game, number):
        """Creates a new turn for a game and rolls the dice."""
        turn = Turn(game=game, number=number)

        # Create an array for the dice
        turn.dice = []

        # Choose a random number between 1 and 6 for each die
        for i in range(5):
            value = random.choice(range(1, 7))
            turn.dice.append(value)
            print value

        turn.roll_count = 1
        turn.put()
        return turn

    def to_form(self):
        return TurnForm(urlsafe_key=self.key.urlsafe(),
                        number=self.number,
                        dice=self.dice,
                        roll_count=self.roll_count,
                        is_complete=self.is_complete)

    def roll_dice(self, keepers):

        self.roll_count += 1

        """Choose a random number between 1 and 6 for
        each die that is not marked as a 'keeper'"""

        for i in range(5):
            if keepers[i] == 0:
                value = random.choice(range(1, 7))
                self.dice[i] = value
                print value

        self.put()

        # Update the game history.
        game = self.game.get()
        entry = (self.roll_count, self.dice)
        game.history[self.number].append(entry)
        # # Save the game history.
        game.put()

        return self.to_form()


class TurnForm(messages.Message):
    urlsafe_key = messages.StringField(1, required=True)
    number = messages.IntegerField(2, required=True)
    dice = messages.IntegerField(3, repeated=True)
    roll_count = messages.IntegerField(4, required=True)
    is_complete = messages.BooleanField(5, required=True)