# iGO DJ

Get the best out of Barcelona with iGo DJ!



## Description

iGo is a Barcelona GPS with which you can use by interacting with its Telegram Bot.

After giving him your position and your destination (using command /go, see section Bot usage), iGo will give you the best route by car/motorcycle to get there.

iGo combines [OpenStreetMap](https://www.openstreetmap.org/#map=6/40.007/-2.488) with traffic data given by Barcelona's local government (see [1](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/transit-relacio-trams) and [2](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/trams))
in order to take into account more than just distances and speeds. As a consequence, the results are more reliable and can surely save you some time.

## Installation

Please check requirements.txt in order to install all needed libraries.

The listed libraries in this file are not python standard libraries.

Make sure you have Python3 installed in your computer.

## igo module

This module integrates all the funcionalities concerning the Barcelona map and its traffic. Its goal is to get both information and merge them into one unique graph where the notion of itime (smart time) is calculated. Moreover, once this is done, its mission is to help the Bot module with tasks like finding the shortest path from an origin to a destination or showing the current location of the user.

It also incorporates some methods to visualize in a map the data given from osmnx (the graph of Barcelona) and the local government: that is, the traffic in Barcelona and the streets where the local government monitors congestions (sometimes, no data can be given).


The main library used in this module is Osmnx. It is used to extract the graph from Barcelona in OpenStreetMap, incorporate the new attribute itime into the graph and get the shortest path using the latter, among others.

The attribute itime is created by merging the *maxspeed* and the *length* of each edge in the graph (given by Osmnx) and the *level of congestion* given by the local government. Nonetheless, traffic data is not available for all the streets in the graph. For these cases, itime is the optimal time for that given street. Moreover, some streets in the graph lack of maxspeed data. In this case, we have adjusted the speed to the actual regulations and to what we thought would make sense depending on the length of the street (see get_initial_itime method).

To store the data from Barcelona's local government, we use pandas python library because it's easy to use and helps understand the code faster.

These are the methods it incorporates:

```python
import igo

igo.download_graph('Barcelona, Catalunya') # Returns the Barcelona graph
igo.save_graph(graph, filename) # Saves the graph using a given filename
igo.load_graph(filename) # Loads the saved graph
igo.get_graph() # returns the barcelona graph, saving it previously, or loads it in case that was saved before.
igo.get_igraph(graph) # returns the igraph, which is the graph with extra parameter called itime.
igo.get_lat_lon(place) # returns the coordinates from the place specified
igo.plot_congestions(highways, image_filename, size) # saves an image of the map with the congestions marked in different colors
igo.plot_highways(highways, congestions, image_filename, size) # saves an image of the map with the highways drawn
igo.get_location_image(lat_lon) # Saves an image of the map with the location given marked, and returns its name, since it is random

# Faltan metodos
```
To get more information about what each method does, simply write the following lines in a python console in the directory where the igo.py is located:

```python
>>> import igo
>>> help(igo)
```


## bot module

This module is in charge of interacting with Telegram users by means of a bot.
It's the middleman between Telegram and the igo module.

Using some of the functionalities of the latter, it finds the shortest path between the user's current location and the given destination, and can also give a map of the user's surroundings (by using the command /where).

These are the methods it incorporates:

```python
#poner metodos aqui ----------------------------------------------------------------
```

To get more information about what each method does, simply write the following lines in a python console in the directory where the bot.py is located:

```python
>>> import bot
>>> help(bot)
```




## Bot usage

In order to interact with the iGo bot, the user has to write commands. Let's take a look at what they can do:

**/start**:

**/help**:

**/authors**:

**/go destination**: Finds the shortest path from the user's current location to the given destination.
                   The destination can either be given in the form of an address or in the form of coordinates.
                   IMPORTANT: in the case of coordinates, they have to be in the order latitude, longitude.

**/where**:


# Authors
