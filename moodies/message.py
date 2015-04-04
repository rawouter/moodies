import json
import types

class Message:

    """
    Parse a the json string received in pusher message data
    """

    def __init__(self, user_id=None, value=None):
        self.value = value
        self.user_id = user_id

    def to_dict(self):
        return {
                'value': self.value
                , 'user_id': self.user_id
        }

    def feed_with_json(self, msg):
        assert type(msg) in types.StringTypes, 'Message instance did not receive a String'
        msg = json.loads(msg)
        self.value = self._get_json_val('value', msg)
        self.user_id = self._get_json_val('user_id', msg)

    def _get_json_val(self, key, json_msg):
        if key in json_msg:
            return json_msg[key]
        else:
            return None

