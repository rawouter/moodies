import logging
import sys
import time

import config
from moodies import events
from moodies.message import Message
from moodies.channel import MoodiesChannel
from moodies.user import MoodiesUser
from moodies.client import MoodiesClient

class MoodiesServer:

    """
    Main server class, will use MoodiesClient to listen to messages, compute them and answer.
    """

    def __init__(self):
        self.logger = logging.getLogger('moodies.Server')
        self.logger.info('Starting Moodies server')
        self.killed = False
        self.moodies_client = MoodiesClient(config.appkey, config.secret, config.connected_channel)
        self.moodies_channel = MoodiesChannel(config.connected_channel)
        self.users = {}
        self.user_id = config.server.user['user_id']

    def run_forever(self):
        """
        Establish the connection to moodies comm layer and keep the MoodiesServer class
        alive until killed
        """
        self._connect_to_moodies()
        self.logger.info('Entering server loop')
        while not self.killed:
            time.sleep(config.server.sleeptime)
            for user_name, user in self.users.iteritems():
                user.moods_container.decrease_all_moods(config.server.mood_decrease_rate)
                user.compute_top_mood()
            if self.moodies_channel.recompute_mood():
                self.moodies_client.send_event(
                    events.COLOR,
                    Message(self.user_id, self.moodies_channel.current_mood.color)
                )

    def _connect_to_moodies(self):
        """
        Establish the connection to the communication channel using MoodiesClient
        """
        self.moodies_client.connect(
            config.server.user['user_id'],
            config.server.user['user_info']['name'],
            self._callback_connection_estabished
        )

    def _callback_connection_estabished(self, moodies_client):
        """
        Configure the private-* moodies channel callbacks
        """
        moodies_client.bind_callback_joining_member(self._callback_joining_member)
        moodies_client.bind_callback_leaving_member(self._callback_leaving_member)
        moodies_client.bind_callback(events.BUTTON_PUSHED, self._callback_button_pushed)


    def _callback_joining_member(self, msg):
        """
        Create a new MoodiesUser and store it for the first time we see the user.
        Append the user to the channel list of users.
        """
        self.logger.debug('Callback joining member - {}'.format(msg))
        message = Message()
        message.feed_with_json(msg)
        if message.user_id not in self.users.keys():
            self.users[message.user_id] = MoodiesUser(message.user_id)
        if self.users[message.user_id] not in self.moodies_channel.users:
            self.moodies_channel.users.append(self.users[message.user_id])

    def _callback_leaving_member(self, msg):
        """
        Remove users from channel users list.
        """
        self.logger.debug('Callback leaving member - {}'.format(msg))
        message = Message()
        message.feed_with_json(msg)
        self.moodies_channel.users.remove(self.users[message.user_id])

    def _callback_button_pushed(self, msg):
        self.logger.debug('Callback button pushed - {}'.format(msg))
        message = Message()
        message.feed_with_json(msg)
        self.logger.info('{} pushed the button'.format(message.user_id))
        # Hardocding values for now, MVP. We could have a config file/DB later for that.
        # Arduino excited
        if message.value == str(int('0b10', 2)):
            self.logger.info('{} is excited'.format(message.user_id))
            self._act_on_mood('excited', message.user_id)
        # Arduino nervous
        elif message.value == str(int('0b100000', 2)):
            self.logger.info('{} is nervous'.format(message.user_id))
            self._act_on_mood('nervous', message.user_id)

    def _act_on_mood(self, mood_name, user_id):
        if user_id not in self.users:
            # This happens if we crashed, might need to ask clients to reconnect if they us joining instead
            self.logger.error('{} is not a known user!'.format(user_id))
            self._callback_joining_member(
                    '{{"value": "", "user_id": "{}" }}'.format(user_id)
           )
        self.users[user_id].moods_container.increase(mood_name)
        if self.moodies_channel.recompute_mood():
            self.moodies_client.send_event(
                events.COLOR,
                Message(self.user_id, self.moodies_channel.current_mood.color)
            )
        self.moodies_client.send_event(
            events.MELODY,
            Message(self.user_id, self.moodies_channel.current_mood.melody)
        )
        self.moodies_client.send_event(
            events.TEXT,
            Message(self.user_id, '{} is {}'.format(user_id, mood_name))
        )



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
        description='Moodies server listening to moodies client messages and acting on them'
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
