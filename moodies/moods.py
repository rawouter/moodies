class Mood:
    """
    Container for a specific mood parameters
    """

    def __init__(self, name, color, value=0, melody=''):
        self.name = name
        self.value = value
        self.color = color
        self.melody = melody

    def decrease(self, val):
        if val < 0: return
        if self.value > val:
            self.value -= val
        else:
            self.value = 0

    def increase(self, val):
        if val < 0: return
        if self.value < (100-val):
            self.value += val
        else:
            self.value = 100



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
        for key in self.moods:
            self.decrease(key, val)

    def decrease(self, mood_name, val=20):
        self.moods[mood_name].decrease(val)

    def increase(self, mood_name, val=20):
        self.moods[mood_name].increase(val)

    def compute_top_mood(self):
        top_mood = self.moods['default']
        max = 0
        for mood_name, mood in self.moods.iteritems():
            if mood.value > max:
                top_mood = mood
                max = mood.value
        return top_mood

