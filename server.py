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
SLEEPTIME = 2
MOOD_DECREASE_RATE = 5


class MoodiesServer:

    """
    Main server class, will connect to pusher, listen to messages, compute them and answer.
    """

    def __init__(self):
        self.logger = logging.getLogger('moodies.Server')
        self.logger.info('Starting Moodies server')
        self.killed = False
        self.pusher = pusherclient.Pusher(APPKEY, secret=SECRET, user_data=USERDATA)
        self.channels = {}
        self.users = {}
        self.user_id = USERDATA['user_id']

    def run_forever(self):
        """
        Establish the connection to Pusher and keep the MoodiesServer class
        alive until killed
        """
        self._connect_to_pusher()
        self.logger.info('Entering server loop')
        while not self.killed:
            time.sleep(SLEEPTIME)
            tic = time.time()
            for user_name, user in self.users.iteritems():
                user.moods_container.decrease_all_moods(MOOD_DECREASE_RATE)
                user.compute_top_mood()
            for channel_name, channel in self.channels.iteritems():
                if channel.recompute_mood():
                    self.send_color(channel, Message(self.user_id, channel.current_mood.color))
            # The above computations are O(n^m) but moods are limited (almost constant),
            # only users can grow without control. Yet, if this becomes too slow we'd need to rethink the
            # algorithm, but this should be enough for an MVP
            self.logger.debug('Update cycle duration: {}'.format(time.time() - tic))

    def _connect_to_pusher(self):
        """
        Establish the connection to pusher, and configure the callback function
        once connected
        """
        self.pusher.connection.bind('pusher:connection_established', self._callback_connection_estabished)
        self.pusher.connect()
        self.logger.info('Pusher connection established')


    def _callback_connection_estabished(self, data):
        """
        Callback to subribe to channels when receiving pusher:connection_established,
        needed as we can't subscribe until we are connected.
        """
        self.logger.debug('Callback pusher:connection_established - {}'.format(data))
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
        def gen_callback(fn):
            return partial(fn, channel_name = pusher_channel.name)
        pusher_channel.bind('pusher_internal:member_added', gen_callback(self._callback_joining_member))
        pusher_channel.bind('pusher_internal:member_removed', gen_callback(self._callback_leaving_member))
        pusher_channel.bind('client-button-pushed', gen_callback(self._callback_button_pushed))


    def _callback_joining_member(self, msg, channel_name):
        """
        Create a new MoodiesUser and store it for the first time we see the user.
        Append the user to the channel list of users.
        """
        self.logger.debug('Callback pusher_internal:member_added - {} - {}'.format(channel_name, msg))
        message = Message()
        message.feed_with_json(msg)
        self.logger.info('{} entering {}'.format(message.user_id, channel_name))
        if message.user_id not in self.users.keys():
            self.users[message.user_id] = MoodiesUser(message.user_id)
        if self.users[message.user_id] not in self.channels[channel_name].users:
            self.channels[channel_name].users.append(self.users[message.user_id])

    def _callback_leaving_member(self, msg, channel_name):
        """
        Remove users from channel users list.
        """
        self.logger.debug('Callback pusher_internal:member_removed - {} - {}'.format(channel_name, msg))
        message = Message()
        message.feed_with_json(msg)
        self.logger.info('{} left {}'.format(message.user_id, channel_name))
        self.channels[channel_name].users.remove(self.users[message.user_id])

    def _callback_button_pushed(self, msg, channel_name):
        self.logger.debug('Callback client-button-pushed - {} - {}'.format(channel_name, msg))
        message = Message()
        message.feed_with_json(msg)
        self.logger.info('{} pushed the button'.format(message.user_id))
        self.logger.debug(message.value)
        # Hardocding values for now, MVP. We could have a config file/DB later for that.
        # Arduino excited
        if message.value == int('0b10', 2):
            self._act_on_mood('excited', message.user_id, channel_name)
        # Arduino nervous
        elif message.value == int('0b100000', 2):
            self._act_on_mood('nervous', message.user_id, channel_name)

    def _act_on_mood(self, mood_name, user_id, channel_name):
        message = Message(self.user_id)
        channel = self.channels[channel_name]

        self.users[user_id].moods_container.increase(mood_name)
        if channel.recompute_mood():
            message.value = channel.current_mood.color
            self.send_color(channel, message)
        message.value = '{} is {}'.format(user_id, mood_name)
        self.send_text(channel, message)
        message.value = channel.current_mood.melody
        self.send_melody(channel, message)

    def send_color(self, moodies_channel, message):
        """
        Send a pusher client-new-color even in pusher channel
        """
        self.logger.debug('Sending new color in {} - {}'.format(moodies_channel.name, message.value))
        moodies_channel.pusher_channel.trigger('client-new-color', message.to_dict())

    def send_text(self, moodies_channel, message):
        """
        Send a pusher client-text-message even in pusher channel
        """
        self.logger.debug('Sending new text in {} - {}'.format(moodies_channel.name, message.value))
        moodies_channel.pusher_channel.trigger('client-text-message', message.to_dict())

    def send_melody(self, moodies_channel, message):
        """
        Send a pusher client-play-melody even in pusher channel
        """
        self.logger.debug('Sending new melody in {} - {}'.format(moodies_channel.name, message.value))
        moodies_channel.pusher_channel.trigger('client-play-melody', message.to_dict())

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
        """
        Recompute the current channel top mood
        Return True if the current mood changed
        """
        moods = self.moods_container.moods
        old_mood = self.current_mood
        for mood_name, mood in moods.iteritems():
            mood.value = 0
            if not len(self.users):
                continue # We just reset moods to 0 if there are no more users
            for user in self.users:
                mood.value += user.moods_container.moods[mood_name].value
            mood.value = mood.value / len(self.users)
        self.current_mood = self.moods_container.compute_top_mood()
        return old_mood.name is not self.current_mood.name


class Mood:
    """
    Contains a mood parameters
    """

    def __init__(self, name, value, color, melody=''):
        self.name = name
        self.value = value
        self.color = color
        self.melody = melody

class MoodsContainer:

    """
    Contains Mood values
    """

    def __init__(self):
        self.moods = {
            'default': Mood('noMood', 0, '000000'),
            'excited': Mood('excited', 0, '00FF00', '1c2g2p1c3g'),
            'nervous': Mood('nervous', 0, 'FF0000', '3e3d5c')
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

    def __init__(self, user_id=None, value=None):
        self.value = value
        self.user_id = user_id

    def feed_with_json(self, msg):
        assert type(msg) in types.StringTypes, 'Message instance did not receive a String'
        msg = json.loads(msg)
        self.value = self._get_json_val('value', msg)
        self.user_id = self._get_json_val('user_id', msg)

    def to_dict(self):
        return {
                'value': self.value
                , 'user_id': self.user_id
        }

    def _get_json_val(self, key, json_msg):
        if key in json_msg:
            return json_msg[key]
        else:
            return None


def start_logger(args):
    module_logger = logging.getLogger('moodies')
    #formatter = logging.Formatter('%(asctime)s - %(name)s.%(lineno)d - %(levelname)s - %(message)s')
    formatter = logging.Formatter('[%(levelname)8s] %(name)s.%(lineno)d --- %(message)s')
    ch = logging.StreamHandler(sys.stdout)

    ch.setFormatter(formatter)
    module_logger.addHandler(ch)

    module_logger.setLevel(args.loglevel)

    # Disable all other logging spurious messages "No handler for"
    logging.getLogger().addHandler(logging.NullHandler())


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description='Moodies server listening to Pusher message and acting on them'
    )
    parser.add_argument('-d', '--debug',
        help='Setup debug loging',
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
        default=logging.WARNING
    )
    parser.add_argument('-v','--verbose',
        help='Setup verbose loging (less than debug)',
        action='store_const',
        dest='loglevel',
        const=logging.INFO
    )
    args = parser.parse_args()
    return args

def main():
    server = MoodiesServer()
    server.run_forever()

if __name__=='__main__':
    args = parse_args()
    start_logger(args)
    main()
