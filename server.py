from functools import partial
import logging
import sys
import time

import pusherclient

import config
from moodies import events
from moodies.message import Message
from moodies.channel import MoodiesChannel
from moodies.user import MoodiesUser

class MoodiesServer:

    """
    Main server class, will connect to pusher, listen to messages, compute them and answer.
    """

    def __init__(self):
        self.logger = logging.getLogger('moodies.Server')
        self.logger.info('Starting Moodies server')
        self.killed = False
        self.pusher = pusherclient.Pusher(config.appkey, secret=config.secret, user_data=config.server.user)
        self.channels = {}
        self.users = {}
        self.user_id = config.server.user['user_id']

    def run_forever(self):
        """
        Establish the connection to Pusher and keep the MoodiesServer class
        alive until killed
        """
        self._connect_to_pusher()
        self.logger.info('Entering server loop')
        while not self.killed:
            time.sleep(config.server.sleeptime)
            #tic = time.time()
            for user_name, user in self.users.iteritems():
                user.moods_container.decrease_all_moods(config.server.mood_decrease_rate)
                user.compute_top_mood()
            for channel_name, channel in self.channels.iteritems():
                if channel.recompute_mood():
                    self.send_pusher_msg(channel, events.COLOR,
                        Message(self.user_id, channel.current_mood.color)
                    )

            # The above computations are O(n^m) but moods are limited (almost constant),
            # only users can grow without control. Yet, if this becomes too slow we'd need to rethink the
            # algorithm, but this should be enough for an MVP
            #self.logger.debug('Update cycle duration: {}'.format(time.time() - tic))

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

        for c in config.connected_channels:
            self.pusher.subscribe(c)
            self.channels[c] = MoodiesChannel(c)
        for key, moodies_channel in self.channels.iteritems():
            self._setup_mood_channels_callbacks(moodies_channel.pusher_channel)


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
        if message.value == str(int('0b10', 2)):
            self.logger.info('{} is excited'.format(message.user_id))
            self._act_on_mood('excited', message.user_id, channel_name)
        # Arduino nervous
        elif message.value == str(int('0b100000', 2)):
            self.logger.info('{} is nervous'.format(message.user_id))
            self._act_on_mood('nervous', message.user_id, channel_name)

    def _act_on_mood(self, mood_name, user_id, channel_name):
        channel = self.channels[channel_name]

        if user_id not in self.users:
            # This happens if we crashed, might need to ask clients to reconnect if they us joining instead
            self.logger.error('{} is not a known user!'.format(user_id))
            self._callback_joining_member(
                    '{{"value": "", "user_id": "{}" }}'.format(user_id)
                , channel_name
           )
        self.users[user_id].moods_container.increase(mood_name)
        if channel.recompute_mood():
            self.send_pusher_msg(channel, events.COLOR,
                Message(self.user_id, channel.current_mood.color)
            )
        self.send_pusher_msg(channel, events.MELODY,
            Message(self.user_id, channel.current_mood.melody)
        )
        self.send_pusher_msg(channel, events.TEXT,
            Message(self.user_id, '{} is {}'.format(user_id, mood_name))
        )

    def send_pusher_msg(self, moodies_channel, event, message):
        """
        Send a pusher event in pusher channel
        """
        self.logger.debug('Sending new {} in {} - {}'.format(event, moodies_channel.name, message.value))
        moodies_channel.pusher_channel.trigger(event, message.to_dict())
        time.sleep(0.05) # Let pusher digest our message, pusher buffer messages without it...


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
