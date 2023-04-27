
import networkx as nx
from pathlib import Path
from networkx.drawing import nx_agraph
import pydot

def convertEntryLabelToFunction(label):
    return label.split(" ")[1][:-2] + " function"

def dfs_edges(G,source):
    nodes=[source]
    visited=set()
    parent_dict = {}
    for start in nodes:
        if start in visited:
            continue
        visited.add(start)
        stack = [(start,iter(G[start]))]
        while stack:
            parent,children = stack[-1]
            try:
                child = next(children)
                if 'call' in G.nodes[child]['label'] or 'ENTRY' in G.nodes[child]['label']:
                    if child not in visited:
                        if 'call' in G.nodes[child]['label']:
                            parent_dict[child] = parent
                            visited.add(child)
                        else:
                            yield parent_dict[parent],child
                        stack.append((child,iter(G[child])))
            except StopIteration:
                stack.pop()

def filteredEdges(G, filter):
    edgeToBeRemoved = []
    for e in G.edges(data=True,keys=True):
        if G[e[0]][e[1]][e[2]]["label"] in filter:
            edgeToBeRemoved.append((e[0],e[1],e[2]))
    G.remove_edges_from(edgeToBeRemoved)
    return G


def addSubgraphFromNode(G,digraph,node, nodeColor, opened):
    nodes_in_subgraph = list(nx.dfs_preorder_nodes(digraph, node))
    function_nodes = set()
    if nodes_in_subgraph is not None:
        nodes_in_subgraph.pop(0)
        for n in nodes_in_subgraph:
            node_val = digraph.nodes[n]
            if('ENTRY' in node_val['label'] and n not in opened):
                function_nodes.add(n)
            if n not in G.nodes():
                G.add_node(n,shape=node_val['shape'],label=node_val['label'], fillcolor = nodeColor, style = "filled")
        edges_in_subgraph = nx.edge_dfs(digraph, node)
        edge_label = nx.get_edge_attributes(digraph, 'label')
        edge_color = nx.get_edge_attributes(digraph, 'color')
        edge_style = nx.get_edge_attributes(digraph, 'style')
        for e in edges_in_subgraph:
            l = edge_label[e] if e in edge_label else None
            s = edge_style[e] if e in edge_style else None
            c = edge_color[e] if e in edge_color else None
            if s is not None and c is not None: 
                G.add_edge(e[0],e[1], key = e[2], label = l, style = s,color = c)
            elif s is not None:
                G.add_edge(e[0],e[1], key = e[2], label = l, style = s)
            elif c is not None:
                G.add_edge(e[0],e[1], key = e[2], label = l, color = c)
            else:
                G.add_edge(e[0],e[1], key = e[2], label = l)
    for fnode in function_nodes:
        nodes_in_fnode = list(nx.dfs_preorder_nodes(digraph, fnode))
        nodes_in_fnode = [n for n in nodes_in_fnode if n not in function_nodes]
        G.remove_nodes_from(nodes_in_fnode)
    return G


def edgeFilter(actualDotSource, excludedEdges, dotSource, opened, nodeToColorMap):
    digraph = nx_agraph.from_agraph(pygraphviz.AGraph(actualDotSource))
    G = nx_agraph.from_agraph(pygraphviz.AGraph(dotSource))
    for n in opened:
        color = nodeToColorMap[n]
        G = addSubgraphFromNode(G,digraph,n, color, opened)
    G = filteredEdges(G,excludedEdges)
    return nx.nx_pydot.to_pydot(G).to_string()

def openFunctionCluster(actualDotSource,node,open_bool, dotSource, excludedEdges, color,opened):
    digraph = getGraphFromDotString(actualDotSource)
    G = getGraphFromDotString(dotSource)
    node_label = G.nodes[node]["label"]
    if("function" not in node_label):
        return dotSource, '', node_label
    if open_bool:
        G = addSubgraphFromNode(G,digraph, node, color, opened)
        G = filteredEdges(G,excludedEdges)
    else:
        nodes_in_subgraph = list(nx.dfs_preorder_nodes(G, node))
        nodes_in_subgraph.pop(0)
        G.remove_nodes_from(nodes_in_subgraph)
    return nx.nx_pydot.to_pydot(G).to_string(), color, node_label
    

def dotToPngv2(filename):
    digraph = nx.nx_pydot.read_dot(filename)
    root_nodes = [n for n,d in digraph.in_degree() if d==0] 
    G = nx.MultiDiGraph()
    for n in digraph.nodes():
        node = digraph.nodes[n]
        if 'ENTRY' in node['label']:
            G.add_node(n,shape = node['shape'],label = convertEntryLabelToFunction(node['label']))
    for root in root_nodes:
        G.add_edges_from(dfs_edges(digraph,root),label = "FUNC_CALL")
    return G

def getGraphFromDotString(dotSource):
    graphs = pydot.graph_from_dot_data(dotSource)
    digraph = nx.nx_pydot.from_pydot(graphs[0])
    return digraph

def dotToPng(dotSource):
    digraph = getGraphFromDotString(dotSource)
    root_nodes = [n for n,d in digraph.in_degree() if d==0] 
    G = nx.MultiDiGraph()
    for n in digraph.nodes():
        node = digraph.nodes[n]
        if not node: 
            continue
        if 'ENTRY' in node['label']:
            G.add_node(n,shape = node['shape'],label = convertEntryLabelToFunction(node['label']))
    for root in root_nodes:
        G.add_edges_from(dfs_edges(digraph,root),label = "FUNC_CALL")
    return nx.nx_pydot.to_pydot(G).to_string()

