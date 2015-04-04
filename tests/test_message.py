from __future__ import absolute_import, unicode_literals

import pytest
import sys
sys.path.append('..')

import json
from moodies.message import Message

msg_dict = {'value': 'plop', 'user_id': 'rawouter'}

@pytest.fixture()
def message():
     return Message(**msg_dict)

def test_message(message):
    assert message.user_id == msg_dict['user_id']
    assert message.value == msg_dict['value']
    assert message.to_dict() == msg_dict

def test_message_from_json():
    message = Message()
    message.feed_with_json(json.dumps(msg_dict))
    test_message(message)
