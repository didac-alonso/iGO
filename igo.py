import csv
import os
import pickle
import urllib
import datetime
import networkx as nx
import random
import matplotlib.pyplot as plt
import osmnx as ox
import haversine
from staticmap import StaticMap, Polygon, Line, CircleMarker, IconMarker
import pandas as pd
import collections
import matplotlib.pyplot as plt

Highway = collections.namedtuple('Highway', 'coordinates')  # Tram
Congestion = collections.namedtuple('Congestion', 'coordinates')

# We define the map constants and parameters
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
LINE_SIZE = 2
INFINITE_TIME = float('inf')
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'
COLOR_CONGESTIONS = ['silver', 'aqua', 'lime', 'orange', 'red', 'darkred', 'black']
TIME_MULTIPLIER = [1.0, 1.0, 1.5, 2, 2.5, 3.0, INFINITE_TIME]

# Según tengo entendido, el orden es:
# 0 --> sense dades
# 1 --> molt fluid
# 2 --> fluid
# 3 --> dens
# 4 --> molt dens
# 5 --> congestió
# 6 --> tallat


def download_graph(place):
    '''Downloads the graph from the given place.
    The returned graph is a Directed Graph from the module networkx'''
    graph = ox.graph_from_place(place, network_type='drive', simplify=True)
    # We convert the graph to a Digraph to only have at most one edge for each pair of vertex
    graph = ox.utils_graph.get_digraph(graph, weight='length')
    # We convert it to a MultiDiGraph (because its the type of Graphs OSmnx uses)
    graph = nx.MultiDiGraph(graph)

    return graph


def download_highways(url):
    '''Downloads the information concerning the fastest streets of the city
    The method returns a DataFrame'''
    return pd.read_csv(url)


def download_congestions(url):
    '''Downloads the information concerning the congestions of the highways
    The method returns a DataFrame'''
    return pd.read_csv(url, sep='#', names=['Tram', 'Data', 'Congestio_actual', 'Congestio_prevista'])


def save_graph(graph, filename):
    '''Saves the given graph in the given filename'''
    with open(filename, 'wb') as file:
        pickle.dump(graph, file)


def load_graph(filename):
    '''loads the graph stored in the filename'''
    with open(filename, 'rb') as file:
        graph = pickle.load(file)
    return graph


def exists_graph(filename):
    '''Returns a boolean that tells if the filename containing the graph is created
    Attention: it does not check if the filename contains a graph, only if the file exists,
    so be careful with the names you use to save the graph'''
    return os.path.isfile(filename)


def plot_graph(graph):
    '''Plots the given MultiDiGraph graph'''
    fig, ax = ox.plot.plot_graph(graph)
    return


def get_graph():
    '''Returns the graph of the GPS'''
    if not exists_graph(GRAPH_FILENAME):
        graph = download_graph(PLACE)
        get_initial_time(graph)
        save_graph(graph, GRAPH_FILENAME)
    else:
        graph = load_graph(GRAPH_FILENAME)

    return graph


def get_igraph(graph):
    highways = download_highways(HIGHWAYS_URL)
    congestions = download_congestions(CONGESTIONS_URL)
    return build_igraph(graph, highways, congestions)


def download_highways(url):
    '''Downloads the information concerning the fastest streets of the city
    The method returns a DataFrame'''
    df = pd.read_csv(url, usecols=['Tram', 'Descripció', 'Coordenades'])
    return df


def plot_highways(highways, image_filename, size):
    '''Input: - highways (DataFrame)
              - image_filename (name of the file you want to save the plot)
              - size of the image (the map or plot)
    Translates the information of highways into a map (the plot).
    Saves the map in the image_filename and plots it.
    '''
    bcn_map = StaticMap(size, size)
    for coordinates in highways['Coordenades']:
        # we separate the coordinates and put them in a list
        coordinates = list(map(float, coordinates.split(',')))
        coordinates = [[coordinates[i], coordinates[i+1]]
                       for i in range(0, len(coordinates), 2)]  # we create the nodes that form the section ("tram")
        pol = Line(coordinates, 'blue', LINE_SIZE)  # we paint the section in the map
        bcn_map.add_line(pol)

    image = bcn_map.render()
    image.save(image_filename)  # we save the image into our directory


def plot_congestions(highways, congestions, image_filename, size):
    '''Input: - highways (DataFrame)
              - congestions (DataFrame)
              - image_filename (name of the file you want to save the plot)
              - size of the image (the map or plot)

    Translates the information of highways into a map (the plot) with their congestion
    Saves the map in the image_filename and plots it.
    '''
    highways_and_congestions = pd.merge(
        left=highways, right=congestions, left_on='Tram', right_on='Tram')

    bcn_map = StaticMap(size, size)

    for index, row in highways_and_congestions.iterrows():
        coordinates = row['Coordenades']
        coordinates = list(map(float, coordinates.split(',')))
        # we create the nodes that form the section ("tram")
        coordinates = [[coordinates[i], coordinates[i+1]] for i in range(0, len(coordinates), 2)]
        # we paint the section in the map using the color coding for each congestion
        pol = Line(coordinates, COLOR_CONGESTIONS[row['Congestio_actual']], LINE_SIZE)
        bcn_map.add_line(pol)

    image = bcn_map.render()
    image.save(image_filename)


def get_initial_time(graph):
    '''Creates a new attribute, itime (in seconds), with the optimal time for each edge'''
    nx.set_edge_attributes(graph, 0, 'itime')
    for u, v, attr in graph.edges(data=True):
        # length is in meters
        # maxspeed is in km/h
        # itime is in seconds
        length = attr['length']
        try:
            attr['itime'] = length / float(attr['maxspeed']) * 3.6
        except:  # there are some edges without maxspeed information
            if length < 500:  # street with length smaller than 500 meters.
                attr['itime'] = length / 10.0 * 3.6
            elif length < 1000:
                attr['itime'] = length / 30.0 * 3.6
            elif length > 1000:
                attr['itime'] = length / 50.0 * 3.6


def build_igraph(graph, highways, congestions):
    '''Returns the igraph, which incorporates the notion of itime'''
    igraph = graph.copy()
    highways_and_congestions = pd.merge(
        left=highways, right=congestions, left_on='Tram', right_on='Tram')

    for index, row in highways_and_congestions.iterrows():
        coordinates = row['Coordenades']
        coordinates = list(map(float, coordinates.split(',')))
        # we create the nodes that form the section ("tram")
        nodes = [(coordinates[i+1], coordinates[i]) for i in range(0, len(coordinates), 2)]
        # get_nearest_node() takes points as (latitude, longitude) tuples, which is the opposite of what we get from the Ajuntament.

        node1 = ox.distance.get_nearest_node(igraph, nodes[0])  # nodes[0] is the initial
        for i in range(1, len(nodes)):  # for every edge in the segment of the highway
            # nodes[i+1] is the other extrem of the segment
            node2 = ox.distance.get_nearest_node(igraph, nodes[i])
            try:
                route = ox.shortest_path(igraph, node1, node2, weight='length')
                update_congestions(igraph, route, TIME_MULTIPLIER[row['Congestio_actual']])
            except nx.NetworkXNoPath:
                try:
                    route = ox.shortest_path(igraph, node2, node1, weight='length')
                    update_congestions(igraph, route, TIME_MULTIPLIER[row['Congestio_actual']])

                except nx.NetworkXNoPath:  # there is no path between the nodes, only happens in a few cases
                    pass
            node1 = node2

    return igraph


def update_congestions(igraph, route, multiplier):
    '''Given the route from a segment, update the itime of the igraph using the factor multiplier'''
    for i in range(len(route)-1):
        # we put 0 as a key because its a MultiDigraph but with at most one edge between two nodes
        igraph[route[i]][route[i+1]][0]['itime'] *= multiplier

    return


def get_shortest_path_with_itimes(igraph, origin, destination):
    '''Given an igraph and an origin and a destination in the format (latitude, longitude), finds the
    shortest path using the concept of itime'''

    print("shortest path beginning")
    route_map = StaticMap(SIZE, SIZE)
    # we convert the (latitude, longitude) format into an ID of a node in the igraph
    origin = ox.distance.get_nearest_node(igraph, origin)
    destination = ox.distance.get_nearest_node(igraph, destination)
    route = ox.shortest_path(igraph, origin, destination, weight='itime')
    # we convert each node ID of the path into the format (longitude, latitude)
    coordinates = [[igraph.nodes[node]['x'], igraph.nodes[node]['y']] for node in route]

    line = Line(coordinates, 'blue', 4)
    route_map.add_line(line)
    # We mark the beginning/origin of the path
    route_map.add_marker(CircleMarker(coordinates[0], 'white', 18))
    route_map.add_marker(CircleMarker(coordinates[0], 'red', 12))

    # We mark the end/destination of the path
    route_map.add_marker(CircleMarker(coordinates[-1], 'white', 18))
    route_map.add_marker(CircleMarker(coordinates[-1], 'green', 12))

    image = route_map.render()
    image_filename = "temp%d.png" % random.randint(1000000, 9999999)
    image.save(image_filename)

    # We approximate the duration of the path
    aprox_time = sum([igraph[route[i]][route[i+1]][0]['itime'] for i in range(len(route)-1)])
    aprox_time = datetime.timedelta(seconds=int(aprox_time))

    # We approximate the distance of the path
    distance = sum([igraph[route[i]][route[i+1]][0]['length'] for i in range(len(route)-1)])

    print(aprox_time, round(distance, 2))

    return image_filename, aprox_time, round(distance, 1)


def get_lat_lon(query):
    return ox.geocoder.geocode(query)


def get_location_image(lat_lon):
    lat, lon = lat_lon
    user_map = StaticMap(SIZE-200, SIZE-200)
    user_map.add_marker(CircleMarker((lon, lat), 'white', 24))
    user_map.add_marker(CircleMarker((lon, lat), 'red', 18))
    image = user_map.render()
    image_filename = "temp%d.png" % random.randint(1000000, 9999999)
    image.save(image_filename)
    return image_filename


# def main():
    # print("hello")
    # igraph = get_graph()
    # # a = graph.get_edge_data(8465686548, 2844600654)
    # # print(a)
    # # print(ox.basic_stats(graph))
    # # print(ox.extended_stats(graph))
    # # graph.edges
    # highways = download_highways(HIGHWAYS_URL)
    # congestions = download_congestions(CONGESTIONS_URL)
    # # print(graph.nodes[2844600654])
    # # print(a)
    # igraph = build_igraph(igraph, highways, congestions)
    # # a = graph.get_edge_data(8465686548, 2844600654)
    # # route = ox.shortest_path(graph, 8465686548, 2844600654)

    # get_shortest_path_with_itimes(igraph, (41.408154, 2.184601), (41.397991, 2.140705))
    # # print(nodes_proj.loc[route])
    # # print(a)
    # # plot_graph(graph)
    # # plot_highways(highways, 'highways.png', SIZE)

    # # plot_congestions(highways, congestions, 'congestions.png', SIZE)

    # # igraph = build_igraph(graph, highways, congestions)


# if __name__ == "__main__":
#     main()
