import csv
import os
import pickle
import urllib
import networkx as nx
import matplotlib.pyplot as plt
import osmnx as ox
import haversine
from staticmap import StaticMap, Polygon, Line
import pandas as pd
import collections
import matplotlib.pyplot as plt

Highway = collections.namedtuple('Highway', 'coordinates')  # Tram
Congestion = collections.namedtuple('Congestion', 'coordinates')

# We define the map constants and parameters
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'
COLOR_CONGESTIONS = ['white', 'green', 'greenyellow',
                     'orange', 'tomato', 'red', 'black']

# Segun tengo entendido, el orden es:
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
    plt.close('all')

    return


def plot_highways(highways, image_file, size):
    '''Input: - highways (DataFrame)
              - image_file (name of the file you want to save the plot)
              - size of the image (the map or plot)
    Translates the information of highways into a map (the plot).
    Saves the map in the image_file and plots it.
    '''
    bcn_map = StaticMap(size, size)
    for coordinates in highways['Coordenades']:
        # we separate the coordinates and put them in a list
        coordinates = list(map(float, coordinates.split(',')))
        coordinates = [[coordinates[i], coordinates[i+1]]
                       for i in range(0, len(coordinates), 2)]  # we create the nodes that form the section ("tram")
        pol = Line(coordinates, 'blue', 2)  # we paint the section in the map
        bcn_map.add_line(pol)

    image = bcn_map.render()
    image.save(image_file)  # we save the image into our directory


def plot_congestions(highways, congestions, image_file, size):
    '''Input: - highways (DataFrame)
              - congestions (DataFrame)
              - image_file (name of the file you want to save the plot)
              - size of the image (the map or plot)

    Translates the information of highways into a map (the plot) with their congestion
    Saves the map in the image_file and plots it.
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
        pol = Line(coordinates, COLOR_CONGESTIONS[row['Congestio_actual']], 2)
        bcn_map.add_line(pol)

    image = bcn_map.render()
    image.save(image_file)


def build_igraph(graph, highways, congestions):
    pass


def get_shortest_path_with_ispeeds(igraph, origin, destination):
    pass


def plot_path(igraph, ipath, size):
    pass


def main():
    if exists_graph(GRAPH_FILENAME):
        graph = load_graph(GRAPH_FILENAME)
    else:
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)

    plot_graph(graph)

    print("hello")

    highways = download_highways(HIGHWAYS_URL)
    plot_highways(highways, 'highways.png', SIZE)

    congestions = download_congestions(CONGESTIONS_URL)
    plot_congestions(highways, congestions, 'congestions.png', SIZE)

    igraph = build_igraph(graph, highways, congestions)


if __name__ == "__main__":
    main()
