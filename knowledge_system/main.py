import json
import os
import sys
from typing import Dict, Any

# NLP imports
from .nlp.main import SemanticEngine

# Director imports
from .director.graph_analyzer import GraphAnalyzer
from .director.importance_engine import ImportanceEngine
from .director.visual_mapper import RelationshipEngine, VisualMapper
from .director.animation_selector import CameraPlanner
from .director.composition_engine import CompositionEngine
from .director.motion_grammar import MotionGrammarEngine
from .director.transition_engine import TransitionEngine
from .director.visualization_schema import (
    VisualizationPlan, ScenePlan, VisualObject, VisualRelationship,
    CameraInstruction, MotionLanguage
)

# Adapter imports
from .adapter.remotion_adapter import RemotionAdapter

class KnowledgeSystemPipeline:
    def __init__(self):
        self.nlp_engine = SemanticEngine()
        self.graph_analyzer = GraphAnalyzer()
        self.importance_engine = ImportanceEngine()
        self.rel_engine = RelationshipEngine()
        self.visual_mapper = VisualMapper()
        self.camera_planner = CameraPlanner()
        self.composition_engine = CompositionEngine()
        self.motion_grammar = MotionGrammarEngine()
        self.transition_engine = TransitionEngine()
        self.adapter = RemotionAdapter()

    def run(self, text: str) -> Dict[str, Any]:
        print("🧠 STEP 1: Semantic NLP Extraction...")
        nlp_result = self.nlp_engine.process(text)

        # 1. Director Planning
        print("🎬 STEP 2: Cinematic Planning (Director Brain)...")
        graph_data = nlp_result['graph']
        global_analysis = self.graph_analyzer.analyze(graph_data)

        scenes = []
        scene_list = nlp_result['scenes']

        for i, scene in enumerate(scene_list):
            scene_id = scene["scene_id"]
            scene_type = scene["scene_type"]
            tone = scene["emotional_tone"]

            # Local node analysis
            scene_nodes = [n for n in graph_data["nodes"] if n.get("scene_id") == scene_id]
            comp = self.composition_engine.plan_composition(scene_nodes, global_analysis["main_structure"]["hero_node"])
            local_hero = comp.hero_object

            visual_objects = []
            for node in scene_nodes:
                is_hero = (node["id"] == local_hero)
                centrality = global_analysis["centrality"].get(node["id"], 0)
                v_weight = self.importance_engine.calculate_weight(node, centrality)

                # Robustly handle null emotion
                node_emotion = node.get("emotion") or "calm"

                v_mapping = self.visual_mapper.map_entity(node["type"], node_emotion)
                layout = self.composition_engine.get_layout(node, is_hero)
                grammar = self.motion_grammar.select_grammar(scene_type, node_emotion, node["label"])

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
                    pulse=node_emotion == "intense",
                    importance=node.get("importance", 1.0),
                    visual_weight=v_weight,
                    emotion=node_emotion,
                    motion_grammar=grammar
                ))

            # Relationship Mapping
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

            # Transition Planning
            next_scene = scene_list[i+1] if i+1 < len(scene_list) else None
            transition = self.transition_engine.plan_transition(scene, next_scene)

            # Camera Planning
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

        plan = VisualizationPlan(
            project_id="knowledge_system_unified",
            scenes=scenes,
            global_theme=global_analysis["main_structure"]["theme"]
        )

        # 2. Remotion Manifest Adaptation
        print("🚀 STEP 3: Remotion Manifest Adaptation...")
        final_manifest = self.adapter.adapt(plan.dict())

        return {
            "nlp": nlp_result,
            "plan": plan.dict(),
            "manifest": final_manifest
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m knowledge_system.main \"Your script here\"")
        return

    text = sys.argv[1]
    pipeline = KnowledgeSystemPipeline()
    results = pipeline.run(text)

    # Save artifacts for verification
    output_dir = "knowledge_system/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(f"{output_dir}/semantic_model.json", "w", encoding="utf-8") as f:
        json.dump(results["nlp"]["scenes"], f, indent=2, ensure_ascii=False)
    with open(f"{output_dir}/knowledge_graph.json", "w", encoding="utf-8") as f:
        json.dump(results["nlp"]["graph"], f, indent=2, ensure_ascii=False)
    with open(f"{output_dir}/visualization_plan.json", "w", encoding="utf-8") as f:
        json.dump(results["plan"], f, indent=2, ensure_ascii=False)
    with open(f"{output_dir}/remotion_render_crve.json", "w", encoding="utf-8") as f:
        json.dump(results["manifest"], f, indent=2, ensure_ascii=False)

    print(f"\n✅ Pipeline complete. Artifacts saved to {output_dir}/")

if __name__ == "__main__":
    main()
