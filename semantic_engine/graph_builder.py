import networkx as nx
from typing import Any
from .semantic_model import SemanticSceneModel

class GraphBuilder:
    def __init__(self):
        pass

    def build(self, model: SemanticSceneModel) -> nx.DiGraph:
        G = nx.DiGraph()

        # Add nodes for entities
        for entity in model.entities:
            G.add_node(entity.id, label=entity.label, type=entity.type, importance=entity.importance)

        # Add nodes for actions (if they have subject/object relations)
        # Or just link entities via relationships derived from actions
        for relation in model.relations:
            G.add_edge(relation.source_id, relation.target_id, relationship=relation.relationship, importance=relation.importance)

        # Add metadata nodes (scene type, tone) as graph attributes or special nodes
        G.graph['scene_type'] = model.scene_type
        G.graph['emotional_tone'] = model.emotional_tone

        return G

    def to_json(self, G: nx.DiGraph) -> dict:
        return nx.node_link_data(G)
