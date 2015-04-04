import unittest

from moodies.moods import Mood, MoodsContainer


class TestMood(unittest.TestCase):
    def test_get_element(self):
        mood = Mood('testMood', 'testColor')
        self.assertEqual(mood.name, 'testMood')
        self.assertEqual(mood.color, 'testColor')
        self.assertIsInstance(mood.value, int)
        self.assertEqual(mood.value, 0)
        self.assertIs(hasattr(mood, 'melody'), True)

class TestMoodsContainer(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()

