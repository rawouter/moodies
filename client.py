#!/usr/bin/env python
from functools import partial
import logging
import os
import sys
import time

import config
from moodies import client
from moodies import events
from moodies import message

"""
This is as an example script to use the client library

It can be used from CLI to listen to channel (sniffer mode)
Or it can be used from CLI to send an event

Example send a button pushed with value 2:
   ./client.py -u rawouter -n Raphael -v 2 client-button-pushed
Example enter sniffing mode:
   ./client.py'
"""

logger = logging.getLogger('client')
logging.getLogger().addHandler(logging.NullHandler())

def print_callback(data, text):
    logger.info('%% Callback for {}: {}'.format(text, data))

def gen_callback(text):
    return partial(
        print_callback,
        text=text
    )

def callback_connected_sniff(moodies_client):
    logger.debug('Configuring all callbacks')
    moodies_client.bind_callback_joining_member(gen_callback('Joining member'))
    moodies_client.bind_callback_leaving_member(gen_callback('Leaving member'))
    moodies_client.bind_callback(events.COLOR, gen_callback('New color'))
    moodies_client.bind_callback(events.TEXT, gen_callback('Text message'))
    moodies_client.bind_callback(events.MELODY, gen_callback('Play melody'))
    moodies_client.bind_callback(events.BUTTON_PUSHED, gen_callback('Button pushed'))

def configure_logger(args):
    logger.setLevel(args.loglevel)
    formatter = logging.Formatter('%(asctime)s - [%(levelname)8s] %(name)s.%(lineno)d --- %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
            description='Moodies client example using the moodies library'
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
    parser.add_argument('-n', '--username',
        help='User Name to be sent',
        action='store',
        dest='user_name',
        default='M. Moodies Client'
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

def send_event_and_kill(data, moodies_client, event, message):
    import signal
    moodies_client.send_event(event, message)
    os.kill(os.getpid(), signal.SIGINT)

if __name__=='__main__':
    args = parse_args()
    configure_logger(args)
    moodies_client = client.MoodiesClient(config.appkey, config.secret, config.connected_channels[0])


    if args.event == 'sniff':
        logger.info('Sniffing mode...')
        moodies_client.connect(args.user_id, args.user_name, callback_connected_sniff)
        sleep_forever()
    else:
        logger.info('Sending command...')
        callback_connected_send_event = partial(
            send_event_and_kill,
            moodies_client=moodies_client,
            event=args.event,
            message=message.Message(args.user_id, args.value)
        )
        moodies_client.connect(args.user_id, args.user_name, callback_connected_send_event)
        try:
            sleep_forever()
        except KeyboardInterrupt:
            logger.info('Byebye')
