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

# Descarreguem el graf
def download_graph(place):
    graph = ox.graph_from_place(place, network_type='drive', simplify=True)
    # si en aquesta linia fem ox.plot_graph(graph), si que el dibuixa
    # ox.plot_graph(graph)
    graph = ox.utils_graph.get_digraph(graph, weight='length')
    # en aquesta linea ja no funciona
    # ox.plot_graph(graph)
    return graph

# El guardem
def save_graph(graph, filename):
    with open(filename, 'wb') as file:
        pickle.dump(graph, file)

# El carreguem
# Preq: ha d'estar guardat
def load_graph(filename):
    with open(filename, 'rb') as file:
        graph = pickle.load(file)
    return graph

# Comproba si està guardat
def exists_graph(filename):
    return os.path.isfile(filename)


# Dibuixa el graf, no funciona.
def plot_graph(graph):
    # nx.draw(graph)
    nx.draw_networkx(graph)
    # ox.plot_graph(graph)


def main():
    if exists_graph(GRAPH_FILENAME):
        graph = load_graph(GRAPH_FILENAME)
    else:
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)

    # aqui comprovem el tipus per si estavem fent alguna cosa malament   
    print(type(graph))
    plot_graph(graph)


main()