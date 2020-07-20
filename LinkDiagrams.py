import networkx as nx
import random
import tqdm

def random_regular_multigraph(num_nodes: int, valence: int) -> nx.MultiGraph:
    G = nx.MultiGraph()
    # num_nodes = random.randint(0,max_nodes)

    for i in range(num_nodes):
        G.add_node(i)

    nodes = list(G.nodes)

    # add edges until graph is `valence`-regular
    for node in nodes:
        while G.degree(node) < valence:
            # this condition ensures new edge doesn't result in degree `valence + 1` node
            if G.degree(node) == valence-1:
                n = random.choice([c for c in nodes 
                                   if c != node 
                                   and G.degree(c) < valence])
            else:
                n = random.choice([c for c in nodes
                                   if G.degree(c) < valence])

            G.add_edge(node, n)

    # test regularity
    for n in nodes:
        assert G.degree(n) == valence

    return G

def convert_multigraph_to_graph(G: nx.MultiGraph) -> nx.Graph:
    H = nx.Graph()
    for i in list(G.nodes()):
        for j in list(G[i]):
            H.add_edge(i, j)
    
    return H

def give_random_vertex_2_coloring(G: nx.MultiGraph, attribute_name: str='color') -> None:
    """Augments the input MultiGraph with a random vertex 2-coloring.
    The colors are represented by booleans."""
    for i in range(len(list(G.nodes))):
        G.nodes[i][attribute_name] = random.choice([True, False])
    
    return None

def _augment_4rmg_with_anchors(G: nx.MultiGraph) -> None:
    """Gives edge data needed to define a knot diagram.
    Edges edges into a node are labeled by top-left, top-right, bottom-left, bottom-right."""
    # weak regularity test
    assert G.number_of_edges() == 4 * G.number_of_nodes() / 2

    # first initialize the dicts
    for crossing in list(G.nodes):
        neighbors = list(G.neighbors(crossing))
        for neighbor in neighbors:
            for i in list(G[crossing][neighbor]):
                G[crossing][neighbor][i][crossing] = []  # initialize dict

    # give the edges data which say how they are connected to crossings
    # edge data is {crossing: anchor}
    # do this randomly
    for crossing in list(G.nodes):
        anchors = ['tl', 'tr', 'bl', 'br']
        random.shuffle(anchors)
        neighbors = list(G.neighbors(crossing))
        for neighbor in neighbors:
            for i in list(G[crossing][neighbor]):
                if crossing == neighbor:
                    G[crossing][neighbor][i][crossing].append(anchors.pop()) 
                    G[crossing][neighbor][i][crossing].append(anchors.pop()) # do twice if edge is a loop
                else:
                    G[crossing][neighbor][i][crossing].append(anchors.pop())  # {attr: val} = {crossing: [anchors]}    
    return None

def _test_if_4rmgwa_is_link_diagram(G: nx.MultiGraph) -> bool:
    """Use edge data to convert each crossing into a 5 node subgraph in an 'X' shape.
    Convert the result from a multigraph to a graph and test planarity."""
    H = nx.MultiGraph(G)
    anchors = ['tl', 'tr', 'bl', 'br']
    for node in list(G.nodes):  # use old nodes
        H.add_nodes_from([(node, anchor) for anchor in anchors + ['center']])
        H.add_edges_from([((node, anchor), (node, 'center')) for anchor in anchors])    # add in the 'X'  
        for neighbor in list(G.neighbors(node)):    # use old edges      
            for i in list(G[node][neighbor]):
                for anchor in anchors:
                    if anchor in G[node][neighbor][i][node]:
                        if len(G[node][neighbor][i][node]) == 1:        # if edge is normal
                            H.add_edge(neighbor, (node, anchor))
                        else:                                           # if edge is loop
                            a = H[node][neighbor][i][node][:]           # make a copy
                            a.remove(anchor)
                            a = a[0]
                            H.add_edge((node, a), (node, anchor))       # NOTE: will end up with a double edge here in this case.
                                                                        #       but it will get taken care of before planarity check
                                                                        #       so it doesn't matter
    H.remove_nodes_from(list(G.nodes))
    H = convert_multigraph_to_graph(H)
    is_planar = nx.algorithms.planarity.check_planarity(H)[0]
    return is_planar

def random_link_diagram(num_crossings: int) -> nx.MultiGraph:
    """A knot diagram is a kind of vertex 2-clored, planar, 4-regular multigraph
    which keeps track of where the edges are in relation to the 'crossing' they go into.
    This function will return a random multigraph which satisfies the above.
    In particular, the edges will contain the data of how they are connected to the crossings."""
    is_planar = False
    tries = 0
    # keep fishing for graphs until we get a pre-vertex-colored link diagram
    while not is_planar:
        # generate a random 4-regular multigraph
        L = random_regular_multigraph(num_crossings, 4)
        _augment_4rmg_with_anchors(L)
        is_planar = _test_if_4rmgwa_is_link_diagram(L)
        tries += 1
    
    print(f"Successful fishing after {tries} attempts!")
     
    # randomly assign each crossing to be either positive or negative
    give_random_vertex_2_coloring(L)

    print(f"Node data: {L.nodes.data()}")
    print(f"Edge data: {L.edges.data()}")

    return L

def resolve_crossing_id(L: nx.MultiGraph, crossing: int) -> nx.MultiGraph:
    # make a duplicate 
    Link = nx.MultiGraph(L)
    # connect other end of top-left of crossing to other end of bottom-left
    for neighbor in list(Link.neighbors(crossing)):
        for i in list(Link[crossing][neighbor]):
            if 'tl' in Link[crossing][neighbor][i][crossing]:
                a = (neighbor, Link[crossing][neighbor][i][neighbor])
            
            if 'bl' in Link[crossing][neighbor][i][crossing]:
                b = (neighbor, Link[crossing][neighbor][i][neighbor])
    
    if a[0] == b[0]:
        Link.add_edges_from([ (a[0], b[0], {a[0]: [a[1], b[1]]}) ])
    else:
        Link.add_edges_from([ (a[0], b[0], {a[0]: [a[1]], b[0]: [b[1]]}) ])

    # connect other end of top-right of crossing to other end of bottom-right
    for neighbor in list(Link.neighbors(crossing)):
        for i in list(Link[crossing][neighbor]):
            if 'tr' in Link[crossing][neighbor][i][crossing]:
                a = (neighbor, Link[crossing][neighbor][i][neighbor])
            
            if 'br' in Link[crossing][neighbor][i][crossing]:
                b = (neighbor, Link[crossing][neighbor][i][neighbor])
    
    if a[0] == b[0]:
        Link.add_edges_from([ (a[0], b[0], {a[0]: [a[1], b[1]]}) ])
    else:
        Link.add_edges_from([ (a[0], b[0], {a[0]: [a[1]], b[0]: [b[1]]}) ])

    # remove crossing
    Link.remove_node(crossing)

    return Link

def resolve_crossing_cap_cup(L: nx.MultiGraph, crossing: int) -> nx.MultiGraph:
    # make a duplicate 
    Link = nx.MultiGraph(L)
    # connect other end of top-left of crossing to other end of bottom-left
    for neighbor in list(Link.neighbors(crossing)):
        for i in list(Link[crossing][neighbor]):
            if 'tl' in Link[crossing][neighbor][i][crossing]:
                a = (neighbor, Link[crossing][neighbor][i][neighbor])
            
            if 'tr' in Link[crossing][neighbor][i][crossing]:
                b = (neighbor, Link[crossing][neighbor][i][neighbor])
    
    if a[0] == b[0]:
        Link.add_edges_from([ (a[0], b[0], {a[0]: [a[1], b[1]]}) ])
    else:
        Link.add_edges_from([ (a[0], b[0], {a[0]: [a[1]], b[0]: [b[1]]}) ])

    # connect other end of top-right of crossing to other end of bottom-right
    for neighbor in list(Link.neighbors(crossing)):
        for i in list(Link[crossing][neighbor]):
            if 'bl' in Link[crossing][neighbor][i][crossing]:
                a = (neighbor, Link[crossing][neighbor][i][neighbor])
            
            if 'br' in Link[crossing][neighbor][i][crossing]:
                b = (neighbor, Link[crossing][neighbor][i][neighbor])
    
    if a[0] == b[0]:
        Link.add_edges_from([ (a[0], b[0], {a[0]: [a[1], b[1]]}) ])
    else:
        Link.add_edges_from([ (a[0], b[0], {a[0]: [a[1]], b[0]: [b[1]]}) ])

    # remove crossing
    Link.remove_node(crossing)

    return Link

def kauffman_bracket_polynomial(L: nx.MultiGraph):
    pass