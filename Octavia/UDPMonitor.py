import socket


class MyData:
    def __init__(self, value):
        self.value = value

# Receiver's IP and port
receiver_ip = '0.0.0.0'  # Listen on all available interfaces
receiver_port = 12345

# Create UDP socket
receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print("Binding to:", receiver_ip," Port:", receiver_port)
# Bind the socket to the receiver's IP and port
receiver_socket.bind((receiver_ip, receiver_port))

while True:
    # Receive data
    print("Awaiting Data..")
    data, addr = receiver_socket.recvfrom(4096)

    

    print(f"Received data: {data} from {addr}")