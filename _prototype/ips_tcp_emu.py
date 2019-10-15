import socket
import math

host = "education.ripas.ru"
port = 9336
user = "test_proto"

#30.259418129213
#15,56508775278
#60.0170857382903
#1,025144297418

coords = [
[ 60.0171192273275, 30.2593820454387,], 
[ 60.017136891861, 30.2594630498299, ], 
[ 60.0171928294879, 30.2596206401908,], 
[ 60.0172281584668, 30.2597222638815,], 
[ 60.0172465589616, 30.2597841217802,], 
[ 60.0172531831372, 30.2598562893287,], 
[ 60.0172502390593, 30.2599314024914,], 
[ 60.0172215342861, 30.2600418630247,], 
[ 60.0171854692793, 30.2601096121519,], 
[ 60.0171206993723, 30.2602672025128,], 
[ 60.0170971466474, 30.2603305332186,], 
[ 60.0170677057177, 30.2604395209449,], 
[ 60.0170463610273, 30.2605617639351,], 
[ 60.0170345846404, 30.2606795885041,], 
[ 60.0170286964454, 30.2607915218446,], 
[ 60.0170301684943, 30.2609358569415,], 
[ 60.0170367927133, 30.2610492630891,], 
[ 60.0170677057177, 30.2612584016989,], 
]

def dd2nmea(lat, lon):
    nmea_min_sec = lambda dd: math.fabs(math.modf(dd)[0] * 60)
    lat_sym = lambda dd: 'N' if dd > 0 else 'S'
    lon_sym = lambda dd: 'E' if dd > 0 else 'W'

    lat_nmea = "{0:02d}{1:02d}{2};{3}".format(
        int(lat),
        int(nmea_min_sec(lat)),
        "{0:.11f}".format(math.modf(nmea_min_sec(lat))[0])[1:], 
        lat_sym(lat), 
    )
    lon_nmea = "{0:03d}{1:02d}{2};{3}".format(
        int(lon),
        int(nmea_min_sec(lon)),
        "{0:.11f}".format(math.modf(nmea_min_sec(lon))[0])[1:], 
        lon_sym(lon), 
    )
    return lat_nmea, lon_nmea

start_data = [
    ["#P#", "#AP#"], 
    ["#L#{};NA".format(user), "#AL#1"], 
    #["#SD#200411;123010;5544.6025;N;03739.6834;E;12;0;0;3", "#ASD#1"], 
    #["#SD#141019;022206;6001.025144297418;N;03015.56508775278;E;12;0;0;3", "#ASD#1"], 
]

track_data = ["#SD#141019;022206;{0};{1};12;0;0;3", "#ASD#1"]

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
# Connect to server and send data
sock.connect((host, port))

for data in start_data: 
    sock.sendall(b"{}\r\n".format(data[0]))
    received = sock.recv(1024)
    print("Sent:     {}".format(data[0]))
    print("Received: {}".format(received))

for coord in coords:
    lat, lon = dd2nmea(*coord)
    track_coord = track_data[0].format(lat, lon)
    
    sock.sendall(b"{}\r\n".format(track_coord))
    received = sock.recv(1024)
    print("Sent:     {}".format(track_coord))
    print("Received: {}".format(received))

sock.close()


