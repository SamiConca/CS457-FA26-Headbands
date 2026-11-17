"""Server in the game 'Headbands'.

Server waits for two clients.

Server assigns roles and sends prompts.
"""

import json
import queue
import random
import socket
import sys
import threading
import time

help_script = """Input format: 'python server.py -p <port num>'

-p <port num>: number of port server is hosted on (e.g. 8080)
"""

send_locks = {}

ROUND_TIME = 60  # seconds

ROLES = {
    "dog": {"type": "animal",
            "class": "mammal",
            "size": "medium",
            "fuzzy": True,
            "four_legs": True,
            "live_ocean": False},
    "whale": {"type": "animal",
              "class": "mammal",
              "size": "large",
              "fuzzy": False,
              "four_legs": False,
              "live_ocean": True},
    "lizard": {"type": "animal",
               "class": "reptile",
               "size": "small",
               "fuzzy": False,
               "four_legs": True,
               "live_ocean": True},
    "redwood": {"type": "plant",
                "class": "tree",
                "size": "large",
                "leaves": True,
                "cold_climate": False,
                "rarity": True},
    "cactus": {"type": "plant",
               "class": "succulent",
               "size": "small",
               "leaves": False,
               "cold_climate": False,
               "rarity": False},
    "beet": {"type": "plant",
             "class": "crop",
             "size": "medium",
             "leaves": False,
             "cold_climate": True,
             "rarity": False},
    "planet": {"type": "object",
               "class": "space",
               "size": "large",
               "made_wood": False,
               "can_sit": True,
               "man_made": False},
    "chair": {"type": "object",
              "class": "furniture",
              "size": "medium",
              "made_wood": True,
              "can_sit": True,
              "man_made": True},
    "computer": {"type": "object",
                 "class": "technology",
                 "size": "small",
                 "made_wood": False,
                 "can_sit": False,
                 "man_made": True},
}

QUESTIONS = {
    "animal": {
        "text": "Am I an animal?",
        "attribute": "type",
        "expected": "animal",
    },
    "plant": {
        "text": "Am I a plant?",
        "attribute": "type",
        "expected": "plant",
    },
    "object": {
        "text": "Am I an object?",
        "attribute": "type",
        "expected": "object",
    },
    "mammal": {
        "text": "Am I a mammal?",
        "attribute": "class",
        "expected": "mammal",
    },
    "reptile": {
        "text": "Am I a reptile?",
        "attribute": "class",
        "expected": "reptile",
    },
    "tree": {
        "text": "Am I a tree?",
        "attribute": "class",
        "expected": "tree",
    },
    "succulent": {
        "text": "Am I a succulent?",
        "attribute": "class",
        "expected": "succulent",
    },
    "crop": {
        "text": "Am I a crop?",
        "attribute": "class",
        "expected": "crop",
    },
    "space": {
        "text": "Am I in space?",
        "attribute": "class",
        "expected": "space",
    },
    "furniture": {
        "text": "Am I furniture?",
        "attribute": "class",
        "expected": "furniture",
    },
    "technology": {
        "text": "Am I technology?",
        "attribute": "class",
        "expected": "technology",
    },
    "small": {
        "text": "Am I small?",
        "attribute": "size",
        "expected": "small",
    },
    "medium": {
        "text": "Am I medium?",
        "attribute": "size",
        "expected": "medium",
    },
    "large": {
        "text": "Am I large?",
        "attribute": "size",
        "expected": "large",
    },
    "fuzzy": {
        "text": "Am I fuzzy?",
        "attribute": "fuzzy",
        "expected": True,
    },
    "leaves": {
        "text": "Do I have leaves?",
        "attribute": "leaves",
        "expected": True,
    },
    "made_wood": {
        "text": "Am I made of wood?",
        "attribute": "made_wood",
        "expected": True,
    },
    "four_legs": {
        "text": "Do I have four legs?",
        "attribute": "four_legs",
        "expected": True,
    },
    "cold_climate": {
        "text": "Do I live in a cold climate?",
        "attribute": "cold_climate",
        "expected": True,
    },
    "can_sit": {
        "text": "Can I be sat on?",
        "attribute": "can_sit",
        "expected": True,
    },
    "live_ocean": {
        "text": "Do I live in the ocean?",
        "attribute": "live_ocean",
        "expected": True,
    },
    "rarity": {
        "text": "Am I rare?",
        "attribute": "rarity",
        "expected": True,
    },
    "man_made": {
        "text": "Am I man-made?",
        "attribute": "man_made",
        "expected": True,
    },
}

TIE_BREAKER_CLUES = {
    ("type", "animal"): "I am an animal.",
    ("type", "plant"): "I am a plant.",
    ("type", "object"): "I am an object.",
    ("class", "mammal"): "I am a mammal.",
    ("class", "reptile"): "I am a reptile.",
    ("class", "tree"): "I am a tree.",
    ("class", "succulent"): "I am a succulent.",
    ("class", "crop"): "I am a crop.",
    ("class", "space"): "I am connected to space.",
    ("class", "furniture"): "I am furniture.",
    ("class", "technology"): "I am technology.",
    ("size", "small"): "I am small.",
    ("size", "medium"): "I am medium.",
    ("size", "large"): "I am large.",
    ("fuzzy", True): "I am fuzzy.",
    ("leaves", True): "I have leaves.",
    ("made_wood", True): "I am made of wood.",
    ("four_legs", True): "I have four legs.",
    ("cold_climate", True): "I live in a cold climate.",
    ("can_sit", True): "I can be sat on.",
    ("live_ocean", True): "I live in the ocean.",
    ("rarity", True): "I am rare.",
    ("man_made", True): "I am man-made.",
}


def send_json(client_socket, data):
    """Send NDJSON data to client with locking for multithreads."""
    message = json.dumps(data).encode("utf-8") + b"\n"
    with send_locks[client_socket]:
        client_socket.sendall(message)


def receive_json(client_socket, inbox, disconnects):
    """Parse NDJSON from client and monitor disconnections."""
    buffer = b""

    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                return

            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if line.strip():
                    inbox.put(json.loads(line.decode("utf-8")))
    except (OSError, json.JSONDecodeError):
        pass
    finally:
        disconnects.put(client_socket)
        print("[DISCONNECT] Client disconnected")


def wait_for_message(inbox, deadline, disconnects):
    """Wait for message from client during round, track disconnections."""
    while time.monotonic() < deadline:
        try:
            disconnected_client = disconnects.get_nowait()
            return None, disconnected_client
        except queue.Empty:
            pass

        remaining_time = deadline - time.monotonic()
        try:
            return inbox.get(timeout=min(remaining_time, 0.2)), None
        except queue.Empty:
            continue

    return None, None


def play_tiebreaker(clients, inboxes, disconnects):
    """Play tiebreaker round where 
    clients guess server role from three clues.
    """
    role = random.choice(list(ROLES.keys()))

    facts = [
        (attribute, value)
        for attribute, value in ROLES[role].items()
        if value is True or attribute in ("type", "class", "size")
    ]

    clues = [
        TIE_BREAKER_CLUES[fact]
        for fact in facts
        if fact in TIE_BREAKER_CLUES
    ]

    if len(clues) < 3:
        raise ValueError(f"[ERROR] Not enough clue text for role {role!r}")

    clues = random.sample(clues, 3)

    while True:
        for client in clients:
            send_json(client,
                      {"type": "tiebreaker",
                       "seconds": 60,
                       "clues": clues, })

        deadline = time.monotonic() + 60

        while time.monotonic() < deadline:
            try:
                disconnected = disconnects.get_nowait()
                winner = (clients[1] if disconnected == clients[0] 
                          else clients[0])
                return winner
            except queue.Empty:
                pass

            for client in clients:
                try:
                    message = inboxes[client].get_nowait()
                except queue.Empty:
                    continue

                if message is None:
                    winner = clients[1] if client == clients[0] else clients[0]
                    return winner

                if message.get("type") == "guess":
                    guess = str(message.get("guess", "")).strip()
                    if guess.casefold() == role.casefold():
                        return client

            time.sleep(0.05)


def play_round(guesser, informer, role, inboxes, disconnects):
    """Play round.

    Assign roles to players, keep time, determine correctness.
    """
    send_json(guesser, {"type": "player", "player": "Guesser"})
    send_json(informer, {"type": "player", "player": "Informer"})

    send_json(informer, {"type": "role", "role": role})

    send_json(guesser, {
        "type": "question_options",
        "options": [
            {"id": question_id, "text": question["text"]}
            for question_id, question in QUESTIONS.items()
        ],
    })

    deadline = time.monotonic() + ROUND_TIME

    while True:
        # Get Guesser's guess
        message, disconnected_client = wait_for_message(inboxes[guesser],
                                                        deadline,
                                                        disconnects)

        if disconnected_client:
            return "disconnected", disconnected_client

        if message is None:
            result = "timeout"
            break

        if message.get("type") == "guess":
            guess = str(message.get("guess", "")).strip()
            if guess.casefold() == role.casefold():
                result = "correct"
                break

            send_json(guesser, {"type": "guess_result", "result": "incorrect"})
            continue

        if message.get("type") != "ask":
            continue

        question_id = message.get("question")
        question = QUESTIONS.get(question_id)
        if question is None:
            send_json(guesser,
                      {"type": "error",
                       "message": "That question is not available.", })
            continue

        send_json(informer,
                  {"type": "question",
                   "question": question_id,
                   "text": question["text"], })

        reply, disconnected_client = wait_for_message(inboxes[informer],
                                                      deadline,
                                                      disconnects)

        if disconnected_client:
            return "disconnected", disconnected_client

        if reply is None:
            result = "timeout"
            break

        answer = str(reply.get("answer", "")).strip().lower()
        if reply.get("type") != "answer" or answer not in ("yes", "no"):
            send_json(informer,
                      {"type": "error",
                       "message": "Type 'answer yes/no'"})
            continue

        send_json(guesser,
                  {"type": "answer",
                   "question": question_id,
                   "answer": answer.title()})

    for client in (guesser, informer):
        send_json(client,
                  {"type": "round_over",
                   "role": role,
                   "result": result})

    return result, None


def handle_client(clients):
    """Handle client connections.

    Track score, track disconnects,
    track active messages, select
    roles for 5 rounds.
    """
    roles = random.sample(list(ROLES.keys()), k=5)
    inboxes = {client: queue.Queue() for client in clients}
    disconnects = queue.Queue()
    scores = {clients[0]: 0, clients[1]: 0}

    for client in clients:
        threading.Thread(
            target=receive_json,
            args=(client, inboxes[client], disconnects),
            daemon=True
        ).start()

    try:
        for round_number, role in enumerate(roles):
            guesser = clients[round_number % 2]
            informer = clients[1 - (round_number % 2)]
            result, disconnected_client = play_round(guesser,
                                                     informer,
                                                     role,
                                                     inboxes,
                                                     disconnects)

            if result == "disconnected":
                winner = (clients[1] if disconnected_client == clients[0]
                          else clients[0])

                try:
                    send_json(winner,
                              {"type": "game_over",
                               "result": "opponent_disconnected",
                               "message": "You win!", })
                except OSError:
                    pass

                return

            if result == "correct":
                scores[guesser] += 1

            for client in clients:
                send_json(client,
                          {"type": "score_update",
                           "score": scores[client]})

        score1 = scores[clients[0]]
        score2 = scores[clients[1]]
        if score1 > score2:
            winner = clients[0]
        elif score2 > score1:
            winner = clients[1]
        else:
            winner = play_tiebreaker(clients, inboxes, disconnects)

        for client in clients:
            send_json(client,
                      {"type": "game_over",
                       "result": "win" if client == winner else "loss",
                       "score": scores[client],
                       "message": ("You win!"
                                   if client == winner
                                   else "You lose"), })
    except (OSError, ConnectionError):
        pass
    finally:
        for client in clients:
            try:
                client.close()
            except OSError:
                pass


def accept_client_connections(server_socket):
    """Set up client connects and threads."""
    while True:
        clients = []
        try:
            while len(clients) < 2:
                client_socket, client_address = server_socket.accept()
                send_locks[client_socket] = threading.Lock()
                clients.append(client_socket)
                print(f"[LOBBY JOIN] Client {client_address}"
                      f"has joined the lobby")

            threading.Thread(
                target=handle_client,
                args=(clients,),
                daemon=True
            ).start()
        except (OSError, KeyboardInterrupt):
            for client in clients:
                client.close()
                print("[DISCCONNECT] Server shutting down...")
            server_socket.close()
            sys.exit(1)


def start_server():
    """Print instructions, bind server, call client conenctions."""
    if (sys.argv[1] == "-h"):
        print(help_script)
        sys.exit(0)

    if (sys.argv[1] == "-p"):
        host_port = int(sys.argv[2])
    else:
        print("Unknown input. Please type 'python server.py -h' for help.")
        sys.exit(1)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", host_port))
    server_socket.listen()
    print(f"[LOBBY WAIT] Server listening on 0.0.0.0:{host_port}")

    accept_client_connections(server_socket)


if __name__ == "__main__":
    start_server()
