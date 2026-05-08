import os
import json
import requests
import cv2
import imagehash
from PIL import Image
import torch
from transformers import (
    BlipProcessor,
    BlipForConditionalGeneration,
    CLIPProcessor,
    CLIPModel
)
import numpy as np
import time
import gc

# =========================================================
# API Keys from Environment Variables
# =========================================================

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

# =========================================================
# Device Configuration
# =========================================================

device = "cuda" if torch.cuda.is_available() else "cpu"

# =========================================================
# Constants
# =========================================================

TEMPLATE_PATH = "master_template.json"
MANIFEST_PATH = "manifest.json"

CONTENT_DIR = "content"
VIDEO_DIR = os.path.join(CONTENT_DIR, "videos")
FRAME_DIR = os.path.join(CONTENT_DIR, "frames")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(FRAME_DIR, exist_ok=True)


# =========================================================
# Validation
# =========================================================

def validate_frame(
    frame_path,
    keywords,
    must_have,
    exclude,
    threshold=0.25
):
    """
    Performs sequential BLIP and CLIP validation to save RAM.
    """

    image = Image.open(frame_path).convert("RGB")

    # -----------------------------------------------------
    # STAGE 1: BLIP (Captioning & Exclusion)
    # -----------------------------------------------------

    print(f"Loading BLIP on {device}...")

    blip_processor = BlipProcessor.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )

    blip_model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    ).to(device)

    inputs = blip_processor(
        image,
        return_tensors="pt"
    ).to(device)

    out = blip_model.generate(**inputs)

    caption = blip_processor.decode(
        out[0],
        skip_special_tokens=True
    )

    print(f"BLIP Caption: {caption}")

    # Cleanup BLIP immediately
    del blip_model
    del blip_processor

    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # -----------------------------------------------------
    # Check exclude keywords in caption
    # -----------------------------------------------------

    for word in exclude:
        if word.lower() in caption.lower():
            print(
                f"Validation failed: Excluded word '{word}' found in caption."
            )
            return False, 0

    # -----------------------------------------------------
    # STAGE 2: CLIP (Similarity Scoring)
    # -----------------------------------------------------

    print(f"Loading CLIP on {device}...")

    clip_processor = CLIPProcessor.from_pretrained(
        "openai/clip-vit-base-patch32"
    )

    clip_model = CLIPModel.from_pretrained(
        "openai/clip-vit-base-patch32"
    ).to(device)

    # Combine keywords and must_have for target description
    target_texts = keywords + must_have

    inputs = clip_processor(
        text=target_texts,
        images=image,
        return_tensors="pt",
        padding=True
    ).to(device)

    image_features_out = clip_model.get_image_features(
        pixel_values=inputs["pixel_values"]
    )

    text_features_out = clip_model.get_text_features(
        input_ids=inputs["input_ids"]
    )

    # Ensure they are tensors
    image_features = (
        image_features_out.pooler_output
        if hasattr(image_features_out, "pooler_output")
        else image_features_out
    )

    text_features = (
        text_features_out.pooler_output
        if hasattr(text_features_out, "pooler_output")
        else text_features_out
    )

    # Normalize
    image_features = image_features / image_features.norm(
        p=2,
        dim=-1,
        keepdim=True
    )

    text_features = text_features / text_features.norm(
        p=2,
        dim=-1,
        keepdim=True
    )

    # Cosine similarity
    similarity = (image_features @ text_features.t()).squeeze(0)

    max_sim = torch.max(similarity).item()

    print(
        f"CLIP Max Similarity: {max_sim:.4f} "
        f"(Threshold: {threshold})"
    )

    # Cleanup CLIP
    del clip_model
    del clip_processor

    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return max_sim > threshold, max_sim


# =========================================================
# Hash Utilities
# =========================================================

def get_image_hash(image_path):
    return imagehash.phash(Image.open(image_path))


def is_duplicate(new_hash, existing_hashes, threshold=0.9):
    for h in existing_hashes:
        distance = new_hash - h
        similarity = 1 - (distance / 64.0)

        if similarity >= threshold:
            return True

    return False


# =========================================================
# File Utilities
# =========================================================

def load_template():
    with open(TEMPLATE_PATH, "r") as f:
        return json.load(f)


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r") as f:
            return json.load(f)

    return {}


def save_manifest(manifest):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


# =========================================================
# Search APIs
# =========================================================

def search_pexels(
    query,
    min_width=1920,
    min_height=1080
):
    if not PEXELS_API_KEY:
        return []

    url = (
        f"https://api.pexels.com/videos/search"
        f"?query={query}&per_page=5"
    )

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()

        candidates = []

        for video in data.get("videos", []):

            video_files = video.get("video_files", [])

            suitable_files = [
                f for f in video_files
                if (
                    f.get("width", 0) >= min_width
                    and f.get("height", 0) >= min_height
                )
            ]

            if suitable_files:
                best_file = suitable_files[0]

                candidates.append({
                    "url": best_file["link"],
                    "id": video["id"],
                    "source": "pexels"
                })

        return candidates

    except Exception as e:
        print(f"Pexels search error: {e}")
        return []


def search_pixabay(query):
    if not PIXABAY_API_KEY:
        return []

    url = (
        f"https://pixabay.com/api/videos/"
        f"?key={PIXABAY_API_KEY}&q={query}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        candidates = []

        for video in data.get("hits", []):

            video_types = video.get("videos", {})

            best_file = (
                video_types.get("large")
                or video_types.get("medium")
                or video_types.get("small")
            )

            if best_file and best_file.get("url"):
                candidates.append({
                    "url": best_file["url"],
                    "id": video["id"],
                    "source": "pixabay"
                })

        return candidates

    except Exception as e:
        print(f"Pixabay search error: {e}")
        return []


# =========================================================
# Video Utilities
# =========================================================

def download_video(url, dest_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

    except Exception as e:
        print(f"Download error: {e}")
        return False


def extract_middle_frame(video_path, frame_path):
    try:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return False

        total_frames = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        if total_frames <= 0:
            cap.release()
            return False

        middle_frame_idx = total_frames // 2

        cap.set(
            cv2.CAP_PROP_POS_FRAMES,
            middle_frame_idx
        )

        ret, frame = cap.read()

        if ret:
            cv2.imwrite(frame_path, frame)
            cap.release()
            return True

        cap.release()
        return False

    except Exception as e:
        print(f"Frame extraction error: {e}")
        return False


# =========================================================
# Scene Processing
# =========================================================

def process_scene(scene, existing_hashes):

    scene_id = scene.get("scene_id")

    config = scene.get("scout_config", {})

    primary_keywords = config.get(
        "primary_keywords",
        []
    )

    fallback_keywords = config.get(
        "fallback_broll",
        []
    )

    min_res = config.get("min_resolution", "1080p")

    min_width, min_height = 1920, 1080

    if min_res == "720p":
        min_width, min_height = 1280, 720

    elif min_res == "4k":
        min_width, min_height = 3840, 2160

    search_queries = (
        primary_keywords + fallback_keywords
    )

    for query in search_queries:

        is_fallback = query in fallback_keywords

        print(
            f"Searching for '{query}' "
            f"(Fallback: {is_fallback})..."
        )

        candidates = (
            search_pexels(
                query,
                min_width,
                min_height
            )
            + search_pixabay(query)
        )

        for i, candidate in enumerate(candidates):

            video_path = os.path.join(
                VIDEO_DIR,
                f"{scene_id}_temp_{i}.mp4"
            )

            if download_video(
                candidate["url"],
                video_path
            ):

                frame_path = os.path.join(
                    FRAME_DIR,
                    f"{scene_id}_temp_{i}.jpg"
                )

                if extract_middle_frame(
                    video_path,
                    frame_path
                ):

                    must_have = config.get(
                        "must_have",
                        []
                    )

                    exclude = config.get(
                        "exclude",
                        []
                    )

                    clip_threshold = config.get(
                        "clip_threshold",
                        0.25
                    )

                    is_valid, score = validate_frame(
                        frame_path,
                        [query],
                        must_have,
                        exclude,
                        threshold=clip_threshold
                    )

                    if is_valid:

                        new_hash = get_image_hash(
                            frame_path
                        )

                        if is_duplicate(
                            new_hash,
                            existing_hashes
                        ):

                            print(
                                f"Candidate {i} is a duplicate."
                            )

                        else:

                            os.rename(
                                video_path,
                                os.path.join(
                                    VIDEO_DIR,
                                    f"{scene_id}.mp4"
                                )
                            )

                            os.rename(
                                frame_path,
                                os.path.join(
                                    FRAME_DIR,
                                    f"{scene_id}.jpg"
                                )
                            )

                            return True

                if os.path.exists(video_path):
                    os.remove(video_path)

                if os.path.exists(frame_path):
                    os.remove(frame_path)

    return False


# =========================================================
# Main
# =========================================================

def main():

    template = load_template()

    manifest = load_manifest()

    existing_hashes = [
        get_image_hash(
            os.path.join(
                FRAME_DIR,
                f"{sid}.jpg"
            )
        )
        for sid, d in manifest.items()
        if (
            d.get("status") == "finished"
            and os.path.exists(
                os.path.join(
                    FRAME_DIR,
                    f"{sid}.jpg"
                )
            )
        )
    ]

    for scene in template.get("scenes", []):

        try:

            scene_id = scene.get("scene_id")

            if (
                not scene_id
                or manifest.get(scene_id, {}).get("status")
                == "finished"
            ):
                continue

            print(f"Processing scene {scene_id}...")

            if process_scene(
                scene,
                existing_hashes
            ):

                final_frame = os.path.join(
                    FRAME_DIR,
                    f"{scene_id}.jpg"
                )

                if os.path.exists(final_frame):

                    existing_hashes.append(
                        get_image_hash(final_frame)
                    )

                manifest[scene_id] = {
                    "status": "finished",
                    "timestamp": time.time(),
                    "video_path": (
                        f"content/videos/{scene_id}.mp4"
                    )
                }

                save_manifest(manifest)

        except Exception as e:
            print(
                f"Error processing scene "
                f"{scene.get('scene_id')}: {e}"
            )


# =========================================================
# Entry
# =========================================================

if __name__ == "__main__":
    main()
