import os
import pickle
import datetime
import networkx as nx
import random
import osmnx as ox
from staticmap import StaticMap, Line, CircleMarker
import pandas as pd


# We define the map constants and parameters
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
LINE_SIZE = 2
INFINITE_TIME = float('inf')
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'
COLOR_CONGESTIONS = ['silver', 'aqua', 'lime', 'orange', 'red', 'darkred', 'black']
TIME_MULTIPLIER = [2.3, 1.5, 3.0, 4.5, 7.5, 13.0, INFINITE_TIME]


def download_graph(place):
    '''
    Downloads and returns the graph from the given place on earth (osmnx module required).
    The returned graph is a MultiDiGraph from the module networkx.
    '''

    # Get the MultiDiGraph from the given place and for driving purposes.
    graph = ox.graph_from_place(place, network_type='drive', simplify=True)

    # We convert the graph to a Digraph to only have at most one edge for each pair of vertices.
    graph = ox.utils_graph.get_digraph(graph, weight='length')

    # We convert it to a MultiDiGraph (because its the type of graphs Osmnx uses)
    graph = nx.MultiDiGraph(graph)

    return graph


def download_highways(url):
    '''
    Downloads the information concerning the fastest streets of the city (called "highways").
    Input: URL with a csv file of the highways and their information.
    Output: Pandas DataFrame
    '''
    return pd.read_csv(url)


def download_congestions(url):
    '''
    Downloads the information concerning the congestions of the highways (fastest streets of the city).
    Input:  URL with a csv file of the highways and their information.
    Output: Pandas DataFrame with the given information
    '''
    return pd.read_csv(url, sep='#', names=['Tram', 'Data', 'Congestio_actual', 'Congestio_prevista'])


def save_graph(graph, filename):
    '''Saves the given graph into the given filename.
    Input: - Networkx Graph
           - name of the file where we want to save the graph
    No output.
    '''
    with open(filename, 'wb') as file:
        pickle.dump(graph, file)


def load_graph(filename):
    '''
    Loads the graph stored in the given filename.
    Input:  name of the file we want to load.
    Output: Networkx Graph
    Prec: The file from the input exists
    '''
    assert exists_graph(filename), f"No such file or directory: '{filename}'"

    with open(filename, 'rb') as file:
        graph = pickle.load(file)
        return graph


def exists_graph(filename):
    '''
    Returns a boolean that tells if the filename containing the graph is created
    Input: name of the file we want to check.
    Ouput: boolean (true if the file exists, false otherwise).
    Attention: it does not check if the filename contains a graph, only if the file exists,
    so be careful with the names you use to save the graph.
    '''
    return os.path.isfile(filename)


def get_graph():
    '''
    Returns the graph of PLACE (see global variable), if the graph doesn't exist, it downloads it and saves it.
    Output: Networkx MultiDiGraph with an additional edge attribute, itime, containing
    the minimum time it takes to cross every edge of the graph. This attribute will further be
    modified to be adjusted to the congestions of PLACE.
    '''
    if not exists_graph(GRAPH_FILENAME):
        graph = download_graph(PLACE)
        get_initial_itime(graph)  # we create the additional attribute
        save_graph(graph, GRAPH_FILENAME)
    else:
        graph = load_graph(GRAPH_FILENAME)

    return graph


def get_initial_itime(graph):
    '''Given a graph, creates a new attribute, itime (in seconds), with the optimal time for each edge.
    Note that the itime calculated in this method is not the final itime, it does not take into account
    the congestions.
    Input: Networkx MultiDiGraph (Osmnx Graph) graph.
    No output.
    '''
    nx.set_edge_attributes(graph, 0, 'itime')
    for u, v, attr in graph.edges(data=True):
        # length is in meters
        # maxspeed is in km/h
        # itime is in seconds
        length = attr['length']
        try:
            attr['itime'] = length / float(attr['maxspeed']) * 3.6  # conversion to seconds
        except:  # there are few edges without maxspeed information
            # we adjust itime for theses edges based on their lengths
            if length < 500:
                attr['itime'] = length / 10.0 * 3.6
            elif length < 1000:
                attr['itime'] = length / 30.0 * 3.6
            elif length > 1000:
                attr['itime'] = length / 50.0 * 3.6


def get_igraph(graph):
    '''
    Input: Networkx MultiDiGraph (OSmnx Graph) graph, containing the initial values of the attribute itime.
    Output: Networkx MultiDiGraph (OSmnx Graph) igraph, containing the adjusted attribute itime with the congestions of PLACE.
    Prec: The graph must be not empty and must be the PLACE graph from osmnx.
    '''
    highways = download_highways(HIGHWAYS_URL)
    congestions = download_congestions(CONGESTIONS_URL)
    return build_igraph(graph, highways, congestions)


def build_igraph(graph, highways, congestions):
    '''
    Returns the igraph, which incorporates the notion of itime adjusted to the congestions of the graph's place
    Input: - Networkx MultiDiGraph (OSmnx Graph) graph: already includes the initial values of itime.
           - DataFrame highways: contains the different highways and their coordinates.
           - DataFrame congestions: contains the level of congestion of the highways, but without the coordinates.
    Output: Networkx MultiDiGraph (OSmnx Graph) igraph.
    Prec: The igraph given must have an attribute called "itime".
    '''
    igraph = graph.copy()

    # we merge highways and congestions to have the coordinates and the level of congestion in the same place
    highways_and_congestions = pd.merge(
        left=highways, right=congestions, left_on='Tram', right_on='Tram')

    for index, row in highways_and_congestions.iterrows():

        coordinates = row['Coordenades']
        coordinates = list(map(float, coordinates.split(',')))

        # we create the nodes that form the section ("tram")
        nodes = [(coordinates[i+1], coordinates[i]) for i in range(0, len(coordinates), 2)]

        # get_nearest_node() takes points as (latitude, longitude) tuples, which is the opposite of what we get from the Ajuntament.
        # for each segment, we assign the congestion to all the edges of the shortest path from one end of the segment to the other.
        # we are actually modifying itime attribute based on the congestion (see update_itime).
        node1 = ox.distance.get_nearest_node(igraph, nodes[0])  # nodes[0] is the initial end
        for i in range(1, len(nodes)):  # for every edge in the segment of the highway

            node2 = ox.distance.get_nearest_node(igraph, nodes[i])

            try:  # if the path is from node1 to node2
                route = ox.shortest_path(igraph, node1, node2, weight='itime')
                # update itime
                update_itime(igraph, route, TIME_MULTIPLIER[row['Congestio_actual']])
            except nx.NetworkXNoPath:
                try:  # if the path is from node2 to node 1
                    route = ox.shortest_path(igraph, node2, node1, weight='itime')
                    # update itime
                    update_itime(igraph, route, TIME_MULTIPLIER[row['Congestio_actual']])
                except nx.NetworkXNoPath:  # there is no path between the nodes, only happens in a few cases
                    pass

            node1 = node2

    return igraph


def update_itime(igraph, route, multiplier):
    '''
    Given the route from a segment, update the itime of the igraph using the factor multiplier (see global variable TIME_MULTIPLIER).
    Input: - igraph (Networkx MultiDiGraph (Osmnx Graph)).
           - route (list of Node IDs).
           - multiplier (float): multiplies itime.
    No output.
    Prec:  - The igraph must have:
               - the given nodes from route.
               - the attribute "itime".
               - at most one edge between two nodes.
    '''
    for i in range(len(route)-1):
        # we put 0 as a key because its a MultiDigraph but with at most one edge between two nodes.
        igraph[route[i]][route[i+1]][0]['itime'] *= multiplier

    return


def get_shortest_path_with_itimes(igraph, origin, destination):
    '''
    Given an igraph, an origin and a destination, finds the shortest path using the concept of itime.
    Input: - igraph (Networkx MultiDiGraph (OSmnx Graph)).
           - origin (has to be in the format (latitude, longitude)).
           - destination (has to be in the format (latitude, longitude)).
    Output:
           - image_filename: name of the file in which the path is plotted.
           - distance: approximate distance from the given origin to the given destination.
    Prec:
           - the igraph given must have an attribute called "itime".
    '''

    # This print is for testing purposes, uncomment it to see when the shortest path begins.
    # print("Shortest path beginning...")

    route_map = StaticMap(SIZE, SIZE)

    # We convert the (latitude, longitude) format into an ID of a node in the igraph.
    origin = ox.distance.get_nearest_node(igraph, origin)
    destination = ox.distance.get_nearest_node(igraph, destination)

    # We search the shortest path from origin to destination.
    route = ox.shortest_path(igraph, origin, destination, weight='itime')

    # We convert each node ID of the path into the format (longitude, latitude).
    coordinates = [[igraph.nodes[node]['x'], igraph.nodes[node]['y']] for node in route]

    # We add the path in the map.
    line = Line(coordinates, 'blue', 4)
    route_map.add_line(line)

    # We mark the beginning/origin of the path.
    route_map.add_marker(CircleMarker(coordinates[0], 'white', 18))
    route_map.add_marker(CircleMarker(coordinates[0], 'red', 12))

    # We mark the end/destination of the path.
    route_map.add_marker(CircleMarker(coordinates[-1], 'white', 18))
    route_map.add_marker(CircleMarker(coordinates[-1], 'green', 12))

    # We save the image into a file
    image = route_map.render()
    image_filename = "temp%d.png" % random.randint(1000000, 9999999)
    image.save(image_filename)

    # We approximate the distance of the path
    distance = sum([igraph[route[i]][route[i+1]][0]['length'] for i in range(len(route)-1)])

    # This print is for testing purposes, uncomment it to see when the shortest path ends.
    # print("...Shortest path finished")

    return image_filename, round(distance, 1)


def get_lat_lon(query):
    '''
    Given a name of a location (query) as a string,
    returns its coordinates in the format (latitude, longitude)
    '''
    return ox.geocoder.geocode(query)


def get_location_image(lat_lon):
    '''
    Given a location, specified by latitude and longitude, generates a PNG temporary
    image of that location in the map, which is saved using a random number as a filename.
    Input:
           - A latitude, longitude pair.
    Output:
           - Filename of the generated image: temp random number
    '''
    lat, lon = lat_lon

    # Saves the map in order to add the marker
    user_map = StaticMap(SIZE-200, SIZE-200)

    # Add the marker to the given location
    user_map.add_marker(CircleMarker((lon, lat), 'white', 24))
    user_map.add_marker(CircleMarker((lon, lat), 'red', 18))

    # Generates and saves the image, as it will be a temporary
    # file it receives a distinctive name.
    image = user_map.render()
    image_filename = "temp%d.png" % random.randint(1000000, 9999999)
    image.save(image_filename)

    return image_filename


def plot_graph(graph):
    '''
    Plots the given MultiDiGraph graph, and saves the image in the file barcelona_graph.png
    We need to save the image because of a known issue with windows users, who can't see the plot directly

    Prec: The graph must be not empty
    '''
    fig, ax = ox.plot_graph(graph, show=True, save=True, filepath='barcelona_graph.png')


def plot_highways(highways, image_filename, size):
    '''
    Saves the plot of highways in the given image_filename with the given size.
    Input: - highways (DataFrame).
           - image_filename (name of the file where you want to save the plot).
           - size of the image.
    No Output.
    '''
    place_map = StaticMap(size, size)
    for coordinates in highways['Coordenades']:

        # we separate the coordinates and put them in a list
        coordinates = list(map(float, coordinates.split(',')))

        # we create the nodes that form the section ("tram")
        coordinates = [[coordinates[i], coordinates[i+1]] for i in range(0, len(coordinates), 2)]

        # we paint the section in the map
        pol = Line(coordinates, 'blue', LINE_SIZE)
        place_map.add_line(pol)

    image = place_map.render()
    image.save(image_filename)  # we save the image into our directory


def plot_congestions(highways, congestions, image_filename, size):
    '''
    Translates the information of highways and their congestions into a map (the plot) using a color coding.
    Saves the map in the image_filename given using the given size of the image.
    Input: - highways (DataFrame).
           - congestions (DataFrame).
           - image_filename (name of the file you want to save the plot).
           - size of the image.
    No Output.

    The color coding is the following:
    silver --> no data
    aqua --> very fluid
    lime --> fluid
    orange --> dens
    red --> heavy traffic
    darkred --> jam
    black --> cut off
    '''

    highways_and_congestions = pd.merge(
        left=highways, right=congestions, left_on='Tram', right_on='Tram')

    place_map = StaticMap(size, size)

    for index, row in highways_and_congestions.iterrows():
        coordinates = row['Coordenades']

        # we separate the coordinates and put them in a list
        coordinates = list(map(float, coordinates.split(',')))

        # we create the nodes that form the section ("tram")
        coordinates = [[coordinates[i], coordinates[i+1]] for i in range(0, len(coordinates), 2)]

        # we paint the section in the map using the color coding for each congestion
        pol = Line(coordinates, COLOR_CONGESTIONS[row['Congestio_actual']], LINE_SIZE)
        place_map.add_line(pol)

    image = place_map.render()
    image.save(image_filename)  # we save the image into our directory


# See the results of download_highways, download_congestions
# def main():
#    graph = get_graph()
#    plot_graph(graph)
#    highways = download_highways(HIGHWAYS_URL)
#    congestions = download_congestions(CONGESTIONS_URL)
#    plot_highways(highways, 'highways.png', SIZE)
#    plot_congestions(highways, congestions, 'congestions.png', SIZE)
#
# if __name__ == "__main__":

# main()
