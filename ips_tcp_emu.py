#!/usr/bin/python2

import sys
import socket
import math
import copy
import json
from random import randint

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
    def __init__(self, shp_file, distance, diff_distance=0):
        
        self.distance = distance
        self.diff_distance = diff_distance
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
                            track_dist = None
                            label_start = False
                        elif coord_first:
                            # start point
                            coord = self.retransorm(
                                list(shapely_line.coords)[0]
                            )
                            track_dist = 0
                            old_current_dist = 0
                            coord_first = False
                        elif current_dist < line_length:
                            # interpolate next points
                            coord = self.retransorm(
                                list(shapely_line.interpolate(current_dist).coords)[0]
                            )
                            track_dist = self.distance + randint(
                                -self.diff_distance,
                                self.diff_distance
                            )
                            old_current_dist = current_dist
                            current_dist += track_dist
                        else:
                            # end point
                            coord = self.retransorm(
                                list(shapely_line.coords)[-1]
                            )
                            track_dist = int(line_length - old_current_dist)
                            current_dist = False
                        yield coord[0], coord[1], track_dist


########################################################################
class IpsSocket(object):
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
    

########################################################################
class Core(object):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, **kwargs):
        """Constructor"""
        self.host = kwargs.get("host", None)
        self.port = kwargs.get("port", None)
        self.user = kwargs.get("user", None)
        self.track_file = kwargs.get("track_file", None)
        self.distance = kwargs.get("distance", None)
        self.diff_distance = kwargs.get("diff_distance", 0)
        self.speed = kwargs.get("speed", None)
        self.diff_speed = kwargs.get("diff_speed", 0)
        self.start_datetime = kwargs.get("start_datetime", False)
        self.imit_mode = kwargs.get("imit_mode", False)
        
        imit_mode_test = (None in (self.host, self.port, self.user)) and not self.imit_mode
        track_test = None in (self.track_file, self.distance)
        if imit_mode_test or track_test:
            raise Exception('ERROR: Config File')
        
        self.ping_data = {
            "req": "#P#",
            "resp":"#AP#", 
        } 
        self.user_data = {
            "req": "#L#{};NA".format(self.user),
            "resp": "#AL#1", 
        }
        self.track_data = {
            "req": "#SD#{0};{1};{2};{3};{4};0;0;3",
            "resp": "#ASD#1", 
        }

        self.sock = IpsSocket(imit=self.imit_mode)

        if isinstance(self.start_datetime, (list, tuple)):
            start_dt = datetime.datetime(*self.start_datetime)
            self.start_ts = int(time.mktime(start_dt.timetuple()))
        else:
            self.start_ts = False
        self.ts = self.start_ts

    def dd2nmea(self, lat, lon):
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
    
    def send_socket(self, **kwargs):
        if kwargs.get("req", False) and kwargs.get("resp", False):
            self.sock.sendall(b"{}\r\n".format(kwargs["req"]))
            received = self.sock.recv(1024)
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
    
    def run(self):
        self.sock.connect(self.host, self.port)
        self.send_socket(**self.ping_data)
            
        track_gen = TrackGen(self.track_file, self.distance, self.diff_distance)
        for point in track_gen.get_track_points():
            dd_lat = point[0]
            dd_lon = point[1]
            track_dist = point[2]
            if not dd_lat and not dd_lon and not track_dist:    
                self.sock.close()
                self.sock.connect(self.host, self.port)
                self.send_socket(**self.user_data)
            else:
                #coord
                nmea_lat, nmea_lon = self.dd2nmea(dd_lat, dd_lon)
                #speed
                if track_dist:
                    nmea_speed = self.speed + randint(
                        -self.diff_speed,
                        self.diff_speed
                    )
                    ms_spped = nmea_speed / 3.6
                    track_time = int(ms_spped * track_dist)
                else:
                    nmea_speed = 0
                    track_time = 0
                #data & time
                if self.start_ts:
                    self.ts += track_time
                else:
                    time.sleep(track_time)
                    self.ts = int(time.time())
                dt = datetime.datetime.fromtimestamp(self.ts)
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
                
                make_track = copy.deepcopy(self.track_data)
                make_track['req'] = make_track['req'].format(
                    nmea_date,
                    nmea_time, 
                    nmea_lat,
                    nmea_lon,
                    nmea_speed, 
                )
                self.send_socket(**make_track)
        self.sock.close()
        
    def __call__(self):
        return self.run()


if __name__ == '__main__':
    with open(sys.argv[1]) as file_:  
        kwargs = json.load(file_)
    core = Core(**kwargs)
    core()