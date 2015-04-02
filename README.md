# Moodies

This git repo contains the python moodies libraries as well as the `server.py` script (listening to events and answering them) and a `client.py` script example that can be used on the CLI to sniff or trigger moodies events.

## `MoodiesClient`

Moodies exchange data between the client using a [Pusher](https://pusher.com/) private chat room, with the [pusherclient library](https://github.com/ekulyk/PythonPusherClient/tree/master/pusherclient). Pusher has been factored out to `moodies/client.py` so that we can evolve to a different messaging system in the future if needed.
`MoodiesClient` is a wrapper to `pusherclient` that will handle all the connection, callbacks and message trigerring to pusher.

## `ModdiesChannel`

A moodies channel is a moodies *"room"* containing online users joining that room and one mood container representing the average of users moods with all possible moods in Moodies (moods are `Mood` object contained in a `MoodiesContainer`).

## `MoodiesUser`

A moodies user, `MoodiesUser` is simply a container holding the `MoodiesContainer` for that user so we keep track of it's mood. The moodies server will remember any users even after they left, so we keep track of their mood if come back before it's going to zero, but the moodies channel will only track the online users.

## Moodies Events

Moodies events are events that client can send/receive in their `MoodiesChannel` throught the `MoodiesClient`. An event is represented by a it's *name*, a string as in `moodies/events.py`and it's *data*, the `Message` object (moodies/message.py)
Below  is a list of events that can occur, and what values that can be set in the Message.

For example, to send the *text message* event the event name will be `events.MESSAGE` and the data can be `Message(user_id='user_id', value='My message')`

Or, using the client to send to the connected room:

```
moodies_client.send_event(events.MESSAGE, Message(user_id='user_id', value='My message'))
```

### Pusher events normally sent by the server:

1. client-new-color

   Tells the client the color we need to display (essentially reprenting the winning mood color for now).
   Format is a string reprensenting DEC RGB separated by comas, example: '0,255,0' for green.

2. client-text-message

   Text to display on the client side.
   Value is the string to display. Will be turned upper case on arduino (not all chars are supported).

3. client-play-melody

   Melody to play, documentation to come (it's in the arduino code)

### Pusher events the server will listen and reply to:

1. client-button-pushed

   Message sent from clients. Value is a string.
   From arduino, the content of the string it actually an integer representing the number of time the button was pushed, from    binary we start with:
   ```
   b1
   ```
   If the button was shortly pushed, we shift right it:
   ````
   b10
   ```
   If the buttong was long pushed, we shift right and add 1:
   ````
   b11
   ```
   So:
   ```
   2 = b10 = one short push
   4 = b100 = two short push
   5 = b101 = one short push followed by one long push
   ```
