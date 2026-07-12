from typing import Optional, List, Dict, Any
from ..schemas.visualization_schema import TransitionPlan

class TransitionEngine:
    def __init__(self):
        pass

    def plan_transition(self, current_scene: Dict[str, Any], next_scene: Optional[Dict[str, Any]]) -> Optional[TransitionPlan]:
        if not next_scene:
            return None

        cur_type = current_scene.get("scene_type")
        next_type = next_scene.get("scene_type")

        # Logic: If transitioning from Intro (Location) to Growth (Details)
        if cur_type == "introduction" and next_type == "growth":
            return TransitionPlan(
                type="zoom_into_city",
                from_node="ঢাকা", # Needs better discovery logic
                to_node="কংক্রিট",
                meaning="city_growth"
            )

        if next_scene.get("emotional_tone") == "intense":
            return TransitionPlan(
                type="layer_shift",
                from_node=current_scene.get("scene_id"),
                to_node="subsurface",
                meaning="revealing_hidden"
            )

        return TransitionPlan(
            type="dissolve_to_detail",
            from_node=current_scene.get("scene_id"),
            to_node=next_scene.get("scene_id"),
            meaning="context_shift"
        )
