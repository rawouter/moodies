from __future__ import absolute_import, unicode_literals

import pytest
import sys
sys.path.append('..')

from moodies.client import MoodiesClient

@pytest.fixture()
def client():
     return MoodiesClient('appkey', 'secret', 'moodies-channel')

def test_moodies_defaults(client):
    assert client.appkey == 'appkey'
    assert client.secret == 'secret'
    assert client.channel_name == 'moodies-channel'
    assert not client.connected
