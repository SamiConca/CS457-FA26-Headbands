""" Server in the game 'Headbands'.

Server waits for two clients.

Server assigns roles and sends prompts.
"""

import json
import socket
import sys
import threading

help_script = """Input format: 'python server.py -p <port num>'

-p <port num>: number of port server is hosted on (e.g. 8080)
"""

send_locks = {}


def send_json(client_socket, data):
    message = json.dumps(data).encode("utf-8") + b"\n"
    with send_locks[client_socket]:
        client_socket.sendall(message)


def receive_json(client_socket):
    buffer = b""

    while True:
        data = client_socket.recv(4096)
        if not data:
            return

        buffer += data
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            if line.strip():
                yield json.loads(line.decode("utf-8"))


def play_round(guesser, informer, role, guesser_score, informer_score):
    send_json(guesser, {"type": "player", "player": "Guesser"})
    send_json(informer, {"type": "player", "player": "Informer"})
    send_json(informer, {"type": "role", "role": role})
    send_json(guesser, {"type": "role", "role": role})

    current_guesser = guesser
    current_informer = informer

    while True:
        # Wait for Guesser's guess
        try:
            message = next(receive_json(current_guesser))
        except (StopIteration, ConnectionError, json.JSONDecodeError):
            return

        if message.get("type") != "guess":
            continue

        guess = str(message.get("value", "")).strip()
        send_json(current_informer, {"type": "guess", "guess": guess})

        # Wait for Informer's answer
        try:
            reply = next(receive_json(current_informer))
        except (StopIteration, ConnectionError, json.JSONDecodeError):
            return

        answer = str(reply.get("value", "")).strip().lower()
        if reply.get("type") != "answer" or answer not in ("yes", "no"):
            send_json(current_informer, {"type": "error", "message": "Invalid answer. Please respond with 'yes' or 'no'."})
            continue

        send_json(current_guesser, {"type": "answer", "answer": answer.title()})
        send_json(current_informer, {"type": "answer received"})

        if guess.casefold() == role.casefold():
            send_json(current_guesser, {"type": "round_over", "result": "correct"})
            guesser_score += 1
            send_json(current_informer, {"type": "round_over", "result": "correct"})
            informer_score += 1
            return (guesser_score, informer_score)



def handle_client(clients):
    roles = ["dog", "redwood", "guitar"]
    guesser_score = 0
    informer_score = 0

    try:
        for round_number, role in enumerate(roles):
            guesser = clients[round_number % 2]
            informer = clients[1 - (round_number % 2)]
            guesser_score, informer_score = play_round(guesser, informer, role, guesser_score, informer_score)

        for client in clients:
            send_json(client, {"type": "game_over", "scores": (guesser_score, informer_score)})
    except (OSError, ConnectionError):
        pass
    finally:
        for client in clients:
            try:
                client.close()
            except OSError:
                pass


def accept_client_connections(server_socket):
    while True:
        clients = []
        try:
            while len(clients) < 2:
                client_socket, client_address = server_socket.accept()
                send_locks[client_socket] = threading.Lock()
                clients.append((client_socket, client_address))
                print(f"[LOBBY JOIN] Client {client_address} has joined the lobby")
        
            threading.Thread(
                target = handle_client, 
                args = (clients,), 
                daemon = True
            ).start()
        except (OSError, KeyboardInterrupt):
            for client in clients:
                client.close()
                print("[DISCCONNECT] Server shutting down...")
            server_socket.close()
            sys.exit(1)


def start_server():
    if (sys.argv[1] == "-h"):
        print(help_script)
        sys.exit(0)

    if (sys.argv[1] == "-p"):
        host_port = int(sys.argv[2])
    else:
        print("Unknown input. Please type 'python server.py -h' for help.")
        sys.exit(1)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsocketopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", host_port))
    server_socket.listen()
    print(f"[LOBBY WAIT] Server listening on 0.0.0.0:{host_port}")

    accept_client_connections(server_socket)


if __name__ == "__main__":
    start_server()
    