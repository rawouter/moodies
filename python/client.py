import logging
import pusherclient
import sys
import time

app_key = '2c987384b72778026687'
secret = '8440acd6ba1e0bfec3d4'
user_data = {
  'user_id': 'rawouter',
  'user_info': {
      'name': 'Mr Wouters'
    }

}

# Logging handler
root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
root.addHandler(ch)

global pusher

# We can't subscribe until we've connected, so we use a callback handler
# to subscribe when able
def connect_handler(data):
    channel = pusher.subscribe('presence-moodies')
    time.sleep(1)
    channel.trigger('client-button-pushed', {'value': 2, 'user_id': user_data['user_id']})
    logging.info('send button_pushed')

pusher = pusherclient.Pusher(app_key, secret=secret, user_data=user_data)
pusher.connection.bind('pusher:connection_established', connect_handler)
pusher.connect()

time.sleep(30)
