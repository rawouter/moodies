from functools import partial
import logging
import pusherclient
import sys
import time

"""
This example show how to use pusherclient to connect to the moodies pusher channel
It's essentially a listener that will print known events to stdout.

It has a function to send a button pushed event (send_button_pushed) but we don't
use it to not garbage the presence-moodies channel at every run
"""

# These credentials will move in the future, 'presence-moodies' is is just a test channel
app_key = '2c987384b72778026687'
secret = '8440acd6ba1e0bfec3d4'
user_data = {
  'user_id': 'clienttester',
  'user_info': {
      'name': 'Mr Nobody'
    }
}

logger = logging.getLogger('client-example') # configure global logger to see pusherclient debugs

def connect_to_pusher():
    """
    Main function making the connection to pusher, and configuring the first callback once connected, because
    we can not subscribe to a channel before being connected
    """
    logger.debug('Connecting to pusher')
    pusher_client = pusherclient.Pusher(app_key, secret=secret, user_data=user_data)
    pusher_client.connection.bind(
        'pusher:connection_established',
        partial(callback_connection_made, pusher_client=pusher_client)
    )
    pusher_client.connect()

def callback_connection_made(data, pusher_client):
    """
    Function called back once connected to pusher.
    It connects to the channel then configure the callbacks for the channel events
    """
    logger.debug('Connection to pusher made')
    pusher_channel = pusher_client.subscribe('presence-moodies')
    configure_channel_callbacks(pusher_channel)

def configure_channel_callbacks(pusher_channel):
    """
    Bind events to callback functions
    """
    logger.debug('Configuring callbacks')
    pusher_channel.bind('pusher_internal:member_added', callback_joining_member)
    pusher_channel.bind('pusher_internal:member_removed', callback_leaving_member)
    pusher_channel.bind('client-new-color', callback_color)
    pusher_channel.bind('client-text-message', callback_text)
    pusher_channel.bind('client-play-melody', callback_melody)

def callback_joining_member(msg):
    logger.info('%% Member joined channel - {}'.format(msg))

def callback_leaving_member(msg):
    logger.info('%% Member left - {}'.format(msg))

def callback_color(msg):
    logger.info('%% Received new color: {}'.format(msg))

def callback_text(msg):
    logger.info('%% Received text message: {}'.format(msg))

def callback_melody(msg):
    logger.info('%% Received melody: {}'.format(msg))

def send_button_pushed(pusher_channel):
    """
    Send a button pushed event
    """
    pusher_channel.trigger('client-button-pushed', {'value': 2, 'user_id': user_data['user_id']})
    logging.info('send button_pushed')

def configure_logger(args):
    logger.setLevel(args.loglevel)
    formatter = logging.Formatter('%(asctime)s - [%(levelname)8s] %(name)s.%(lineno)d --- %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description='Moodies client example using the pusherclient library'
    )
    parser.add_argument('-d', '--debug',
        help='Setup debug loging',
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
        default=logging.INFO
    )
    args = parser.parse_args()
    return args

def sleep_forever():
    while True:
        # You can do useful things here
        # The whole pusher connection is managed by callbacks
        time.sleep(1)

if __name__=='__main__':
    args = parse_args()
    configure_logger(args)
    connect_to_pusher()
    sleep_forever()
