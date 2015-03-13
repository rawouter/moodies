import json
import logging
import pusherclient
import sys
import time

# Configuration
# TODO: Move this out in other files
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
        pusher_channel.bind('client-button_pushed', self._callback_button_pushed)

    def _callback_joining_member(self, msg):
        #2015-03-11 22:35:27,217 - pusherclient.connection - INFO - Connection: Message -
        #{"event":"pusher_internal:member_added","data":"{\"user_info\": {\"name\": \"Mr Wouters\"},
        #        \"user_id\": \"rawouter\"}","channel":"presence-moodies"}
        msg = json.loads(msg)
        self.logger.info('{} entering'.format(msg['user_id']))

    def _callback_leaving_member(self, msg):
        #2015-03-11 22:35:36,698 - pusherclient.connection - INFO - Connection: Message -
        #{"event":"pusher_internal:member_removed","data":"{\"user_id\":\"rawouter\"}","channel":"presence-moodies"}
        self.logger.info('Leaving member')

    def _callback_button_pushed(self, msg):
        self.logger.info('button_pushed event')
        self.logger.debug(msg)

class MoodiesChannel:
    def __init__(self, pusher_channel):
        self.logger = logging.getLogger('moodies.MoodiesChannel')
        self.pusher_channel = pusher_channel
        self.name = pusher_channel.name
        self.mood = Mood()

class Mood:
    def __init__(self):
        self.excited = 0
        self.nervous = 0

def start_logging():
    module_logger = logging.getLogger()
    module_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s.%(lineno)d - %(levelname)s - %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    module_logger.addHandler(ch)

def main():
    start_logging()
    server = MoodiesServer()
    server.run_forever()

if __name__=='__main__':
    main()
