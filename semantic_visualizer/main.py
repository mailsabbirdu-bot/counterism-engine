import json
import os
from typing import Dict, Any, List

from semantic_visualizer.schemas.visualization_schema import (
    VisualizationPlan, ScenePlan, VisualObject, VisualRelationship, Animation, CameraInstruction
)
from semantic_visualizer.core.graph_analyzer import GraphAnalyzer
from semantic_visualizer.core.importance_engine import ImportanceEngine, EmotionEngine
from semantic_visualizer.core.visual_mapper import RelationshipEngine, VisualMapper
from semantic_visualizer.core.animation_selector import AnimationSelector, CameraPlanner

class SemanticVisualizer:
    def __init__(self):
        self.graph_analyzer = GraphAnalyzer()
        self.importance_engine = ImportanceEngine()
        self.emotion_engine = EmotionEngine()
        self.rel_engine = RelationshipEngine()
        self.visual_mapper = VisualMapper()
        self.anim_selector = AnimationSelector()
        self.camera_planner = CameraPlanner()

    def process(self, semantic_model_path: str, knowledge_graph_path: str) -> VisualizationPlan:
        with open(semantic_model_path, 'r') as f:
            semantic_data = json.load(f)
        with open(knowledge_graph_path, 'r') as f:
            graph_data = json.load(f)

        # Global Analysis
        global_analysis = self.graph_analyzer.analyze(graph_data)

        scenes = []
        previous_tone = "calm"

        # Process each scene
        # Handle both dictionary {"scenes": [...]} and raw list [...] formats
        scene_list = semantic_data["scenes"] if isinstance(semantic_data, dict) and "scenes" in semantic_data else semantic_data

        for scene in scene_list:
            scene_id = scene["scene_id"]
            scene_type = scene["scene_type"]
            tone = scene["emotional_tone"]

            # Local node analysis for this scene
            scene_nodes = [n for n in graph_data["nodes"] if n.get("scene_id") == scene_id]

            # Determine Scene Theme and Hero
            scene_theme = f"{tone} {scene_type}"
            if tone == "intense":
                scene_theme = "hidden danger"

            local_hero = global_analysis["main_structure"]["hero_node"]
            if scene_nodes:
                # Find node in this scene with highest importance or centrality
                local_hero = max(scene_nodes, key=lambda x: x.get("importance", 1.0) + global_analysis["centrality"].get(x["id"], 0))["id"]

            visual_objects = []
            for node in scene_nodes:
                centrality = global_analysis["centrality"].get(node["id"], 0)
                v_weight = self.importance_engine.calculate_weight(node, centrality)
                v_mapping = self.visual_mapper.map_entity(node["type"], node.get("emotion", "calm"))

                visual_objects.append(VisualObject(
                    id=node["id"],
                    label=node["label"],
                    type=v_mapping["type"],
                    style=v_mapping["style"],
                    position="center" if node["id"] == local_hero else "top" if node.get("type") == "location" else "bottom",
                    scale=node.get("scale", 1.0),
                    pulse=node.get("emotion") == "intense",
                    importance=node.get("importance", 1.0),
                    visual_weight=v_weight,
                    emotion=node.get("emotion", "calm")
                ))

            # Filter edges for this scene
            edges_key = "links" if "links" in graph_data else "edges"
            scene_edges = [e for e in graph_data[edges_key] if e.get("scene_id") == scene_id]
            visual_rels = []
            for edge in scene_edges:
                rel_mapping = self.rel_engine.map_relation(edge["relationship"])
                visual_rels.append(VisualRelationship(
                    source_id=edge["source"],
                    target_id=edge["target"],
                    type=rel_mapping["type"],
                    visual=rel_mapping["visual"],
                    strength=edge.get("strength", 1.0)
                ))

            # Animations
            anims = []
            scene_anim = self.anim_selector.select(scene_type, tone)
            for obj in visual_objects:
                anims.append(Animation(
                    target_id=obj.id,
                    enter=scene_anim["enter"],
                    motion=scene_anim["motion"],
                    exit=scene_anim["exit"]
                ))

            # Camera
            cam = self.camera_planner.plan(scene_type, local_hero)

            scenes.append(ScenePlan(
                scene_id=scene_id,
                duration=300, # Default duration
                theme=scene_theme,
                visual_objects=visual_objects,
                relationships=visual_rels,
                animations=anims,
                camera=CameraInstruction(**cam)
            ))

            previous_tone = tone

        return VisualizationPlan(
            project_id="megacity_documentary",
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

    print(f"✅ Visualization plan generated: {args.output}")

if __name__ == "__main__":
    main()
