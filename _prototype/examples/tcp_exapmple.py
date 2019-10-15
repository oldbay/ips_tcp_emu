import socket

host = "education.ripas.ru"
port = 9336
user = "test_proto2"

all_data = [
    ["#P#", "#AP#"], 
    ["#L#{};NA".format(user), "#AL#1"], 
    #["#SD#200411;123010;5544.6025;N;03739.6834;E;12;0;0;3", "#ASD#1"], 
    ["#SD#141019;022206;6001.2;N;03015.34;E;12;0;0;3", "#ASD#1"], 
]

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
# Connect to server and send data
sock.connect((host, port))

for data in all_data: 
    sock.sendall(b"{}\r\n".format(data[0]))
    received = sock.recv(1024)
    print("Sent:     {}".format(data[0]))
    print("Received: {}".format(received))

sock.close()


