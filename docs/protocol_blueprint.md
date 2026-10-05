#### Message Types:
1. `CONNECT` (Client -> Server): Request to join game.
2. `LOBBY_WAIT` (Server -> Client): Notification that server is waiting for Player 2.
3. `GAME_START` (Server -> Clients): Game initiated, assigns inital roles via coinflip (e.g. Player 1 is Guesser, Player 2 is Informer)
4. `ASK` (Client -> Server): Guesser action (i.e. yes or no question).
5. `INFORM` (Client -> Server): Informer action (i.e. yes or no response).
6. `GUESS` (CLients -> Server): Draw condition only; clients perform Guesser action in lightning round.
6. `STATE_UPDATE` (Server -> Clients): Broadcast current point status, time, round, and roles.
7. `DRAW` (Server -> Clients): Begin draw condition round.
8. `GAME_OVER` (Server -> Clients): Victory notification with final scores.
9. `ERROR` (Server -> Client): Invalid move or malformed packet error.

### Message Transport & Serialization Format
- **Transport Protocol:** TCP
- **Serialization Format:** [JSON / Fixed-Header Binary / Delimited Text]
- **Framing Mechanism:** [e.g., Newline-delimited (`\n`) JSON payloads OR 4-byte big-endian length prefix]

#### Example JSON Protocol Schema:
```json
{
  "msg_type": "MOVE",
  "player_id": "Player_1",
  "payload": {
    "row": 0,
    "col": 2
  },
  "timestamp": 1727000000
}
```
