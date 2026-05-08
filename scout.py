import os
import json
import requests
import cv2
import imagehash
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration, CLIPProcessor, CLIPModel
import numpy as np
import time

PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')

# Global AI Models
blip_processor = None
blip_model = None
clip_processor = None
clip_model = None
device = "cuda" if torch.cuda.is_available() else "cpu"

def init_ai_models():
    global blip_processor, blip_model, clip_processor, clip_model
    print(f"Initializing AI models on {device}...")
    blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)

def validate_frame(frame_path, keywords, must_have, exclude, threshold=0.25):
    if not blip_model or not clip_model:
        init_ai_models()
        
    image = Image.open(frame_path).convert("RGB")
    
    # BLIP Captioning
    inputs = blip_processor(image, return_tensors="pt").to(device)
    out = blip_model.generate(**inputs)
    caption = blip_processor.decode(out[0], skip_special_tokens=True)
    print(f"BLIP Caption: {caption}")
    
    # Check exclude keywords in caption
    for word in exclude:
        if word.lower() in caption.lower():
            print(f"Validation failed: Excluded word '{word}' found in caption.")
            return False, 0
            
    # CLIP Similarity
    # Combine keywords and must_have for target description
    target_texts = keywords + must_have
    inputs = clip_processor(text=target_texts, images=image, return_tensors="pt", padding=True).to(device)
    
    # Better approach for similarity:
    image_features_out = clip_model.get_image_features(pixel_values=inputs['pixel_values'])
    text_features_out = clip_model.get_text_features(input_ids=inputs['input_ids'])
    
    # Ensure they are tensors
    if hasattr(image_features_out, 'pooler_output'):
        image_features = image_features_out.pooler_output
    else:
        image_features = image_features_out
        
    if hasattr(text_features_out, 'pooler_output'):
        text_features = text_features_out.pooler_output
    else:
        text_features = text_features_out
    
    # Normalize
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
    
    # Cosine similarity
    similarity = (image_features @ text_features.t()).squeeze(0)
    max_sim = torch.max(similarity).item()
    print(f"CLIP Max Similarity: {max_sim:.4f} (Threshold: {threshold})")
    
    return max_sim > threshold, max_sim

def get_image_hash(image_path):
    return imagehash.phash(Image.open(image_path))

def is_duplicate(new_hash, existing_hashes, threshold=0.9):
    for h in existing_hashes:
        # imagehash distance is number of bits that differ. 
        # For 64-bit hash, 10% difference is 6.4 bits.
        # So > 90% match means distance < 6.4
        distance = new_hash - h
        similarity = 1 - (distance / 64.0)
        if similarity >= threshold:
            return True
    return False

# Constants
TEMPLATE_PATH = 'master_template.json'
MANIFEST_PATH = 'manifest.json'
CONTENT_DIR = 'content'
VIDEO_DIR = os.path.join(CONTENT_DIR, 'videos')
FRAME_DIR = os.path.join(CONTENT_DIR, 'frames')

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(FRAME_DIR, exist_ok=True)

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

def main():
    template = load_template()
    manifest = load_manifest()
    
    # Collect existing hashes for deduplication
    existing_hashes = []
    for sid, data in manifest.items():
        if data.get('status') == 'done':
            frame_path = os.path.join(FRAME_DIR, f"{sid}.jpg")
            if os.path.exists(frame_path):
                existing_hashes.append(get_image_hash(frame_path))

    scenes = template.get('scenes', [])
    
    for scene in scenes:
        scene_id = scene.get('scene_id')
        if not scene_id:
            continue
            
        if manifest.get(scene_id, {}).get('status') == 'done':
            print(f"Skipping scene {scene_id}, already marked as done.")
            continue
            
        print(f"Processing scene {scene_id}...")
        
        # Placeholder for scouting logic
        success = process_scene(scene, existing_hashes)
        
        if success:
            # Update existing hashes
            final_frame_path = os.path.join(FRAME_DIR, f"{scene_id}.jpg")
            if os.path.exists(final_frame_path):
                existing_hashes.append(get_image_hash(final_frame_path))
                
            manifest[scene_id] = {
                'status': 'done',
                'timestamp': time.time(),
                'video_path': f"content/videos/{scene_id}.mp4"
            }
            save_manifest(manifest)
            print(f"Scene {scene_id} completed.")
        else:
            print(f"Scene {scene_id} failed.")

def search_pexels(query, min_width=1920, min_height=1080):
    if not PEXELS_API_KEY:
        return []
    
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=5"
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        candidates = []
        for video in data.get('videos', []):
            # Find best file
            video_files = video.get('video_files', [])
            suitable_files = [f for f in video_files if f.get('width', 0) >= min_width and f.get('height', 0) >= min_height]
            
            if suitable_files:
                # Pick the one closest to target resolution or just the first suitable one
                best_file = suitable_files[0]
                candidates.append({
                    'url': best_file['link'],
                    'id': video['id'],
                    'source': 'pexels'
                })
        return candidates
    except Exception as e:
        print(f"Pexels search error: {e}")
        return []

def search_pixabay(query):
    if not PIXABAY_API_KEY:
        return []
    
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        candidates = []
        for video in data.get('hits', []):
            # Pixabay provides multiple sizes in 'videos' object
            video_types = video.get('videos', {})
            # Prefer large or medium
            best_file = video_types.get('large') or video_types.get('medium') or video_types.get('small')
            
            if best_file and best_file.get('url'):
                candidates.append({
                    'url': best_file['url'],
                    'id': video['id'],
                    'source': 'pixabay'
                })
        return candidates
    except Exception as e:
        print(f"Pixabay search error: {e}")
        return []

def download_video(url, dest_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
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
            print(f"Error opening video file: {video_path}")
            return False
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            print(f"Invalid frame count: {total_frames}")
            cap.release()
            return False
            
        middle_frame_idx = total_frames // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_idx)
        
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(frame_path, frame)
            cap.release()
            return True
        else:
            print(f"Could not read frame at index {middle_frame_idx}")
            cap.release()
            return False
    except Exception as e:
        print(f"Frame extraction error: {e}")
        return False

def process_scene(scene, existing_hashes):
    scene_id = scene.get('scene_id')
    config = scene.get('scout_config', {})
    keywords = config.get('primary_keywords', [])
    min_res = config.get('min_resolution', '1080p')
    
    # Parse min_resolution
    min_width, min_height = 1920, 1080
    if min_res == '720p':
        min_width, min_height = 1280, 720
    elif min_res == '4k':
        min_width, min_height = 3840, 2160
        
    if not keywords:
        print(f"No keywords for scene {scene_id}")
        return False
        
    query = keywords[0]
    print(f"Searching for '{query}' with min resolution {min_width}x{min_height}...")
    
    candidates = search_pexels(query, min_width, min_height) + search_pixabay(query)
    
    if not candidates:
        print(f"No candidates found for '{query}'")
        return False
        
    for i, candidate in enumerate(candidates):
        video_path = os.path.join(VIDEO_DIR, f"{scene_id}_temp_{i}.mp4")
        print(f"Trying candidate {i} from {candidate['source']}...")
        
        if download_video(candidate['url'], video_path):
            frame_path = os.path.join(FRAME_DIR, f"{scene_id}_temp_{i}.jpg")
            if extract_middle_frame(video_path, frame_path):
                must_have = config.get('must_have', [])
                exclude = config.get('exclude', [])
                clip_threshold = config.get('clip_threshold', 0.25)
                
                is_valid, score = validate_frame(frame_path, keywords, must_have, exclude, threshold=clip_threshold)
                
                if is_valid:
                    new_hash = get_image_hash(frame_path)
                    if is_duplicate(new_hash, existing_hashes):
                        print(f"Candidate {i} is a duplicate of an existing scene.")
                    else:
                        final_path = os.path.join(VIDEO_DIR, f"{scene_id}.mp4")
                        os.rename(video_path, final_path)
                        
                        final_frame_path = os.path.join(FRAME_DIR, f"{scene_id}.jpg")
                        os.rename(frame_path, final_frame_path)
                        return True
                else:
                    print(f"Candidate {i} failed validation with score {score:.4f}")
            
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(frame_path):
                os.remove(frame_path)
            
    return False

if __name__ == "__main__":
    main()
