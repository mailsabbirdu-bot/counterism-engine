import networkx as nx
from typing import Dict, Any, List

class GraphAnalyzer:
    def __init__(self):
        pass

    def analyze(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        G = nx.node_link_graph(graph_data)

        # Handle empty graph
        if G.number_of_nodes() == 0:
            return {
                "main_structure": {
                    "theme": "empty",
                    "hero_node": None,
                    "support_nodes": [],
                    "layout_type": "force"
                },
                "centrality": {},
                "node_count": 0,
                "edge_count": 0
            }

        # Calculate centralities
        degree_cent = nx.degree_centrality(G)

        # Identify hero node (highest degree centrality)
        hero_node = max(degree_cent, key=degree_cent.get) if degree_cent else None

        # Identify themes based on types and emotional tones
        scene_type = graph_data.get('graph', {}).get('scene_type', 'trend')
        emotional_tone = graph_data.get('graph', {}).get('emotional_tone', 'calm')

        main_theme = f"{emotional_tone} {scene_type}"
        if emotional_tone == 'intense':
            main_theme = "hidden danger"

        important_nodes = sorted(degree_cent, key=degree_cent.get, reverse=True)[:3]

        # Determine semantic layout type
        layout_type = "force"
        if nx.is_tree(G):
            layout_type = "tree"
        elif any(type(n) == str and "time" in n.lower() for n in G.nodes):
            layout_type = "timeline"
        elif len(G.nodes) > 10:
            layout_type = "radial"

        return {
            "main_structure": {
                "theme": main_theme,
                "hero_node": hero_node,
                "support_nodes": [n for n in important_nodes if n != hero_node],
                "layout_type": layout_type
            },
            "centrality": degree_cent,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges)
        }
