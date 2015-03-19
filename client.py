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
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)

global pusher

# We can't subscribe until we've connected, so we use a callback handler
# to subscribe when able
def connect_handler(data):
    channel = pusher.subscribe('presence-moodies')
    channel.bind('client-new-color', callback_color)
    channel.bind('client-text-message', callback_text)
    time.sleep(1)
    channel.trigger('client-button-pushed', {'value': 2, 'user_id': user_data['user_id']})
    logging.info('send button_pushed')

def callback_color(msg):
    logger.info('%% Received new color: {}'.format(msg))

def callback_text(msg):
    logger.info('%% Received text message: {}'.format(msg))

pusher = pusherclient.Pusher(app_key, secret=secret, user_data=user_data)
pusher.connection.bind('pusher:connection_established', connect_handler)
pusher.connect()

time.sleep(30)
