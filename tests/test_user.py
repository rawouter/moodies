from __future__ import absolute_import, unicode_literals

import pytest
import sys
sys.path.append('..')

from moodies.user import MoodiesUser

@pytest.fixture()
def user():
    return MoodiesUser('testUser')

# MoodiesUser tests
def test_moodies_user_default(user):
    assert user.user_id == 'testUser'
    assert user.top_mood.name == 'default'

def test_moodies_user_moodchange(user):
    user.moods_container.increase('excited', 20)
    top_mood = user.compute_top_mood()
    assert top_mood.value == 20
    assert top_mood.name == 'excited'
