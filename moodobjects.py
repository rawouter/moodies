import logging

class MoodiesChannel:

    """
    Channel class representing a chat room (pusher channel) and it's moods (MoodsContainer class)
    """

    def __init__(self, pusher_channel):
        self.logger = logging.getLogger('moodies.MoodiesChannel')
        self.pusher_channel = pusher_channel
        self.name = pusher_channel.name
        self.moods_container = MoodsContainer()
        self.current_mood = self.moods_container.moods['default']
        self.users = []

    def recompute_mood(self):
        """
        Recompute the current channel top mood
        Return True if the current mood changed
        """
        moods = self.moods_container.moods
        old_mood = self.current_mood
        for mood_name, mood in moods.iteritems():
            mood.value = 0
            if not len(self.users):
                continue # We just reset moods to 0 if there are no more users
            for user in self.users:
                mood.value += user.moods_container.moods[mood_name].value
            mood.value = mood.value / len(self.users)
        self.current_mood = self.moods_container.compute_top_mood()
        return old_mood.name is not self.current_mood.name


class Mood:
    """
    Contains a mood parameters
    """

    def __init__(self, name, value, color, melody=''):
        self.name = name
        self.value = value
        self.color = color
        self.melody = melody

class MoodsContainer:

    """
    Contains Mood values
    """

    def __init__(self):
        self.moods = {
            'default': Mood('noMood', 0, '0,0,0'),
            'excited': Mood('excited', 0, '0,255,0', '1c2g2p1c3g'),
            'nervous': Mood('nervous', 0, '255,0,0', '3e3d5c')
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



