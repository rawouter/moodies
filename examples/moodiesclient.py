from functools import partial
import logging
import pusherclient
import sys
import time

"""
This example show how to use pusherclient to connect to the moodies pusher channel
It can be used from CLI to listen to channel
Or it can be used from CLI to send an event

"""

# These credentials will move in the future, 'presence-moodies' is is just a test channel
APPKEY = '2c987384b72778026687'
SECRET = '8440acd6ba1e0bfec3d4'
CHANNEL_NAME = 'presence-moodies'

logger = logging.getLogger('client-example') # configure global logger to see pusherclient debugs
logging.getLogger().addHandler(logging.NullHandler())

def connect_to_pusher(args):
    """
    Main function making the connection to pusher, and configuring the first callback once connected, because
    we can not subscribe to a channel before being connected
    """
    logger.debug('Connecting to pusher')
    user_data = {
      'user_id': args.user_id,
      'user_info': {
          'name': 'Mr Nobody from moodiesclient.py'
        }
    }
    pusher_client = pusherclient.Pusher(APPKEY, secret=SECRET, user_data=user_data)
    pusher_client.connection.bind(
        'pusher:connection_established',
        partial(callback_connection_made, pusher_client=pusher_client)
    )
    pusher_client.connect()
    return pusher_client

def callback_connection_made(data, pusher_client):
    """
    Function called back once connected to pusher.
    It connects to the channel then configure the callbacks for the channel events
    """
    logger.debug('Connection to pusher made')
    pusher_channel = pusher_client.subscribe(CHANNEL_NAME)
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

def send_event(pusher_client, pusher_channel_name, event, value, user_id):
    """
    Send a button pushed event
    """
    pusher_client.channels[pusher_channel_name].trigger(
        event,
        {'value': value, 'user_id': user_id}
    )

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
    parser.add_argument('event',
        metavar='EVENT',
        type=str,
        default='sniff',
        nargs='?',
        help='Event to be send, if no event is provided we will enter in "sniffing" mode'
    )
    parser.add_argument('-u', '--userid',
        help='UserID to be sent',
        action='store',
        dest='user_id',
        default='moodies_client'
    )
    parser.add_argument('-v', '--value',
        help='Value for the EVENT sent',
        action='store',
        dest='value',
        default=''
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
        # You can do useful things here, the whole pusher connection is managed by callbacks
        time.sleep(60)

if __name__=='__main__':
    args = parse_args()
    configure_logger(args)
    pusher_client = connect_to_pusher(args)
    if args.event == 'sniff':
        sleep_forever()
    else:
        def send_button_pushed(data):
            import sys
            send_event(pusher_client, CHANNEL_NAME, args.event, args.value, args.user_id)
            sys.exit(0)

        pusher_client.connection.bind(
            'pusher:connection_established',
            send_button_pushed
        )
        time.sleep(5)
        print 'Got a time out, not sure the event was sent'
