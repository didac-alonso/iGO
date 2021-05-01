import csv
import os
import pickle
import urllib
import networkx as nx
import osmnx as ox
import haversine
import staticmap
import telegram
import collections

# We define the map constants and parameters
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'


def download_graph(place):
    graph = ox.graph_from_place(place, network_type='drive', simplify=True)
    graph = ox.utils_graph.get_digraph(graph, weight='length')
    return graph

def save_graph(graph, filename):
    with open(filename, 'wb') as file:
        pickle.dump(graph, file)
    
def load_graph(filename):
    with open(filename, 'rb') as file:
        graph = pickle.load(file)
    return graph

def exists_graph(filename):
    return os.path.isfile(filename)


def plot_graph(graph):
    # nx.draw(graph)
    nx.draw_networkx(graph)



def main():
    if exists_graph(GRAPH_FILENAME):
        graph = load_graph(GRAPH_FILENAME)
    else:
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)
    
    print(type(graph))
    plot_graph(graph)


main()