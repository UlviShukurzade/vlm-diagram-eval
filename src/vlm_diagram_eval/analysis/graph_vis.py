"""
visualiser for networkx structures
"""

import matplotlib.pyplot as plt
import networkx as nx


def draw_graph(graph):
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, arrows=True)
    plt.show()


netx = """
    {'nodes': [{'id': 'registry', 'label': 'Patch Registry', 'labelStyle': '', 'padding': 15, 'cssStyles': [], 'cssCompiledStyles': [], 'cssClasses': 'default ', 'domId': 'flowchart-registry-0', 'look': 'classic', 'isGroup': False, 'shape': 'roundedRect'}, {'id': 'dlopen', 'label': 'dlopen patch p1.so', 'labelStyle': '', 'padding': 15, 'cssStyles': [], 'cssCompiledStyles': [], 'cssClasses': 'default ', 'domId': 'flowchart-dlopen-1', 'look': 'classic', 'isGroup': False, 'shape': 'squareRect'}, {'id': 'dlsym', 'label': 'dlsym relevant parts', 'labelStyle': '', 'padding': 15, 'cssStyles': [], 'cssCompiledStyles': [], 'cssClasses': 'default ', 'domId': 'flowchart-dlsym-2', 'look': 'classic', 'isGroup': False, 'shape': 'roundedRect'}, {'id': 'supported', 'label': 'Atomically live-patch', 'labelStyle': '', 'padding': 15, 'cssStyles': [], 'cssCompiledStyles': [], 'cssClasses': 'default ', 'domId': 'flowchart-supported-3', 'look': 'classic', 'isGroup': False, 'shape': 'roundedRect'}, {'id': 'nosupport', 'label': 'Lock required live-patch', 'labelStyle': '', 'padding': 15, 'cssStyles': [], 'cssCompiledStyles': [], 'cssClasses': 'default ', 'domId': 'flowchart-nosupport-4', 'look': 'classic', 'isGroup': False, 'shape': 'roundedRect'}], 'edges': [{'id': 'L_registry_dlopen_0', 'isUserDefinedId': False, 'start': 'registry', 'end': 'dlopen', 'type': 'arrow_point', 'label': 'Available Patches', 'labelpos': 'c', 'thickness': 'normal', 'minlen': 1, 'classes': 'edge-thickness-normal edge-pattern-solid flowchart-link', 'arrowTypeStart': 'none', 'arrowTypeEnd': 'arrow_point', 'arrowheadStyle': 'fill: #333', 'cssCompiledStyles': [], 'labelStyle': [], 'style': [], 'pattern': 'normal', 'look': 'classic', 'curve': 'basis'}, {'id': 'L_dlopen_dlsym_0', 'isUserDefinedId': False, 'start': 'dlopen', 'end': 'dlsym', 'type': 'arrow_point', 'label': 'filter symbols', 'labelpos': 'c', 'thickness': 'normal', 'minlen': 1, 'classes': 'edge-thickness-normal edge-pattern-solid flowchart-link', 'arrowTypeStart': 'none', 'arrowTypeEnd': 'arrow_point', 'arrowheadStyle': 'fill: #333', 'cssCompiledStyles': [], 'labelStyle': [], 'style': [], 'pattern': 'normal', 'look': 'classic', 'curve': 'basis'}, {'id': 'L_dlsym_supported_0', 'isUserDefinedId': False, 'start': 'dlsym', 'end': 'supported', 'type': 'arrow_point', 'label': 'Compiler w/ live patch support', 'labelpos': 'c', 'thickness': 'normal', 'minlen': 1, 'classes': 'edge-thickness-normal edge-pattern-solid flowchart-link', 'arrowTypeStart': 'none', 'arrowTypeEnd': 'arrow_point', 'arrowheadStyle': 'fill: #333', 'cssCompiledStyles': [], 'labelStyle': [], 'style': [], 'pattern': 'normal', 'look': 'classic', 'curve': 'basis'}, {'id': 'L_dlsym_nosupport_0', 'isUserDefinedId': False, 'start': 'dlsym', 'end': 'nosupport', 'type': 'arrow_point', 'label': 'W/out live patch support', 'labelpos': 'c', 'thickness': 'normal', 'minlen': 1, 'classes': 'edge-thickness-normal edge-pattern-solid flowchart-link', 'arrowTypeStart': 'none', 'arrowTypeEnd': 'arrow_point', 'arrowheadStyle': 'fill: #333', 'cssCompiledStyles': [], 'labelStyle': [], 'style': [], 'pattern': 'normal', 'look': 'classic', 'curve': 'basis'}]}
    """

draw_graph(netx)
