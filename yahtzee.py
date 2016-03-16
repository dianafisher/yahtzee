"""
yahtzee.py - Create and configure the game API.

"""
__author__ = 'diana.fisher@gmail.com (Diana Fisher)'

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from google.appengine.ext import ndb

from models import User, Game, Score
from models import StringMessage

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# @endpoints.api( name='yahtzee',
#                 version='v1',
#                 allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
#                 scopes=[EMAIL_SCOPE])

@endpoints.api( name='yahtzee', version='v1' )
class YahtzeeApi(remote.Service):
    """Yahtzee API v0.1"""
    
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))


# registers API
api = endpoints.api_server([YahtzeeApi])         