# Moodies

This git repo contains the python moodies libraries as well as the server script (listening to events and answering them) and a client script example that can be used on the CLI to sniff or trigger moodies events.

## MoodiesClient

Moodies library current work on top with pusherclient library, which in turn exchange the message using Pusher. Pusher has been factored out to moodies/client.py so that we can evolve to a different messaging system in the future if needed.
MoodiesClient is a wrapper to pusher that will handle all the connection, callbacks and message trigerring to pusher.

## ModdiesChannel

A moodies channel is a chat room containing moods (modds are Mood object contained in a MoodiesContainer).
The channel mood is an average of the users that joined that channel.

## MoodiesUser

A moodies user, it currently only holds the MoodiesContainer for that user.

## MoodiesEvents

Moodies event are event named event that client can send/receive. The moodies client will send and forward moodies events with their data being a Message object (moodies/message.py)
Below  is a list of events that can occur, and what value can be set in the Message.

For example, to send a message the event will be `events.MESSAGE` and the data will be `Message(user_id='user_id', value='My message')`

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
