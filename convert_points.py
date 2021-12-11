
import csv
from geojson import FeatureCollection
from geojson import Feature
from geojson import Point
from geojson import Polygon
import math

# this function calculates the new lon/lat of a new point resting at center+p, where
# p is an x/y point on a plane centered at.. center. and center is a lon/lat pair
# (this is used assuming area is defined on a flat plane, centered on the plots centerpoint,
# not as an area of the earth's surface which would be curved. from some preliminary searching,
# this does not seem to be a common way to measure land area, which is good for us :D)
def plane_projection(center, p):
    (dx, dy)=p
    (center_lon, center_lat)=center
    # taken from here https://en.wikipedia.org/wiki/Earth_radius
    # radius=6378000 #equatorial radius
    radius=6371000 #globally average radius
    # determine the spherical angle from the center, to a point directly to the left of the center by dx. note this point is *not* on the surface of the earth anymore.
    # c=center of plot
    #
    # c--c+dx
    # | /
    # |/ <-angle
    # (center of the earth)
    dx_angle=math.degrees(math.atan2(dx,radius))
    dy_angle=math.degrees(math.atan2(dy,radius))
    #add the delta to the center's lon/lat (aka, sphereical coordinates)
    return (center_lon+dx_angle, center_lat+dy_angle)

def longitude_latitude_to_cartesian(lon, lat):
    # taken from here https://en.wikipedia.org/wiki/Earth_radius
    # radius=6378000 #equatorial radius
    radius=6371000 #globally average radius
    #going to need everything in radians...
    lat=math.radians(lat)
    lon=math.radians(lon)
    # calculation from https://stackoverflow.com/questions/1185408/converting-from-longitude-latitude-to-cartesian-coordinates
    # note the comments regarding sphere/elipsiod assumptions of the earth.. we assume a sphereical earth here.
    x=radius*math.cos(lat)*math.cos(lon)
    y=radius*math.cos(lat)*math.sin(lon)
    z=radius*math.sin(lat)
    return (x,y,z)

#read the csv file into a list of dictionaries, by applying a filter function to avoid
#bringing the whole file into memory
def read_data_as_list(filename, filter_fn):
    with open(filename) as csvfile:
        reader=csv.DictReader(csvfile)
        data=[]
        for row in reader:
            #put them in our list if they meet the criteria, so we never keep the whole file in memory...
            if filter_fn(row):
                data.append(row)
    return data

#would be nice to use a real vector library if this gets more complicated..
def distance(p1, p2):
    dx=p1[0]-p2[0]
    dy=p1[1]-p2[1]
    dz=p1[2]-p2[2]
    return math.sqrt(dx*dx+dy*dy+dz*dz)

#would be nice to use a real vector library if this gets more complicated..
def rotate_2d(p, angle):
    (x,y) = p
    #from https://academo.org/demos/rotation-about-point/
    return (x*math.cos(angle)-y*math.sin(angle),
            y*math.cos(angle)+x*math.sin(angle))
    # return (x,y)

# when the plots are not aligned to lat/lon lines, but are offset by some angle, we
# can use two left/right adjacent plot centers to determine a suitable angle from latitude lines
# that the plots sit on. in our data, there seems to be a slight angle from
# true lat/lon grid.
def angle_between_plots(filename, fid1, fid2):
    data=read_data_as_list(filename, lambda row: row['FID']==fid1 or row['FID']==fid2)
    for row in data:
        (x,y,z) = longitude_latitude_to_cartesian(float(row['Longitude']),
                                                  float(row['Latitude']))
        row['position']=(x,y,z)
    triangle=[
        data[0]['position'],
        data[1]['position'],
        longitude_latitude_to_cartesian(float(data[0]['Longitude']),
                                        float(data[1]['Latitude']))
    ]
    # TODO this bit could use work.. depending on the data, the angle might be the same
    # depending on if data[0] is to the left or the right of data[1]. for our dataset
    # this.. works. but with a different dataset, we might need to be more selective
    # in how we assign data[0] and data[1]. but, for different data, the whole assumption
    # of a simple angle offset may not hold up either...
    hypotenuese=distance(data[0]['position'], data[1]['position'])
    side_length=distance(data[0]['position'], triangle[2])
    angle=math.asin(side_length/hypotenuese)
    return -angle


#TODO make filename a cli parameter
filename='plots.csv'

centerpoints=[] # a collection of Point features for the plot centers. why not.
plots=[] # the 'plots: ' json field
smallest_plot_area=math.inf #we might use this as an error bound later.
angle_offset=angle_between_plots(filename, '117', '118')

with open(filename) as csvfile:
    reader=csv.DictReader(csvfile)
    for row in reader:
        #name our fields
        fid=int(row['FID'])
        area=float(row['Area'])
        lon=float(row['Longitude'])
        lat=float(row['Latitude'])
        #find the smallest plot.
        if smallest_plot_area>area:
            smallest_plot_area=area

        #find the centerpoint
        center=(lon,lat)
        centerpoints.append(Feature(geometry=Point([lon,lat])))

        # find the corner points!
        #assuming a flat plane...
        length=math.sqrt(area)
        dx=length/2
        dy=length/2
        corners=[
            [
                plane_projection(center, rotate_2d((dx, dy), angle_offset)),
                plane_projection(center, rotate_2d((-dx, dy), angle_offset)),
                plane_projection(center, rotate_2d((-dx, -dy), angle_offset)),
                plane_projection(center, rotate_2d((dx, -dy), angle_offset)),
                plane_projection(center, rotate_2d((dx, dy), angle_offset)),
            ]
        ]

        #and add the polygon to our features
        plot=Feature(geometry=Polygon(corners), properties={"FID":fid})
        plots.append(plot)
        # features.append(center)
        # features.append(plot) #standard convention seems to use the "feature:" json field, output however wants it to be under "plots:" field. adding to "features:" lets standard visualization tools work well


#create and print out the final collection in geojson format
collection=FeatureCollection(plots)
collection.plots=plots
print(collection)
