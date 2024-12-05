import socket
import time

HOST = "192.168.0.205"  # Replace with the server's IP address
PORT = 10001  # Port number

# Example string to send
message = "Hello, this is a test string from the client!"

# Connect to the server and send the string
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    while(True):
        sock.sendall(message.encode("utf-8"))  # Send the message as bytes
        time.sleep(5)
