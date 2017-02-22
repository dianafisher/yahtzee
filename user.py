from protorpc import messages
from google.appengine.ext import ndb

"""
user.py - This file contains the class definitions for the User entity.
"""


class User(ndb.Model):
    """ User object """
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    high_score = ndb.IntegerProperty(default=0)
    total_played = ndb.IntegerProperty(default=0)

    def to_form(self):
        """Returns a UserForm representation of the User
        """
        form = UserForm(urlsafe_key=self.key.urlsafe(),
                        user_name=self.name,
                        email=self.email,
                        total_played=self.total_played,
                        high_score=self.high_score)
        return form

    def add_score(self, score):
        self.total_played += 1
        if score > self.high_score:
            self.high_score = score

        self.put()


# Forms

class UserForm(messages.Message):
    """UserForm for outbound user information
    """
    urlsafe_key = messages.StringField(1, required=True)
    user_name = messages.StringField(2, required=True)
    email = messages.StringField(3, required=True)
    total_played = messages.IntegerField(4, required=True)
    high_score = messages.IntegerField(5, required=True)


class UserForms(messages.Message):
    """Form to return a list of all users
    """
    users = messages.MessageField(UserForm, 1, repeated=True)
