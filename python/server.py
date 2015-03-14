import json
import logging
from PythonPusherClient import pusherclient
import sys
import time
import types

# Configuration
APPKEY = '2c987384b72778026687'
SECRET = '8440acd6ba1e0bfec3d4'
CONNECTED_CHANNELS = ['presence-moodies']
USERDATA = {
  'user_id': 'moodies-server',
  'user_info': {
      'name': 'Moodies Server'
    }
}


class MoodiesServer:
    """
    Main server class, will connect to pusher, listen to messages, compute them and answer.
    """


    def __init__(self):
        self.logger = logging.getLogger('moodies.Server')
        self.killed = False
        self.pusher = pusherclient.Pusher(APPKEY, secret=SECRET, user_data=USERDATA)
        self.channels = {}

    def run_forever(self):
        """
        Establish the connection to Pusher and keep the MoodiesServer class
        alive until killed
        """
        self._connect_to_pusher()
        while not self.killed:
            time.sleep(1)

    def _connect_to_pusher(self):
        """
        Establish the connection to pusher, and configure the callback function
        once connected
        """
        self.pusher.connection.bind('pusher:connection_established', self._callback_connection_estabished)
        self.pusher.connection.bind('default', self._callback_default)
        self.pusher.connect()

    def _callback_connection_estabished(self, data):
        """
        Callback to subribe to channels when receiving pusher:connection_established,
        needed as we can't subscribe until we are connected.
        """
        pusher_channel_config = self.pusher.subscribe('moodies-client-config')
        self.channels['moodies-client-config'] = MoodiesChannel(pusher_channel_config)
        self._setup_config_channel_callbacks(pusher_channel_config)

        for c in CONNECTED_CHANNELS:
            self.channels[c] = MoodiesChannel(self.pusher.subscribe(c))
        for key, moodies_channel in self.channels.iteritems():
            self._setup_mood_channels_callbacks(moodies_channel.pusher_channel)

    def _callback_default(self, channel_name, msg):
        self.logger.debug("DEFAULT HANDLER: {} - {}".format(channel_name, msg))

    def _setup_config_channel_callbacks(self, pusher_channel_config):
        """
        Configure the config channel callbacks
        """
        pass

    def _setup_mood_channels_callbacks(self, pusher_channel):
        """
        Configure the private-* moodies channel callbacks
        """
        pusher_channel.bind('pusher_internal:member_added', self._callback_joining_member)
        pusher_channel.bind('pusher_internal:member_removed', self._callback_leaving_member)
        pusher_channel.bind('client-button-pushed', self._callback_button_pushed)

    def _callback_joining_member(self, channel_name, msg):
        message = Message(msg)
        self.logger.info('{} entering {}'.format(message.user_id, channel_name))

    def _callback_leaving_member(self, channel_name, msg):
        message = Message(msg)
        self.logger.info('{} left {}'.format(message.user_id, channel_name))

    def _callback_button_pushed(self, channel_name, msg):
        message = Message(msg)
        self.logger.info('{} pushed the button'.format(message.user_id))
        self.logger.debug(message.value)
        #self.channels[channel_name]


class MoodiesChannel:
    """
    Channel class representing a chat room (pusher channel) and it's mood (Mood class)
    """


    def __init__(self, pusher_channel):
        self.logger = logging.getLogger('moodies.MoodiesChannel')
        self.pusher_channel = pusher_channel
        self.name = pusher_channel.name
        self.mood = Mood()


class Mood:
    """
    Contains mood values
    """


    def __init__(self):
        self.excited = 0
        self.nervous = 0

    def decrease_all_moods(self):
        for key in vars(self):
            mood = self[key]
            assert type(mood) is types.IntType, 'Mood class has a non Integer variable: {}'.format(key)
            if mood > 0:
                mood -= 1

    def increase(self, mood_var):
        if mood_var < 100:
            mood_var += 1
        else:
            mood_var = 100


class Message:
    """
    Parse a json object
    """


    def __init__(self, msg):
        assert type(msg) in types.StringTypes, 'Message instance did not receive a String'
        msg = json.loads(msg)
        self.value = self._get_json_val('value', msg)
        self.user_id = self._get_json_val('user_id', msg)

    def _get_json_val(self, key, json_msg):
        if json_msg.has_key(key):
            return json_msg[key]
        else:
            return None


def start_logger():
    module_logger = logging.getLogger()
    module_logger.setLevel(logging.DEBUG)
    #formatter = logging.Formatter('%(asctime)s - %(name)s.%(lineno)d - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(levelname)s - %(name)s.%(lineno)d - %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    module_logger.addHandler(ch)

def main():
    start_logger()
    server = MoodiesServer()
    server.run_forever()

if __name__=='__main__':
    main()
