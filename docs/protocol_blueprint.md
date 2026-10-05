#### Message Types:
1. `CONNECT` (Client -> Server): Request to join game.
2. `LOBBY_WAIT` (Server -> Client): Notification that server is waiting for Player 2.
3. `GAME_START` (Server -> Clients): Game initiated, assigns inital roles via coinflip (e.g. Player 1 is Guesser, Player 2 is Informer)
4. `ASK` (Client -> Server): Guesser action (i.e. yes or no question).
5. `INFORM` (Client -> Server): Informer action (i.e. yes or no response).
6. `GUESS` (CLients -> Server): Draw condition only; clients perform Guesser action in lightning round.
7. `STATE_UPDATE` (Server -> Clients): Broadcast current point status, time, round, and roles.
8. `DRAW` (Server -> Clients): Begin draw condition round.
9. `GAME_OVER` (Server -> Clients): Victory notification with final scores.
10. `ERROR` (Server -> Client): Invalid move or malformed packet error.
11. `DISCONNECT` (Server -> Client): Sends disconnect message to remaining client.

### Message Transport & Serialization Format
- **Transport Protocol:** TCP
- **Serialization Format:** JSON
- **Framing Mechanism:** Newline-delimited (`\n`) JSON payloads

### Example Newline-Delimited (`\n`) Wirestream:
```
{"msg_type":"CONNECT","player_id":"Player_1","timestamp":1727000000}\n{"msg_type":"ASK","player_id":"Player_1","payload":{"question":"Am I an object?"},"timestamp":1727000005}\n{"msg_type":"INFORM","player_id":"Player_2","payload":{"answer":"No"},"timestamp":1727000010}\n
```

#### Example JSON Protocol Schema:
```json
{
  "msg_type": "ASK",
  "player_id": "Player_1",
  "payload": {
    "question": "Am I an object?"
  },
  "timestamp": 1727000005
}
```
