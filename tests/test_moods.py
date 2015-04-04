from __future__ import absolute_import, unicode_literals

import sys
sys.path.append('..')

from moodies.moods import Mood, MoodsContainer

# Mood tests
def test_mood_object_defaults():
    mood = Mood('testMood', 'testColor')
    assert mood.name == 'testMood'
    assert mood.color == 'testColor'
    assert isinstance(mood.value, int)
    assert mood.value == 0
    assert hasattr(mood, 'melody')

def test_mood_object_func():
    mood = Mood('testMood', 'testColor')
    mood.increase(50)
    assert mood.value == 50
    mood.increase(-2)
    assert mood.value == 50
    mood.increase(77)
    assert mood.value == 100
    mood.decrease(77)
    assert mood.value == 23
    mood.decrease(-2)
    assert mood.value == 23
    mood.decrease(77)
    assert mood.value == 0

# MoodsContainer tests
def test_moodscontainer_detauls():
    container = MoodsContainer()
    assert len(container.moods) > 1
    default_mood = container.moods['default']
    assert default_mood.value == 0

def test_moodscontainer_func():
    container = MoodsContainer()
    default_mood = container.moods['default']
    container.decrease_all_moods(10)
    assert default_mood.value == 0
    container.increase('default', 50)
    assert default_mood.value == 50
    container.increase('default', 77)
    assert default_mood.value == 100
    assert container.compute_top_mood().name == 'default'


