# TODO: 
# - Test with multiple clients on different machines running at the same time (should work)
# - Add logic for distributing URLs from last indexed position within data_sources (pickup where we left off)

import socket
import threading
import requests

urls = []
lock = threading.Lock()
data_sources = [
    "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links-ACTIVE.txt"
]

# Function to load URLs from data_sources into the shared list
def load_urls():
    global urls
    for source in data_sources:
        response = requests.get(source)
        urls += response.text.splitlines()

# Function to handle client connections
def handle_client(client_socket):
    while True:
        # Lock to ensure thread-safe access to shared resource (urls)
        with lock:
            if urls:
                url = urls.pop(0)
            else:
                break

        client_socket.send(url.encode())
        response = client_socket.recv(1024)
        print(f"Received response from client: {response.decode()}")

    client_socket.close()

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the server IP address and port 8889
server_socket.bind(('172.105.102.230', 8889))

# Listen for incoming connections
server_socket.listen(5)
print("Server listening on port 8889...")

# Load URLs from data_sources into the shared list
load_urls()

while True:
    # Accept a new connection
    client_socket, client_address = server_socket.accept()
    print(f"Connection from {client_address[0]}:{client_address[1]}")

    # Start a new thread to handle the client
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()
