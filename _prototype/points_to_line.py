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
    
    
if __name__ == '__main__':
    track_gen = TrackGen("shp/track.shp", 15)
    for point in track_gen.get_track_points():
        print point