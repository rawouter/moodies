from moods import MoodsContainer

class MoodiesUser:

    """
    User class, store Mood per users in a MoodsContainer
    """

    def __init__(self, user_id):
        self.user_id = user_id
        self.moods_container = MoodsContainer()
        self.top_mood = self.moods_container.moods['default']

    def compute_top_mood(self):
        self.top_mood = self.moods_container.compute_top_mood()
        return self.top_mood
