from __future__ import absolute_import, unicode_literals

import pytest
import sys
sys.path.append('..')

from moodies.moods import Mood, MoodsContainer

@pytest.fixture()
def mood():
     return Mood('testMood', 'testColor')

@pytest.fixture()
def container():
     return MoodsContainer()

# Mood tests
def test_mood_object_defaults(mood):
    assert mood.name == 'testMood'
    assert mood.color == 'testColor'
    assert isinstance(mood.value, int)
    assert mood.value == 0
    assert hasattr(mood, 'melody')

def test_mood_object_value_operations(mood):
    with pytest.raises(AssertionError):
        mood.value = 'Only numbers are accepted'
    mood.value += 50
    assert mood.value == 50
    mood.value += 77
    assert mood.value == 100
    mood.value -= 77.5
    assert mood.value == 22.5
    mood.value -= 77
    assert mood.value == 0

# MoodsContainer tests
def test_moodscontainer_detauls(container):
    assert len(container.moods) > 1
    default_mood = container.moods['default']
    assert default_mood.value == 0

def test_moodscontainer_func(container):
    default_mood = container.moods['default']
    container.decrease_all_moods(10)
    assert default_mood.value == 0
    container.increase('default', 50)
    assert default_mood.value == 50
    container.increase('default', 77)
    assert default_mood.value == 100
    assert container.compute_top_mood().name == 'default'


