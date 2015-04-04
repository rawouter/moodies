from __future__ import absolute_import, unicode_literals

import pytest
import sys
sys.path.append('..')

from moodies.channel import MoodiesChannel
from moodies.user import MoodiesUser

@pytest.fixture()
def channel():
    return MoodiesChannel('testChannel')

@pytest.fixture()
def user1():
    user1 = MoodiesUser('user1')
    user1.moods_container.increase('excited', 40)
    return user1

@pytest.fixture()
def user2():
    user2 = MoodiesUser('user2')
    user2.moods_container.increase('nervous', 20)
    return user2

def test_moodies_channel_default(channel, user1, user2):
    assert channel.name == 'testChannel'
    assert channel.current_mood.name == 'default'
    assert len(channel.users) == 0

def test_moodies_channel_users(channel, user1, user2):
    channel.users.append(user1)
    channel.users.append(user2)
    assert channel.recompute_mood() == True
    assert channel.current_mood.name == 'excited'
