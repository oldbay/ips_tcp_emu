from osgeo import ogr
from shapely.geometry import MultiLineString, Point
from shapely import wkt
import sys

## set the driver for the data
driver = ogr.GetDriverByName("FileGDB")
################################################################################
## CHANGE gdb, input_lyr_name, distance, output_pts (optional)

## path to the FileGDB
gdb = r"C:\Users\******\Documents\ArcGIS\Default.gdb"
## open the GDB in write mode (1)
ds = driver.Open(gdb, 1)

## single linear feature
input_lyr_name = "input_line"

## distance between each points
distance = 10

## output point fc name
output_pts = "{0}_{1}m_points".format(input_lyr_name, distance)
################################################################################

## reference the layer using the layers name
if input_lyr_name in [ds.GetLayerByIndex(lyr_name).GetName() for lyr_name in range(ds.GetLayerCount())]:
    lyr = ds.GetLayerByName(input_lyr_name)
    print "{0} found in {1}".format(input_lyr_name, gdb)
## if the feature class cannot be found exit gracefully
else:
    print "{0} NOT found in {1}".format(input_lyr_name, gdb)
    sys.exit()

## if the output already exists then delete it
if output_pts in [ds.GetLayerByIndex(lyr_name).GetName() for lyr_name in range(ds.GetLayerCount())]:
    ds.DeleteLayer(output_pts)
    print "Deleting: {0}".format(output_pts)

## create a new point layer with the same spatial ref as lyr
out_lyr = ds.CreateLayer(output_pts, lyr.GetSpatialRef(), ogr.wkbPoint)

## create a field to hold the distance values
dist_fld = ogr.FieldDefn("DISTANCE", ogr.OFTReal)
out_lyr.CreateField(dist_fld)
## check the geometry is a line
first_feat = lyr.GetFeature(1)

## accessing linear feature classes using FileGDB driver always returns a MultiLinestring
if first_feat.geometry().GetGeometryName() in ["LINESTRING", "MULTILINESTRING"]:
    for ln in lyr:
        ## list to hold all the point coords
        list_points = []
        ## set the current distance to place the point
        current_dist = distance
        ## get the geometry of the line as wkt
        line_geom = ln.geometry().ExportToWkt()
        ## make shapely MultiLineString object
        shapely_line = MultiLineString(wkt.loads(line_geom))
        ## get the total length of the line
        line_length = shapely_line.length
        ## append the starting coordinate to the list
        list_points.append(Point(list(shapely_line[0].coords)[0]))
        ## https://nathanw.net/2012/08/05/generating-chainage-distance-nodes-in-qgis/
        ## while the current cumulative distance is less than the total length of the line
        while current_dist < line_length:
            ## use interpolate and increase the current distance
            list_points.append(shapely_line.interpolate(current_dist))
            current_dist += distance
        ## append end coordinate to the list
        list_points.append(Point(list(shapely_line[0].coords)[-1]))

        ## add points to the layer
        ## for each point in the list
        for num, pt in enumerate(list_points, 1):
            ## create a point object
            pnt = ogr.Geometry(ogr.wkbPoint)
            pnt.AddPoint(pt.x, pt.y)
            feat_dfn = out_lyr.GetLayerDefn()
            feat = ogr.Feature(feat_dfn)
            feat.SetGeometry(pnt)
            ## populate the distance values for each point.
            ## start point
            if num == 1:
                feat.SetField("DISTANCE", 0)
            elif num < len(list_points):
                feat.SetField("DISTANCE", distance * (num - 1))
            ## end point
            elif num == len(list_points):
                feat.SetField("DISTANCE", int(line_length))
            ## add the point feature to the output.
            out_lyr.CreateFeature(feat)

else:
    print "Error: make sure {0} is a linear feature class with at least one feature".format(input_lyr_name)
    sys.exit()

del ds, out_lyr