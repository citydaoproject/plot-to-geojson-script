This script is used to convert plots of land given in a particulat csv format into geojson format.

There are several assumptions about this data:

1. all the plots are square.
2. all the plots are aliged to one another. (though, they may not be aligned to latitude and longitude lines! see the --adjacent-plots parameter)

# Usage

`usage: convert_plots.py [-h] -a PLOTS filename`
    
where PLOTS are two, comma seperated plot id's that are to the left/right of each other. this is used to calculate the angle that the plots align, relative to latitude and longitude lines.

example using provided csv, where plots 117 and 118 are adjacent plots:

`python convert_plots.py plots.csv -a 117,118 > output.json`

# Note about angle offset and adjacent plots

This script assumes that all plots are squares, oriented the same to one another. For instance, they might all line up neatly along latitude+longitude lines. 

However, given our first dataset, they may not line up along latitude+longitude lines. In this case, they may align along some angle, relative to latitude lines. For instance, imagine a perfect grid along x and y axis as longitude+latitude line(this technically isn't correct, but for small areas is a decent approximation). Imagine that grid rotated by say, 45.0 degrees: this is what our plots might look like.

In order to calculate what this angle-offset is for a given dataset, the script can use two similar-sized, adjacent plots, whose center points would then form a line along one of the axes.

One way to find this, is to use a geojson viewer to manually pick out two adjacent plots. That method is described here:

1. run the script without the -a option
2. load the result into a geojson viewer such as [https://geojson.in/](https://geojson.in/)  
3. pick two adjacent plots. look at their properties to find their FID values. In geojson.in, clicking on the plots should bring up their properties in the bottom panel.
4. feed those two plots back into the script using the -a option, with the left-most plot first, followed by the right-most plot. For example, in the provided dataset in this repo, that would be -a 117,118
