from moods import MoodsContainer

class MoodiesChannel:

    """
    Channel class holding a chat room (pusher channel) and it's moods (MoodsContainer class)
    """

    def __init__(self, channel_name):
        self.name = channel_name
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
