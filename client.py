""" Client in the game 'Headbands'.

Clients take turns guessing what they are,
in a certain time limit.

Client with most correct guesses wins.
"""

import socket
import sys

help_script = """Input format: 'python client.py -i <host name> -p <port num>'

-i <host name>: name of host for client (e.g. server.smith.edu)

-p <port num>: number of port client is hosted on (e.g. 8080)
"""


if __name__ == "__main__":
    if (sys.argv[1] == "-h"):
        print(help_script)
        sys.exit(0)

    if (sys.argv[1] == "-i" and sys.argv[3] == "-p"):
        try:
            host_ip = socket.gethostbyname(sys.argv[2])
        except socket.gaierror as e:
            print(f"[ERROR] Unable to resolve DNS hostname '{sys.argv[2]}'.")
            print("Please check your CISCO router DNS configuration or spelling")
            sys.exit(1)
        host_port = int(sys.argv[4])
    else:
        print("Unknown input. Please type 'python client.py -h' for help.")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind((host_ip, host_port))