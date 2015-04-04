class Mood:
    """
    Container for a specific mood parameters
    """

    def __init__(self, name, color, value=0, melody=''):
        self.name = name
        self.value = value
        self.color = color
        self.melody = melody


class MoodsContainer:

    """
    Container for all moodies Mood values
    """

    def __init__(self):
        self.moods = {
            'default': Mood('noMood', '0,0,0'),
            'excited': Mood('excited', '0,255,0', '1c2g2p1c3g'),
            'nervous': Mood('nervous', '255,0,0', '3e3d5c')
        }

    def decrease_all_moods(self, val):
        for key in self.moods:
            self.decrease(key, val)

    def decrease(self, mood_name, val=20):
        if self.moods[mood_name].value > val:
            self.moods[mood_name].value -= val
        else:
            self.moods[mood_name].value = 0

    def increase(self, mood_name, val=20):
        if self.moods[mood_name].value < (100-val):
            self.moods[mood_name].value += val
        else:
            self.moods[mood_name].value = 100

    def compute_top_mood(self):
        top_mood = self.moods['default']
        max = 0
        for mood_name, mood in self.moods.iteritems():
            if mood.value > max:
                top_mood = mood
                max = mood.value
        return top_mood

