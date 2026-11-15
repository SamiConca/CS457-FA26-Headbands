""" Server in the game 'Headbands'.

Server waits for two clients.

Server assigns roles and sends prompts.
"""

import socket
import sys
import threading

help_script = """Input format: 'python server.py -p <port num>'

-p <port num>: number of port server is hosted on (e.g. 8080)
"""

send_locks = {}


def handle_client(client_socket, client_address):
    print(f"[LOBBY JOIN] Client {client_address} has joined the lobby")
    client_socket.sendall(b"Welcome to Headbands! Please wait for another player to join...\n")
    # TODO: Implement game logic, including role assignment and prompt sending
    client_socket.close()


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


if __name__ == "__main__":
    start_server()
    