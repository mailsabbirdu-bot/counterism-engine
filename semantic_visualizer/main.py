import json
import os
from typing import Dict, Any, List, Optional

from semantic_visualizer.schemas.visualization_schema import (
    VisualizationPlan, ScenePlan, VisualObject, VisualRelationship, MotionLanguage,
    CameraInstruction, Composition, TransitionPlan, GeometryPath
)
from semantic_visualizer.core.graph_analyzer import GraphAnalyzer
from semantic_visualizer.core.importance_engine import ImportanceEngine, EmotionEngine
from semantic_visualizer.core.visual_mapper import RelationshipEngine, VisualMapper
from semantic_visualizer.core.animation_selector import AnimationSelector, CameraPlanner
from semantic_visualizer.core.composition_engine import CompositionEngine
from semantic_visualizer.core.motion_grammar import MotionGrammarEngine
from semantic_visualizer.core.transition_engine import TransitionEngine

class SemanticVisualizer:
    def __init__(self):
        self.graph_analyzer = GraphAnalyzer()
        self.importance_engine = ImportanceEngine()
        self.emotion_engine = EmotionEngine()
        self.rel_engine = RelationshipEngine()
        self.visual_mapper = VisualMapper()
        self.anim_selector = AnimationSelector()
        self.camera_planner = CameraPlanner()
        self.composition_engine = CompositionEngine()
        self.motion_grammar = MotionGrammarEngine()
        self.transition_engine = TransitionEngine()

    def process(self, semantic_model_path: str, knowledge_graph_path: str) -> VisualizationPlan:
        with open(semantic_model_path, 'r') as f:
            semantic_data = json.load(f)
        with open(knowledge_graph_path, 'r') as f:
            graph_data = json.load(f)

        # Global Analysis
        global_analysis = self.graph_analyzer.analyze(graph_data)

        scenes = []

        # Handle both dictionary {"scenes": [...]} and raw list [...] formats
        scene_list = semantic_data["scenes"] if isinstance(semantic_data, dict) and "scenes" in semantic_data else semantic_data

        # Process each scene
        for i, scene in enumerate(scene_list):
            scene_id = scene["scene_id"]
            scene_type = scene["scene_type"]
            tone = scene["emotional_tone"]

            # Local node analysis for this scene
            scene_nodes = [n for n in graph_data["nodes"] if n.get("scene_id") == scene_id]

            # 1. Composition Planning
            comp = self.composition_engine.plan_composition(scene_nodes, global_analysis["main_structure"]["hero_node"])
            local_hero = comp.hero_object

            visual_objects = []
            for node in scene_nodes:
                is_hero = (node["id"] == local_hero)
                centrality = global_analysis["centrality"].get(node["id"], 0)
                v_weight = self.importance_engine.calculate_weight(node, centrality)
                v_mapping = self.visual_mapper.map_entity(node["type"], node.get("emotion", "calm"))
                layout = self.composition_engine.get_layout(node, is_hero)
                grammar = self.motion_grammar.select_grammar(scene_type, node.get("emotion", "calm"), node["label"])

                visual_objects.append(VisualObject(
                    id=node["id"],
                    label=node["label"],
                    type=v_mapping["type"],
                    style=v_mapping["style"],
                    x=layout["x"],
                    y=layout["y"],
                    depth=layout["depth"],
                    layer=layout["layer"],
                    visual_priority=layout["visual_priority"],
                    scale=node.get("scale", 1.0),
                    pulse=node.get("emotion") == "intense",
                    importance=node.get("importance", 1.0),
                    visual_weight=v_weight,
                    emotion=node.get("emotion", "calm"),
                    motion_grammar=grammar
                ))

            # 2. Relationship Mapping
            edges_key = "links" if "links" in graph_data else "edges"
            scene_edges = [e for e in graph_data[edges_key] if e.get("scene_id") == scene_id]
            visual_rels = []
            for edge in scene_edges:
                rel_mapping = self.rel_engine.map_relation(edge["relationship"])
                visual_rels.append(VisualRelationship(
                    source_id=edge["source"],
                    target_id=edge["target"],
                    type=rel_mapping["type"],
                    renderer=rel_mapping["renderer"],
                    path=rel_mapping["path"],
                    speed=rel_mapping["speed"],
                    strength=edge.get("strength", 1.0)
                ))

            # 3. Transition Planning
            next_scene = scene_list[i+1] if i+1 < len(scene_list) else None
            transition = self.transition_engine.plan_transition(scene, next_scene)

            # 4. Camera Planning
            cam_data = self.camera_planner.plan(scene_type, local_hero)
            if tone == "intense":
                cam_data["movement"] = "descend"

            theme = f"{tone} {scene_type}" if tone != "intense" else "hidden danger"

            scenes.append(ScenePlan(
                scene_id=scene_id,
                duration=300,
                theme=theme,
                composition=comp,
                visual_objects=visual_objects,
                relationships=visual_rels,
                transition=transition,
                camera=CameraInstruction(**cam_data)
            ))

        return VisualizationPlan(
            project_id="megacity_documentary_directorial",
            scenes=scenes,
            global_theme=global_analysis["main_structure"]["theme"]
        )

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="semantic_visualizer/input/semantic_model.json")
    parser.add_argument("--graph", default="semantic_visualizer/input/knowledge_graph.json")
    parser.add_argument("--output", default="semantic_visualizer/output/visualization_plan.json")
    args = parser.parse_args()

    visualizer = SemanticVisualizer()
    plan = visualizer.process(args.model, args.graph)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(plan.dict(), f, indent=2, ensure_ascii=False)

    print(f"✅ Advanced Directorial Visualization plan generated: {args.output}")

if __name__ == "__main__":
    main()
