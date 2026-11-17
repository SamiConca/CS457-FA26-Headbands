"""Client in the game 'Headbands'.

Clients take turns guessing what they are,
in a certain time limit.

Client with most correct guesses wins.
"""

import json
import socket
import sys
import threading

help_script = """Input format: 'python client.py -i <host name> -p <port num>'

-i <host name>: name of host for server (e.g. server.smith.edu)

-p <port num>: number of port server is hosted on (e.g. 8080)
"""

instructions = """Instructions:
1. The game consists of 5 rounds.
2. In each round, one player is the Guesser and the other is the Informer.
3. The Guesser will be assigned a role (e.g. 'dog')
and must guess what it is by asking the Informer yes or no questions.
4. The Informer will know the role
and must answer the Guesser's questions truthfully.
5. The round ends when the Guesser guesses the role correctly or time runs out.
6. The player with the most correct guesses wins.
7. In the event of a tie, the game will ask both players to
try to guess what role the server has assigned itself.

Commands:
- 'ask <question-id>' to make a guess.
- 'guess <role>' to guess your role.
- 'answer <yes/no>' to answer a guess.
- 'quit' to exit the game.
"""


def send_json(client_socket, data):
    """Send NDJSON message to server."""
    message = json.dumps(data).encode("utf-8") + b"\n"
    client_socket.sendall(message)


def receive_json(client_socket):
    """Parse NDJSON message from server and inform client appropriately."""
    buffer = b""

    while True:
        # Obtain and process NDJSON data
        data = client_socket.recv(4096)
        if not data:
            print("[DISCONNECT] Server has disconnected")
            return

        buffer += data
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            if not line.strip():
                continue

            try:
                message = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                print("[ERROR] Received invalid JSON from server")
                continue

            # Determine correct response to parsed message
            type = message.get("type")

            if type == "player":
                print(f"\n[ASSIGNMENT] You are the {message['player']}")
            elif type == "role":
                print(f"[ROLE] The Guesser is a {message['role']}")
            elif type == "question_options":
                print("\n[QUESTIONS] Choose a question to ask:")
                for option in message["options"]:
                    print(f" {option['id']}: {option['text']}")
                print("Type: 'ask <question-id>'")
            elif type == "question":
                print(f"\n[ASK] The Guesser asks: {message['text']}")
                print("Reply with: 'answer yes' or 'answer no'")
            elif type == "answer":
                print(f"[INFORM] The Informer replied: {message['answer']}")
            elif type == "guess_result":
                print(f"[GUESS] {message['result']}")
            elif type == "score_update":
                print(f"[SCORE UPDATE] Your current score "
                      f"is: {message['score']}")
            elif type == "round_over":
                print(f"[ROUND OVER] The round is over. "
                      f"The Guesser was a {message['role']} "
                      f"and the result was {message['result']}.")
            elif type == "tiebreaker":
                print("\n[DRAW] Guess the server's role.")
                print("Clues:")
                for clue in message["clues"]:
                    print(f" - {clue}")
                print("You have 60 seconds; "
                      "if neither player guesses correctly, "
                      "the server picks another role.")
            elif type == "game_over":
                print(f"[GAME OVER] {message['message']}.")
                print(f"[FINAL SCORE] Your score: {message['score']}")
                return
            elif type == "error":
                print(f"[ERROR] {message['message']}")


def set_up_clients(server_ip, server_port):
    """Establish client threads and basic behavior."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[CONNECT] Attempting to connect"
          f"to server at {server_ip}:{server_port}...")
    client_socket.connect((server_ip, server_port))
    print("[LOBBY JOIN] Successfully joined the lobby")

    threading.Thread(
        target=receive_json,
        args=(client_socket,),
        daemon=True
    ).start()

    print(instructions)

    while True:
        # Try to get user input from clients
        try:
            user_input = input("> ").strip()
        except EOFError:
            print("\n[ERROR] EOFError, exiting...")
            break

        if user_input.lower() == "quit":
            print("[DISCONNECT] Exiting the game...")
            break

        # Parse user input; valid types are guess, ask, and answer
        command, _, value = user_input.partition(" ")
        command = command.lower()
        value = value.strip()

        if command == "ask" and value:
            send_json(client_socket,
                      {"type": "ask", "question": value, })
        elif command == "guess" and value:
            send_json(client_socket,
                      {"type": "guess", "guess": value, })
        elif command == "answer" and value.lower() in ("yes", "no"):
            send_json(client_socket,
                      {"type": "answer", "answer": value.lower(), })
        else:
            print("[ERROR] Invalid command. "
                  "Please use 'ask <question-id> or "
                  "'guess <role>' if you are Guesser, "
                  "'answer <yes/no>' if you are Informer, "
                  "or 'quit' to exit the game.")


def connect_to_server():
    """Print instructions, connect to server."""
    if (sys.argv[1] == "-h"):
        print(help_script)
        sys.exit(0)

    if (sys.argv[1] == "-i" and sys.argv[3] == "-p"):
        try:
            server_ip = socket.gethostbyname(sys.argv[2])
        except socket.gaierror:
            print(f"[ERROR] Unable to resolve DNS hostname '{sys.argv[2]}'.")
            print("Please check your CISCO router "
                  "DNS configuration or spelling")
            sys.exit(1)
        server_port = int(sys.argv[4])
        if not (server_port > 1023 and server_port < 65536):
            print(f"[ERROR] Port not in range 1024-65535.")
            sys.exit(1)
    else:
        print("Unknown input. Please type 'python client.py -h' for help.")
        sys.exit(1)

    set_up_clients(server_ip, server_port)


if __name__ == "__main__":
    connect_to_server()
