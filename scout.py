
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
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Hardcoded API Keys for ease of use in Colab
PEXELS_API_KEY = '2DSzg1JdB7OB3DBf1eEPpyjRkAKWqDGzrOLhTTQBHTN1N1nplYD5srZ3'
PIXABAY_API_KEY = '55426706-88c01ac01bdf3ded9bde88edc'

# Device Configuration
device = "cuda" if torch.cuda.is_available() else "cpu"

# Global Models to avoid repeated reloading
print(f"Loading Global AI Models on {device}...")

BLIP_PROCESSOR = BlipProcessor.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

BLIP_MODEL = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
).to(device)

CLIP_PROCESSOR = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32"
)

CLIP_MODEL = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32"
).to(device)

# Constants
TEMPLATE_PATH = 'master_template.json'
MANIFEST_PATH = 'manifest.json'

CONTENT_DIR = 'content'
VIDEO_DIR = os.path.join(CONTENT_DIR, 'videos')
FRAME_DIR = os.path.join(CONTENT_DIR, 'frames')
THUMB_DIR = os.path.join(CONTENT_DIR, 'thumbs')

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(FRAME_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)


def get_image_hash(image_path):
    return imagehash.phash(Image.open(image_path))


def is_duplicate(new_hash, existing_hashes, threshold=0.9):
    for h in existing_hashes:
        distance = new_hash - h
        similarity = 1 - (distance / 64.0)

        if similarity >= threshold:
            return True

    return False


def load_template():
    with open(TEMPLATE_PATH, 'r') as f:
        return json.load(f)


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)

    return {}


def save_manifest(manifest):
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)


def search_pexels(query, min_width=1920, min_height=1080):
    if not PEXELS_API_KEY:
        return []

    url = (
        f"https://api.pexels.com/videos/search?"
        f"query={query}&per_page=5"
    )

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        candidates = []

        for video in data.get('videos', []):
            video_files = video.get('video_files', [])

            suitable_files = [
                f for f in video_files
                if f.get('width', 0) >= min_width
                and f.get('height', 0) >= min_height
            ]

            if suitable_files:
                best_file = suitable_files[0]

                candidates.append({
                    'url': best_file['link'],
                    'thumb_url': video['image'],
                    'id': f"pexels_{video['id']}",
                    'source': 'pexels'
                })

        return candidates

    except Exception as e:
        print(f"Pexels search error: {e}")
        return []


def search_pixabay(query):
    if not PIXABAY_API_KEY:
        return []

    url = (
        f"https://pixabay.com/api/videos/?"
        f"key={PIXABAY_API_KEY}&q={query}"
    )

    try:
        response = requests.get(url, timeout=30)

        response.raise_for_status()

        data = response.json()

        candidates = []

        for video in data.get('hits', []):
            video_types = video.get('videos', {})

            best_file = (
                video_types.get('large')
                or video_types.get('medium')
                or video_types.get('small')
            )

            if best_file and best_file.get('url'):
                thumb_url = (
                    f"https://i.vimeocdn.com/video/"
                    f"{video['picture_id']}_640x360.jpg"
                )

                candidates.append({
                    'url': best_file['url'],
                    'thumb_url': thumb_url,
                    'id': f"pixabay_{video['id']}",
                    'source': 'pixabay'
                })

        return candidates

    except Exception as e:
        print(f"Pixabay search error: {e}")
        return []


def download_resource(url, dest_path):
    try:
        response = requests.get(
            url,
            stream=True,
            timeout=60
        )

        response.raise_for_status()

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

    except Exception as e:
        print(f"Download error: {e}")
        return False


def extract_frames(video_path, frame_paths):
    """
    Extracts multiple frames for temporal validation.
    """

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

        # Sample 25%, 50%, 75%
        indices = [
            total_frames // 4,
            total_frames // 2,
            (3 * total_frames) // 4
        ]

        results = []

        for i, idx in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)

            ret, frame = cap.read()

            if ret:
                if frame_paths[i] != "_":
                    cv2.imwrite(frame_paths[i], frame)

                results.append(True)

            else:
                results.append(False)

        cap.release()

        return all(results)

    except Exception as e:
        print(f"Frame extraction error: {e}")
        return False


def batch_semantic_filter(
    candidates,
    keywords,
    must_have,
    exclude,
    threshold=0.28
):
    """
    Batch processes thumbnails to find the best candidate.
    """

    if not candidates:
        return None

    # Load images for batch processing
    imgs = []
    active_candidates = []

    for c in candidates:
        if os.path.exists(c['thumb_path']):
            imgs.append(
                Image.open(c['thumb_path']).convert("RGB")
            )

            active_candidates.append(c)

    if not imgs:
        return None

    # -----------------------------
    # STAGE 1: Batch BLIP
    # -----------------------------
    inputs = BLIP_PROCESSOR(
        imgs,
        return_tensors="pt",
        padding=True
    ).to(device)

    with torch.no_grad():
        out = BLIP_MODEL.generate(
            **inputs,
            max_new_tokens=30
        )

    captions = BLIP_PROCESSOR.batch_decode(
        out,
        skip_special_tokens=True
    )

    remaining_imgs = []
    remaining_candidates = []

    for i, caption in enumerate(captions):
        is_excluded = any(
            word.lower() in caption.lower()
            for word in exclude
        )

        if not is_excluded:
            remaining_imgs.append(imgs[i])
            remaining_candidates.append(
                active_candidates[i]
            )

            active_candidates[i]['caption'] = caption

        else:
            print(
                f"Excluding "
                f"{active_candidates[i]['id']}: "
                f"{caption}"
            )

    if not remaining_imgs:
        return None

    # -----------------------------
    # STAGE 2: Batch CLIP
    # -----------------------------
    target_texts = keywords + must_have

    inputs = CLIP_PROCESSOR(
        text=target_texts,
        images=remaining_imgs,
        return_tensors="pt",
        padding=True
    ).to(device)

    with torch.no_grad():
        image_features = CLIP_MODEL.get_image_features(
            pixel_values=inputs['pixel_values']
        )

        text_features = CLIP_MODEL.get_text_features(
            input_ids=inputs['input_ids']
        )

    # Normalize and score
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

    # Cosine similarity matrix
    similarity = (
        image_features @ text_features.t()
    )

    max_sims, _ = torch.max(similarity, dim=1)

    for i, sim in enumerate(max_sims):
        remaining_candidates[i]['clip_score'] = sim.item()

    worthy = [
        c for c in remaining_candidates
        if c['clip_score'] >= threshold
    ]

    worthy.sort(
        key=lambda x: x['clip_score'],
        reverse=True
    )

    return worthy[0] if worthy else None


def temporal_validate(
    video_path,
    scene_id,
    keywords,
    threshold=0.28
):
    """
    Sample multiple frames and average CLIP score.
    """

    temp_frames = [
        os.path.join(
            FRAME_DIR,
            f"{scene_id}_val_{i}.jpg"
        )
        for i in range(3)
    ]

    if not extract_frames(video_path, temp_frames):
        return False, 0

    imgs = [
        Image.open(f).convert("RGB")
        for f in temp_frames
    ]

    inputs = CLIP_PROCESSOR(
        text=keywords,
        images=imgs,
        return_tensors="pt",
        padding=True
    ).to(device)

    with torch.no_grad():
        img_feats = CLIP_MODEL.get_image_features(
            pixel_values=inputs['pixel_values']
        )

        txt_feats = CLIP_MODEL.get_text_features(
            input_ids=inputs['input_ids']
        )

    img_feats = img_feats / img_feats.norm(
        p=2,
        dim=-1,
        keepdim=True
    )

    txt_feats = txt_feats / txt_feats.norm(
        p=2,
        dim=-1,
        keepdim=True
    )

    avg_sim = (
        img_feats @ txt_feats.t()
    ).mean().item()

    for f in temp_frames:
        os.remove(f)

    return avg_sim >= threshold, avg_sim


def process_scene(scene, existing_hashes):
    scene_id = scene.get('scene_id')

    config = scene.get('scout_config', {})

    primary_keywords = config.get(
        'primary_keywords',
        []
    )

    fallback_keywords = config.get(
        'fallback_broll',
        []
    )

    min_res = config.get(
        'min_resolution',
        '1080p'
    )

    clip_threshold = config.get(
        'clip_threshold',
        0.28
    )

    min_width, min_height = 1920, 1080

    if min_res == '720p':
        min_width, min_height = 1280, 720

    elif min_res == '4k':
        min_width, min_height = 3840, 2160

    search_queries = [
        primary_keywords,
        fallback_keywords
    ]

    for queries in search_queries:
        if not queries:
            continue

        print(f"Parallel Search for {queries}...")

        all_candidates = []

        with ThreadPoolExecutor(
            max_workers=min(8, len(queries) * 2)
        ) as executor:

            p_results = list(
                executor.map(
                    lambda q: search_pexels(
                        q,
                        min_width,
                        min_height
                    ),
                    queries
                )
            )

            b_results = list(
                executor.map(
                    search_pixabay,
                    queries
                )
            )

            for res in p_results + b_results:
                all_candidates.extend(res)

        if not all_candidates:
            continue

        # De-duplicate
        unique_candidates = list({
            c['id']: c
            for c in all_candidates
        }.values())

        print(
            f"Validating "
            f"{len(unique_candidates)} thumbnails..."
        )

        processed_candidates = []

        for i, c in enumerate(
            tqdm(unique_candidates, desc="Thumbs")
        ):
            thumb_path = os.path.join(
                THUMB_DIR,
                f"{scene_id}_t_{i}.jpg"
            )

            if download_resource(
                c['thumb_url'],
                thumb_path
            ):
                c['thumb_path'] = thumb_path
                processed_candidates.append(c)

        # -----------------------------
        # Batch semantic validation
        # -----------------------------
        winner = batch_semantic_filter(
            processed_candidates,
            queries,
            config.get('must_have', []),
            config.get('exclude', []),
            threshold=clip_threshold
        )

        if winner:
            print(
                f"Semantic match found "
                f"({winner['id']}). "
                f"Downloading full video..."
            )

            final_video = os.path.join(
                VIDEO_DIR,
                f"{scene_id}.mp4"
            )

            if download_resource(
                winner['url'],
                final_video
            ):
                # Temporal Validation
                valid, avg_sim = temporal_validate(
                    final_video,
                    scene_id,
                    queries,
                    threshold=clip_threshold
                )

                if valid:
                    # Perceptual Deduplication
                    extract_frames(
                        final_video,
                        [
                            os.path.join(
                                FRAME_DIR,
                                f"{scene_id}.jpg"
                            ),
                            "_",
                            "_"
                        ]
                    )

                    win_hash = get_image_hash(
                        os.path.join(
                            FRAME_DIR,
                            f"{scene_id}.jpg"
                        )
                    )

                    if is_duplicate(
                        win_hash,
                        existing_hashes
                    ):
                        print(
                            "Duplicate detected. "
                            "Skipping."
                        )

                        os.remove(final_video)

                    else:
                        print(
                            f"Selected: "
                            f"{winner['id']} "
                            f"(Avg Sim: {avg_sim:.4f})"
                        )

                        # Cleanup thumbs
                        for c in processed_candidates:
                            os.remove(c['thumb_path'])

                        return True

                else:
                    print(
                        f"Temporal validation failed "
                        f"({avg_sim:.4f})."
                    )

                    os.remove(final_video)

        # Cleanup thumbs if no winner
        for c in processed_candidates:
            os.remove(c['thumb_path'])

    return False


def main():
    template = load_template()

    manifest = load_manifest()

    existing_hashes = []

    for sid, d in manifest.items():
        if d.get('status') == 'completed':
            fp = os.path.join(
                FRAME_DIR,
                f"{sid}.jpg"
            )

            if os.path.exists(fp):
                existing_hashes.append(
                    get_image_hash(fp)
                )

    for scene in template.get('scenes', []):
        try:
            sid = scene.get('scene_id')

            if (
                not sid
                or manifest.get(sid, {}).get('status')
                == 'completed'
            ):
                continue

            print(f"\n--- Scene: {sid} ---")

            if process_scene(scene, existing_hashes):
                final_frame = os.path.join(
                    FRAME_DIR,
                    f"{sid}.jpg"
                )

                if os.path.exists(final_frame):
                    existing_hashes.append(
                        get_image_hash(final_frame)
                    )

                manifest[sid] = {
                    'status': 'completed',
                    'timestamp': time.time(),
                    'video_path': (
                        f"content/videos/{sid}.mp4"
                    )
                }

                save_manifest(manifest)

                print(f"SUCCESS: {sid}")

            else:
                print(f"FAILED: {sid}")

        except Exception as e:
            print(
                f"Error in "
                f"{scene.get('scene_id')}: {e}"
            )


if __name__ == "__main__":
    main()
