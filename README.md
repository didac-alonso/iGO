# iGO

iGo is a Barcelona GPS. To use it you must interact with a bot in telegram.

# Description

# Installation

Please check requirements.txt in order to install all needed libaries.

# iGO module
```python
import igo

igo.download_graph('Barcelona, Catalunya') # returns the Barcelona graph
igo.save_graph(graph, filename) #saves the graph using a given filename
igo.load_graph(filename) # loads the saved graph
igo.get_graph() # returns the barcelona graph, saving it previously, or loads it in case that was saved before.
igo.get_igraph(graph) # returns the igraph, which is the graph with extra parameter called itime.
igo.get_lat_lon(place) # returns the coordinates from the place specified
igo.plot_congestions(highways, image_filename, size) # saves an image of the map with the congestions marked in different colors
igo.plot_highways(highways, congestions, image_filename, size) # saves an image of the map with the highways drawn
igo.get_location_image(lat_lon) # Saves an image of the map with the location given marked, and returns its name, since it is random

```

# bot module
```python

```

# Bot usage:

In telegram, there are the following instructions:

/start:

/help:

/authors:

/go destination:

/where:


# Authors
