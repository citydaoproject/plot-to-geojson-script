
import csv
from geojson import FeatureCollection
from geojson import Feature
from geojson import Point
from geojson import Polygon
import math



#assuming area is defined on a flat plane, centered on the plots centerpoint.
def plane_projection(center, dx, dy):
    (center_lon, center_lat)=center
    # taken from equatorial radius here https://en.wikipedia.org/wiki/Earth_radius
    radius=6378000 #equatorial radius
    radius=6371000 #globally average radius
    # determine the spherical angle from the center, to a point directly to the left of the center by dx. note this point is *not* on the surface of the earth anymore.
    # c--c+dx
    # | /
    # |/ <-angle
    # (center of the earth)
    dx_angle=math.degrees(math.atan2(dx,radius))
    dy_angle=math.degrees(math.atan2(dy,radius))
    #add the delta to the center's lon/lat (aka, sphereical coordinates)
    return (center_lon+dx_angle, center_lat+dy_angle)


centerpoints=[]
plots=[]
features=[]
#TODO make filename a parameter
with open('plots.csv', newline='\n') as csvfile:
    reader=csv.reader(csvfile, delimiter=',')
    #skip the title row
    reader.__next__()
    for row in reader:
        fid=int(row[0])
        area=float(row[1])
        lon=float(row[2])
        lat=float(row[3])
        center=Feature(geometry=Point([lon,lat]))
        centerpoints.append(center)
        #assuming a flat plane...
        length=math.sqrt(area)
        dx=length/2
        dy=length/2

        center=(lon,lat)
        corners=[
            [
            plane_projection(center, dx, dy),
            plane_projection(center, -dx, dy),
            plane_projection(center, -dx, -dy),
            plane_projection(center, dx, -dy),
            plane_projection(center, dx, dy),
            ]
        ]

        plot=Feature(geometry=Polygon(corners))
        # features.append(center)
        features.append(plot)
collection=FeatureCollection(features)
# collection.centers=centerpoints
# collection.plots=plots
print(collection)

# def binary_search(expected_value, guess1, guess2, max_iter=1000):
#     for i in range(max_iter):
#         area=solid_angle(guess)
#     return solution

# def solid_angle(n,s,e,w):
#     # taken from equatorial radius here https://en.wikipedia.org/wiki/Earth_radius
#     radius=6378000 #equatorial radius
#     radius=6371000 #globally average radius
#     #see https://en.wikipedia.org/wiki/Solid_angle for formulas
#     area=(sin(theta_north)-sin(theta_south))*(theta_east-theta_west)*radius
#     return area
