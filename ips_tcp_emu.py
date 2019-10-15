import socket
import math
import copy

import ogr
import osr

import datetime
import time

from shapely.geometry import LineString, Point
from shapely import wkt


########################################################################
class TrackGen(object):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, shp_file, distance, **kwargs):
        """
        kwargs
        datetime - YYYYMMDDHHMM
        speed - km/h
        
        datetime to timestamp
        dt = datetime.datetime(2019,10,15,17,48)
        ts = int(time.mktime(dt.timetuple()))
        
        timestamp to datatime
        ts = int(time.time())
        dt = datetime.datetime.fromtimestamp(ts)
        """
        
        self.distance = distance
        self.driver = ogr.GetDriverByName("ESRI Shapefile")
        self.ds = self.driver.Open(shp_file)
        
        grid_srs = osr.SpatialReference()
        grid_srs.ImportFromEPSG(4326)
        meter_srs = osr.SpatialReference()
        meter_srs.ImportFromEPSG(3857)
        self.grid2meter_transform = osr.CoordinateTransformation(grid_srs, meter_srs)
        self.meter2grid_transform = osr.CoordinateTransformation(meter_srs, grid_srs)
    
    def retransorm(self, coord):
        pnt = ogr.Geometry(ogr.wkbPoint)
        pnt.AddPoint(*coord)
        pnt.Transform(self.meter2grid_transform)
        return pnt.GetY(), pnt.GetX()
    
    def get_track_points(self):
        
        layers = [
            self.ds.GetLayerByIndex(lyr_name).GetName() 
            for lyr_name 
            in range(self.ds.GetLayerCount())
        ]
        for lyr_name in layers:
        
            lyr = self.ds.GetLayerByName(lyr_name)
            
            first_feat = lyr.GetFeature(0)
            if first_feat.geometry().GetGeometryName() == "LINESTRING":
                for ln in lyr:
                    geom = ln.GetGeometryRef()
                    geom.Transform(self.grid2meter_transform)
                    line_geom = geom.ExportToWkt()
                    # add line to shaple
                    shapely_line = LineString(wkt.loads(line_geom))
                    line_length = shapely_line.length
                    # add first point
                    current_dist = self.distance
                    label_start = True
                    coord_first = True
                    while current_dist:
                        if label_start:
                            coord = (None, None)
                            label_start = False
                        elif coord_first:
                            # start point
                            coord = self.retransorm(
                                list(shapely_line.coords)[0]
                            )
                            coord_first = False
                        elif current_dist < line_length:
                            # interpolate next points
                            coord = self.retransorm(
                                list(shapely_line.interpolate(current_dist).coords)[0]
                            )
                            current_dist += self.distance
                        else:
                            # end point
                            coord = self.retransorm(
                                list(shapely_line.coords)[-1]
                            )
                            current_dist = False
                        yield int(time.time()), coord[0], coord[1]

########################################################################
class IpsSocket:
    """"""

    #----------------------------------------------------------------------
    def __init__(self, imit=False):
        """Constructor"""
        self.imit = imit
        
    def connect(self, host, port):
        if not self.imit:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))
        
    def sendall(self, data):
        if not self.imit:
            self.sock.sendall(data)
        
    def recv(self, bite):
        if not self.imit:
            return self.sock.recv(bite)
        else:
            return "IMIT MODE"
    
    def close(self):
        if not self.imit:
            self.sock.close()
    


host = "education.ripas.ru"
port = 9336
user = "test_proto"
track_file = "shp/track.shp"
distance = 15

def dd2nmea(lat, lon):
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
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

def send_socket(sock_obj, **kwargs):
    if kwargs.get("req", False) and kwargs.get("resp", False):
        sock_obj.sendall(b"{}\r\n".format(kwargs["req"]))
        received = sock_obj.recv(1024)
        if received != "IMIT MODE" and kwargs["resp"] not in received:
            raise Exception(
                "IPS OUTPUT ERROR\nSent:     {0}\nERR:      {1}".format(
                    kwargs["req"],
                    received
                )
            )
        else:
            print("Sent:     {}".format(kwargs["req"]))
            print("Received: {}".format(received))

ping_data = {
    "req": "#P#",
    "resp":"#AP#", 
} 
user_data = {
    "req": "#L#{};NA".format(user),
    "resp": "#AL#1", 
}
track_data = {
    "req": "#SD#{0};{1};{2};{3};12;0;0;3",
    "resp": "#ASD#1", 
}

# TCP socket
#sock = IpsSocket(imit=True)
sock = IpsSocket()
sock.connect(host, port)
send_socket(sock, **ping_data)

track_gen = TrackGen(track_file, distance)
for point in track_gen.get_track_points():
    ts = int(point[0])
    dt = datetime.datetime.fromtimestamp(ts)
    nmea_date = "{0:02d}{1:02d}{2:02d}".format(
        dt.day,
        dt.month,
        int(dt.year)-2000, 
    )
    nmea_time = "{0:02d}{1:02d}{2:02d}".format(
        dt.hour,
        dt.minute,
        dt.second, 
    )
    dd_lat = point[1]
    dd_lon = point[2]
    
    if not dd_lat and not dd_lon:    
        sock.close()
        sock.connect(host, port)
        send_socket(sock, **user_data)
    else:
        nmea_lat, nmea_lon = dd2nmea(dd_lat, dd_lon)
        make_track = copy.deepcopy(track_data)
        make_track['req'] = make_track['req'].format(
            nmea_date,
            nmea_time, 
            nmea_lat,
            nmea_lon, 
        )
        send_socket(sock, **make_track)

sock.close()


