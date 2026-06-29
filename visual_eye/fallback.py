from .schema import SceneAnalysis

def get_empty_analysis() -> SceneAnalysis:
    return SceneAnalysis(
        status="fallback",
        scene_type="unknown",
        objects=[],
        safe_text_regions=[]
    )
