"""
Defines the event strings that can this server will send or listen to in the pusher channel.

Clients events must be prefixed by client-
https://pusher.com/docs/client_api_guide/client_events
"""

# Events received by this server
BUTTON_PUSHED = 'client-button-pushed'

# Events sent by this server
CHANGE_COLOR = 'client-new-color'
DISPLAY_TEXT = 'client-text-message'
PLAY_MELODY = 'client-play-melody'
