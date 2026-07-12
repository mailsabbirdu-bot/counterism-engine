import networkx as nx
from typing import Any, List
from .semantic_model import SemanticSceneModel

class GraphBuilder:
    def __init__(self):
        pass

    def build(self, model: SemanticSceneModel) -> nx.DiGraph:
        G = nx.DiGraph()
        # Add nodes for entities
        for entity in model.entities:
            G.add_node(entity.id, label=entity.label, type=entity.type, importance=entity.importance)
        # Add edges for relations
        for relation in model.relations:
            G.add_edge(relation.source_id, relation.target_id, relationship=relation.relationship, importance=relation.importance)
        G.graph['scene_type'] = model.scene_type
        G.graph['emotional_tone'] = model.emotional_tone
        return G

    def build_multi(self, models: List[SemanticSceneModel]) -> nx.DiGraph:
        G = nx.DiGraph()
        # Create a unified graph from multiple scenes
        # For simplicity, we use the first scene's classifier for global state
        if models:
            G.graph['scene_type'] = models[0].scene_type
            G.graph['emotional_tone'] = models[0].emotional_tone

        for model in models:
            for entity in model.entities:
                # Deduplicate nodes by label in multi-scene graph
                node_id = entity.label
                if not G.has_node(node_id):
                    G.add_node(node_id,
                               label=entity.label,
                               type=entity.type,
                               importance=entity.importance,
                               emotion=entity.emotion,
                               scale=entity.scale,
                               scene_id=model.scene_id)
                else:
                    # Update importance if higher
                    G.nodes[node_id]['importance'] = max(G.nodes[node_id]['importance'], entity.importance)

            for relation in model.relations:
                # Map entity IDs back to labels for unified graph
                def get_label(eid):
                    for e in model.entities:
                        if e.id == eid: return e.label
                    return eid

                src = get_label(relation.source_id)
                tgt = get_label(relation.target_id)
                if src and tgt:
                    G.add_edge(src, tgt, relationship=relation.relationship, scene_id=model.scene_id)
        return G

    def to_json(self, G: nx.DiGraph) -> dict:
        data = nx.node_link_data(G)
        # Flatten attributes for easier use in Remotion
        for node in data['nodes']:
            # Ensure type exists
            if 'type' not in node:
                node['type'] = 'concept'
            # Add visual weight calculation
            importance = node.get('importance', 1.0)
            scale = node.get('scale', 1.0)
            node['visual_weight'] = importance * scale

        return data
