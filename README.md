This script is used to convert plots of land given in a particulat csv format into geojson format.

There are several assumptions about this data:

1. all the plots are square.
2. all the plots are aliged to one another. (though, they may not be aligned to latitude and longitude lines! see the --adjacent-plots parameter)

# Usage

`usage: convert_plots.py [-h] -a PLOTS filename`
    
where PLOTS are two, comma seperated plot id's that are to the left/right of each other. this is used to calculate the angle that the plots align, relative to latitude and longitude lines.

example using provided csv, where plots 117 and 118 are adjacent plots:

`python convert_plots.py plots.csv -a 117,118 > output.json`
