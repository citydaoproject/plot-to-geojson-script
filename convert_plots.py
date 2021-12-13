
import csv
from geojson import FeatureCollection
from geojson import Feature
from geojson import Point
from geojson import Polygon
import math
import numpy as np
import sys
import argparse

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

def cartesian_to_longitude_latitude(x, y, z):
    # taken from here https://en.wikipedia.org/wiki/Earth_radius
    # radius=6378000 #equatorial radius
    radius=6371000 #globally average radius
    # calculation from https://stackoverflow.com/questions/1185408/converting-from-longitude-latitude-to-cartesian-coordinates
    # note the comments regarding sphere/elipsiod assumptions of the earth.. we assume a sphereical earth here.
    lat=math.degrees(math.asin(z/radius))
    lon=math.degrees(math.atan2(y,x))
    return (lon, lat)


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

#given two points in lon/lat, calculate the "distance" between them.
def distance_lonlat(p1, p2):
    p1_position=longitude_latitude_to_cartesian(p1[0], p1[1])
    p2_position=longitude_latitude_to_cartesian(p2[0], p2[1])
    return distance(p1_position, p2_position)

def point_line_distance(line, point):
    #everything as cartesian to make things easy...
    (p1, p2)=line
    a=np.array(longitude_latitude_to_cartesian(p1[0], p1[1]))
    b=np.array(longitude_latitude_to_cartesian(p2[0], p2[1]))
    p=np.array(longitude_latitude_to_cartesian(point[0], point[1]))

    # taken from https://stackoverflow.com/questions/56463412/distance-from-a-point-to-a-line-segment-in-3d-python
    # normalized tangent vector
    d = np.divide(b - a, np.linalg.norm(b - a))
    # signed parallel distance components
    s = np.dot(a - p, d)
    t = np.dot(p - b, d)
    # clamped parallel distance
    h = np.maximum.reduce([s, t, 0])
    # perpendicular distance component
    c = np.cross(p - a, d)
    return np.hypot(h, np.linalg.norm(c))

def place_on_line(line, point):
    # #see formula from here: https://mathworld.wolfram.com/Point-LineDistance3-Dimensional.html
    # #everything as cartesian to make things easy...
    (p1, p2)=line
    x1=np.array(longitude_latitude_to_cartesian(p1[0], p1[1]))
    x2=np.array(longitude_latitude_to_cartesian(p2[0], p2[1]))
    x0=np.array(longitude_latitude_to_cartesian(point[0], point[1]))
    t=-np.dot(x1-x0, x2-x1)/pow(np.linalg.norm(x2-x1), 2)
    v=x1+t*(x2-x1)
    if t<0.0001 or t>0.9999: #likely endpoints. these are duplicates. we don't need to move them.
        return point
    else:
        point=cartesian_to_longitude_latitude(v[0], v[1], v[2])
        return point

def main(argv):
    parser=argparse.ArgumentParser(description="converts a csv file of plot centers and area into geojson formated polygon boundries")
    parser.add_argument('filename', help="the input csv file to process")
    parser.add_argument('-a', '--adjacent-plots', dest='plots', required=False, help='a comma seperated string of two plots that are to the left/right of each other.')
    args=parser.parse_args()

    filename=args.filename
    if args.plots is not None:
        plots=args.plots.split(',')
        plot1=plots[0].lstrip()
        plot2=plots[1].lstrip()

    angle_offset=0.0
    if args.plots is not None:
        angle_offset=angle_between_plots(filename, plot1, plot2)

    # rather than build the geojson objects directly, we know that plot corners will not
    # align with one another. to fix this, we will first calculate and collect all the
    # corner points first, then do a pass to average nearby corners. this will require
    # couple passes through the data, first to find a good estimate of "nearby" using
    # the smallest plot available. the next to actually calculate the corners in lon/lat
    # then a pass through all the points to average them, and finally a pass through
    # each plot again, this time picking the correct averaged point, instead of calculating
    # the "real" corner positions.
    # this will hold our points in a list-of-list data (list of lists-that-contain-similar-points)
    points=[]

    #find the smallest plot, and use it to calculate an error bound between "connected" points
    smallest_plot_area=math.inf
    distance_error=math.inf
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
                length=math.sqrt(area)
                distance_error=length/3.0 #just use some fraction of the smallest plot's side length

    centerpoints=[] # a collection of Point features for the plot centers. why not.
    plots=[] # a collection of plot object that include the corner indexes into 'points', and other data as a dict
    # find all the projected corner points, and match them together in the 'points' list
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
                    plane_projection(center, rotate_2d((dx, dy), angle_offset)),
                    plane_projection(center, rotate_2d((-dx, dy), angle_offset)),
                    plane_projection(center, rotate_2d((-dx, -dy), angle_offset)),
                    plane_projection(center, rotate_2d((dx, -dy), angle_offset)),
            ]

            #loop through each corner, trying to find a close existing point
            corner_indexes=[]
            for corner in corners:
                bucket_found= False
                #look at all the existing points...
                for i, point_bucket in enumerate(points):
                    existing_point=point_bucket[0] # no need to check against all the points. if we are close to one, we should be close to all of them.
                    # if it is close, we're done.
                    if distance_lonlat(corner, existing_point)<distance_error:
                        corner_indexes.append(i)
                        point_bucket.append(corner)
                        bucket_found=True
                        break
                # if there are no close points, we add to the list.
                if not bucket_found:
                    corner_indexes.append(len(points))
                    points.append([corner])

            plots.append({
                'corners': corner_indexes,
                'fid': fid,
                'area': area,
                'lon': lon,
                'lat': lat,
            })
    # average together "close" points, aka points in the same bucket
    for point_bucket in points:
        avg_lat=0
        avg_lon=0
        for point in point_bucket:
            avg_lat+=point[0]
            avg_lon+=point[1]
        avg_lat/=len(point_bucket)
        avg_lon/=len(point_bucket)
        point_bucket.insert(0, (avg_lat, avg_lon))
    # and finally, make the geojson features out of the points
    plot_features=[]
    features=[]
    # need to sort by size so that gaps of smaller plots are filled by processing larger plots.
    plots.sort(reverse=True, key=lambda plot: plot['area'])
    for plot in plots:
        corners=plot['corners']
        fid=plot['fid']
        corners.append(corners[0]) #to make a enclosed shape

        # for each corner idx, pick a point out of the existing point bucket at that index. this should be the averaged point.
        corners=list(map(lambda idx: points[idx][0], corners))

        # now, to avoid gaps, we need to find points that lie "close" to one of this plots borders,
        # anf if so, place it exactly on the border.
        sides=[
            (corners[0], corners[1]), #I'm sure there's a more elegant way to do this..
            (corners[1], corners[2]),
            (corners[2], corners[3]),
            (corners[3], corners[0]),
        ]

        for side in sides:
            points_sharing_side=0
            for point_bucket in points:
                # if distside[0]!=point_bucket[0] and not side[1]!=point_bucket[0]: #no need to compare if its the same point
                    if point_line_distance(side, point_bucket[0])<distance_error:
                        point_bucket[0] = place_on_line(side, point_bucket[0])
                        points_sharing_side+=1
            # print("sharing side:", points_sharing_side)

        # print(corners)
        #and add the polygon to our features
        polygon=Feature(geometry=Polygon([
            [
                corners[0],
                corners[1],
                corners[2],
                corners[3],
                corners[4],
            ]
        ]), properties={"FID":fid})
        plot_features.append(polygon)
        features.append(polygon) #standard convention seems to use the "feature:" json field, output however wants it to be under "plots:" field. adding to "features:" lets standard visualization tools work well

    #create and print out the final collection in geojson format
    collection=FeatureCollection(features)
    collection.plots=plot_features
    print(collection)

if __name__ == "__main__":
   main(sys.argv[1:])
