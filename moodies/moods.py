class Mood(object):
    """
    Container for a specific mood parameters
    """

    def __init__(self, name, color, melody=''):
        self.name = name
        self.color = color
        self.melody = melody
        self._value = 0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        assert isinstance(val, (int, float)), 'Value is not a number'
        if val > 100: val = 100
        elif val < 0: val = 0
        self._value = val

class MoodsContainer:

    """
    Container for all moodies Mood values
    """

    def __init__(self):
        self.moods = {
            'default': Mood('default', '0,0,0'),
            'excited': Mood('excited', '0,255,0', melody='1c2g2p1c3g'),
            'nervous': Mood('nervous', '255,0,0', melody='3e3d5c')
        }

    def decrease_all_moods(self, val):
        for key, mood in self.moods.iteritems():
            mood.value -= val

    def decrease(self, mood_name, val=20):
        self.moods[mood_name].value -= val

    def increase(self, mood_name, val=20):
        self.moods[mood_name].value += val

    def compute_top_mood(self):
        top_mood = self.moods['default']
        max = 0
        for mood_name, mood in self.moods.iteritems():
            if mood.value > max:
                top_mood = mood
                max = mood.value
        return top_mood

