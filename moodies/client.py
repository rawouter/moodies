from functools import partial
import logging
import pusherclient
import sys
import time

"""
Client functionalities to have moodies appliance connect to a specific pusher channel
This is mainly a wrapper to abstract pusherclient library
"""

logger = logging.getLogger('moodies.client') # configure global logger to see pusherclient debugs
logging.getLogger().addHandler(logging.NullHandler())

class MoodiesClient:

    def __init__(self, appkey, secret, channel):
        """
        :param appkey: pusher appkey
        :param secret: pusher secret
        :param channel: pusher channel to join
        """
        self.appkey = appkey
        self.secret = secret
        self.channel_name = channel
        self.connected = False
        self.pusher_client = None

    def _start_logger(self):
        formatter = logging.Formatter('[%(levelname)8s] %(name)s.%(lineno)d --- %(message)s')
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    def connect(self, user_id, user_name, callback):
        """
        Main function making the connection to pusher, and configuring the first callback so we can configure
        the channel connection

        :param user_id: the User ID of the connecting user
        :param usern_name: the User name of the connecting user
        :param callback: function to call back once connected
        """
        logger.debug('Connecting to pusher')
        user_data = {
          'user_id': user_id,
          'user_info': {
              'name': user_name
            }
        }
        self.pusher_client = pusherclient.Pusher(self.appkey, secret=self.secret, user_data=user_data)
        self.pusher_client.connection.bind(
            'pusher:connection_established',
            partial(
                self._callback_connection_made,
                callback=callback
            )
        )
        self.pusher_client.connect()

    def disconnect(self):
        """
        Disconnect from pusher
        """
        if self.connected:
            self.pusher_client.disconnect()
            self.connected = False

    def _callback_connection_made(self, data, callback):
        """
        Function called back once connected to pusher.
        It connects to the channel then configure the callbacks for the channel events

        :param data: Data sent by pusherclient callback, unused
        :param callback: Function to callback (useful for consumer to bing other event callbacks)
        """
        logger.debug('Connection to pusher made')
        self.pusher_client.subscribe(self.channel_name)
        logger.debug('Channel {} joined'.format(self.channel_name))
        self.connected = True
        callback(self)

    def _get_pusher_channel(self):
        """
        Return the pusher channel we are connected to

        :returns: pusherclient.Channel
        """
        return self.pusher_client.channels[self.channel_name]

    def bind_callback_joining_member(self, func):
        """
        Callback for joining member

        :param func: function to call back
        """
        self.bind_callback('pusher_internal:member_added', func)

    def bind_callback_leaving_member(self, func):
        """
        Callback for leaving member

        :param func: function to call back
        """
        self.bind_callback('pusher_internal:member_removed', func)

    def bind_callback(self, event, callback):
        """
        Bind moodies event to callback functions

        :param event: The event as defined in moodies.events
        :callback event: The callback function
        """
        pusher_channel = self._get_pusher_channel()
        logger.debug('Configuring callbacks for {}'.format(event))
        pusher_channel.bind(event, callback)

    def send_event(self, event, message):
        """
        Send a event in pusher Channel

        :param event: The event (should be as defined in moodies.events)
        :type event: str
        :param message: Message to send
        :type message: moodies.message.Message

        :returns: True if the message was sent, False otherwise
        :rtype: bool
        """
        if self.connected:
            self._get_pusher_channel().trigger(
                event,
                message.to_dict()
            )
            return True
        else:
            return False

if __name__=='__main__':
    import os
    import time
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    import config
    import events

    logger.setLevel(logging.DEBUG)
    client = MoodiesClient(config.appkey, config.secret, config.connected_channels[0])
    client._start_logger()

    def print_callback(data, text):
        logger.info('Callback for {}: {}'.format(text, data))
    def gen_callback(text):
        return partial(
            print_callback,
            text=text
        )
    def callback_connected(client):
        logger.debug('Configuring all callbacks')
        client.bind_callback_joining_member(gen_callback('Joining member'))
        client.bind_callback_leaving_member(gen_callback('Leaving member'))
        client.bind_callback(events.COLOR, gen_callback('New color'))
        client.bind_callback(events.TEXT, gen_callback('Text message'))
        client.bind_callback(events.MELODY, gen_callback('Play melody'))


    client.connect('testclient', 'M. Test Moddies Client', callback_connected)

    while True:
        time.sleep(60)
