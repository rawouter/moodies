from functools import partial
import json
import logging
import sys
import time
import types

import pusherclient

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
        self.users = {}

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

    def _callback_default(self, msg):
        self.logger.debug("!!! DEFAULT PUSHER EVENT HANDLER !!! {} - {}".format(channel_name, msg))


    def _setup_config_channel_callbacks(self, pusher_channel_config):
        """
        Configure the config channel callbacks
        """
        pass

    def _setup_mood_channels_callbacks(self, pusher_channel):
        """
        Configure the private-* moodies channel callbacks
        """
        cjm = partial(self._callback_joining_member, channel_name = pusher_channel.name)
        pusher_channel.bind('pusher_internal:member_added', cjm)
        clm = partial(self._callback_leaving_member, channel_name = pusher_channel.name)
        pusher_channel.bind('pusher_internal:member_removed', clm)
        bp = partial(self._callback_button_pushed, channel_name = pusher_channel.name)
        pusher_channel.bind('client-button-pushed', bp)


    def _callback_joining_member(self, msg, channel_name):
        """
        Create a new MoodiesUser and store it for the first time we see the user.
        Append the user to the channel list of users.
        """
        message = Message(msg)
        self.logger.info('{} entering {}'.format(message.user_id, channel_name))
        if message.user_id not in self.users.keys():
            self.users[message.user_id] = MoodiesUser(message.user_id)
        if self.users[message.user_id] not in self.channels[channel_name].users:
            self.channels[channel_name].users.append(self.users[message.user_id])

    def _callback_leaving_member(self, msg, channel_name):
        """
        Remove users from channel users list.
        """
        message = Message(msg)
        self.logger.info('{} left {}'.format(message.user_id, channel_name))
        self.channels[channel_name].users.remove(self.users[message.user_id])

    def _callback_button_pushed(self, msg, channel_name):
        message = Message(msg)
        self.logger.info('{} pushed the button'.format(message.user_id))
        self.logger.debug(message.value)
        # Hardocding values for now, MVP. We could have a config file/DB later for that.
        # Arduino happy
        if message.value == int('0b10', 2):
            self._is_happy(message.user_id, channel_name)
        # Arduino unhappy
        elif message.value == int('0b100000', 2):
            self._is_nervous(message.user_id, channel_name)

    def _is_happy(self, user_id, channel_name):
        moods = self.users[user_id].moods
        moods.increase(moods.happy)
        self.send_text(channel_name, user_id, '{} is happy'.format(user_id))
        self.channels[channel_name].recompute_mood()

    def _is_nervous(self, user_id, channel_name):
        moods = self.users[user_id].moods
        moods.increase(moods.nervous)
        self.send_text(channel_name, user_id, '{} is nervous'.format(user_id))
        self.channels[channel_name].recompute_mood()

    def send_text(self, channel_name, user_id, text):
        #TODO
        pass

class MoodiesUser:

    """
    User class, store Mood per users
    """

    def __init__(self, user_id):
        self.user_id = user_id
        self.moods_container = MoodsContainer()
        self.top_mood = self.moods_container.moods['default']

    def compute_top_mood(self):
        self.top_mood = self.moods_container.compute_top_mood()
        return self.top_mood


class MoodiesChannel:

    """
    Channel class representing a chat room (pusher channel) and it's moods (MoodsContainer class)
    """

    def __init__(self, pusher_channel):
        self.logger = logging.getLogger('moodies.MoodiesChannel')
        self.pusher_channel = pusher_channel
        self.name = pusher_channel.name
        self.moods_container = MoodsContainer()
        self.current_mood = self.moods_container.moods['default']
        self.users = []

    def recompute_mood(self):
        moods = self.moods_container.moods
        for mood_name, mood in moods.iteritems():
            mood.value = 0
            if not len(self.users):
                continue # We just reset moods to 0 if there are no more users
            for user in self.users:
                mood.value += user.moods_container.moods[mood_name].value
            mood.value = mood.value / len(self.users)
        self.current_mood = self.moods_container.compute_top_mood()


class Mood:
    """
    Contains a mood parameters
    """

    def __init__(self, name, value, color):
        self.name = name
        self.value = value
        self.color = color

class MoodsContainer:

    """
    Contains Mood values
    """

    def __init__(self):
        self.moods = {
            'default': Mood('', 0, '000000'),
            'excited': Mood('excited', 0, '00FF00'),
            'nervous': Mood('nervous', 0, 'FF0000')
        }

    def decrease_all_moods(self, val):
        for key in self.moods:
            self.decrease(key, val)

    def decrease(self, mood_name, val=20):
        if self.moods[mood_name].value > val:
            self.moods[mood_name].value -= val
        else:
            self.moods[mood_name].value = 0

    def increase(self, mood_name, val=20):
        if self.moods[mood_name].value < (100-val):
            self.moods[mood_name].value += val
        else:
            self.moods[mood_name].value = 100

    def compute_top_mood(self):
        top_mood = self.moods['default']
        max = 0
        for mood_name, mood in self.moods.iteritems():
            if mood.value > max:
                top_mood = mood
                max = mood.value
        return top_mood


class Message:

    """
    Parse a the json string received in pusher message data
    """

    def __init__(self, msg):
        assert type(msg) in types.StringTypes, 'Message instance did not receive a String'
        msg = json.loads(msg)
        self.value = self._get_json_val('value', msg)
        self.user_id = self._get_json_val('user_id', msg)

    def _get_json_val(self, key, json_msg):
        if key in json_msg:
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
