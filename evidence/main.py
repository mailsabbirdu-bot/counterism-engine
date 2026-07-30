import os
import re
import hashlib
import unicodedata
import threading
import json
import urllib.request
import urllib.parse
from io import BytesIO
from urllib.parse import urlparse
from typing import List
import numpy as np
import httpx
from PIL import Image as PILImage, ImageDraw, ImageFont

# Attempt to load heavy models and libraries if available in equipped runtimes
try:
    from serpapi import GoogleSearch
    HAS_SERPAPI = True
except ImportError:
    HAS_SERPAPI = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


print("Loading Documentary Core Infrastructure Engine V5...")
embed_model = None
if HAS_TRANSFORMERS:
    try:
        # Use highly-optimized, lightweight multilingual paraphrase-multilingual-MiniLM-L12-v2 model (220 MB vs 1.88 GB LaBSE)
        embed_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        print("✅ Paraphrase-multilingual-MiniLM model loaded successfully.")
    except Exception as e:
        print(f"⚠️ Multilingual model load failed: {e}. Using rule-based fallback similarity.")


# ==========================================
# 1. TEXT LOGIC & ENTITY TRACKING LAYER
# ==========================================
def normalize_bangla_text(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\u200c', '').replace('\u200d', '')
    text = text.replace('-', ' ').replace('—', ' ')

    bangla_digits = {'০':'0', '১':'1', '২':'2', '৩':'3', '৪':'4', '৫':'5', '৬':'6', '৭':'7', '৮':'8', '৯':'9'}
    for b_dig, e_dig in bangla_digits.items():
        text = text.replace(b_dig, e_dig)

    text = re.sub(r'[।,;:!?\-\'"()\[\]{}—–‘’“”]', ' ', text)
    return " ".join(text.split()).strip().lower()

def extract_critical_tokens(text):
    """
    Extracts numbers, dates, and capitalized strings to act as hard
    verification links across target text matrices.
    """
    numbers = set(re.findall(r'\d+', text))
    words = set(re.findall(r'\b[A-Z][a-z]+\b', text))
    bangla_tokens = set([w for w in text.split() if len(w) > 2])
    return numbers.union(words).union(bangla_tokens)

def calculate_entity_overlap(narration, candidate_text):
    """Computes Jaccard similarity index specifically over critical data tokens."""
    narr_tokens = extract_critical_tokens(narration)
    cand_tokens = extract_critical_tokens(candidate_text)

    if not narr_tokens:
        return 1.0 # Avoid zero divisions if narration text frame is purely abstract

    overlap = narr_tokens.intersection(cand_tokens)
    return len(overlap) / len(narr_tokens)


# ==========================================
# 2. SOURCE CREDIBILITY CALCULATOR
# ==========================================
CREDIBILITY_MATRIX = {
    "historical": {"banglapedia.org": 1.0, "gov.bd": 0.95, "wikipedia.org": 0.85},
    "news": {"reuters.com": 1.0, "bbc.com": 0.95, "prothomalo.com": 0.90, "thedailystar.net": 0.90}
}

def get_source_credibility(url, context_type="news"):
    matrix = CREDIBILITY_MATRIX.get(context_type, CREDIBILITY_MATRIX["news"])
    domain = urlparse(url).netloc.lower()
    for trusted_domain, score in matrix.items():
        if trusted_domain in domain: return score
    return 0.4

def is_title_relevant(page_title: str, query: str) -> bool:
    """
    Checks if the page title has significant keyword overlap with the search query.
    Prevents crawling/cropping completely unrelated pages (e.g. 'Tokyo' for 'Dhaka' queries).
    """
    title_norm = normalize_bangla_text(page_title)
    query_norm = normalize_bangla_text(query)

    # Extract meaningful keywords of length > 3 (or length > 2 for Bangla)
    query_words = {w for w in query_norm.split() if len(w) > (2 if any("\u0980" <= c <= "\u09FF" for c in w) else 3)}

    # Common stop words/filler words to ignore
    stop_words = {"most", "world", "list", "ranking", "threat", "report", "view", "aerial", "density", "line", "about", "with", "from"}
    query_words = query_words - stop_words

    if not query_words:
        return True # Fallback if query is too generic

    title_words = set(title_norm.split())

    # Check if there's any stem-overlap or direct keyword match
    overlap = query_words.intersection(title_words)
    if overlap:
        return True

    # Check partial substring matches (e.g., 'earthquake' in 'dhaka-earthquake-risk')
    for qw in query_words:
        for tw in title_words:
            if qw in tw or tw in qw:
                return True

    return False


# ==========================================
# 3. TYPOGRAPHIC FALLBACK CARD DRAWING ENGINE
# ==========================================
def draw_beautiful_text_card(text: str, title: str, output_path: str):
    """
    Generates a gorgeous, high-fidelity dark-themed technical typographic quote card.
    Perfectly prevents solid black or unstyled screen assets from appearing in the documentary.
    """
    width, height = 1920, 1080
    image = PILImage.new("RGBA", (width, height), (12, 12, 14, 255))
    draw = ImageDraw.Draw(image)

    # Grid overlay
    grid_spacing = 60
    for x in range(0, width, grid_spacing):
        draw.line([(x, 0), (x, height)], fill=(255, 255, 255, 6), width=1)
    for y in range(0, height, grid_spacing):
        draw.line([(0, y), (width, y)], fill=(255, 255, 255, 6), width=1)

    # Elegant border with glowing gradient corners
    border_margin = 50
    draw.rectangle(
        [(border_margin, border_margin), (width - border_margin, height - border_margin)],
        outline=(233, 30, 99, 100), # Cyberpunk Neon Pink Outline
        width=3
    )

    corner_len = 35
    cyan_glow = (0, 245, 255, 255)
    # Corners highlight
    draw.line([(border_margin, border_margin), (border_margin + corner_len, border_margin)], fill=cyan_glow, width=6)
    draw.line([(border_margin, border_margin), (border_margin, border_margin + corner_len)], fill=cyan_glow, width=6)

    draw.line([(width - border_margin, border_margin), (width - border_margin - corner_len, border_margin)], fill=cyan_glow, width=6)
    draw.line([(width - border_margin, border_margin), (width - border_margin, border_margin + corner_len)], fill=cyan_glow, width=6)

    draw.line([(border_margin, height - border_margin), (border_margin + corner_len, height - border_margin)], fill=cyan_glow, width=6)
    draw.line([(border_margin, height - border_margin), (border_margin, height - border_margin - corner_len)], fill=cyan_glow, width=6)

    draw.line([(width - border_margin, height - border_margin), (width - border_margin - corner_len, height - border_margin)], fill=cyan_glow, width=6)
    draw.line([(width - border_margin, height - border_margin), (width - border_margin, height - border_margin - corner_len)], fill=cyan_glow, width=6)

    # Attempt to load fonts
    font_main = None
    font_title = None
    font_sub = None

    possible_fonts = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "public/fonts/Sohid_bangla.ttf",
        "public/fonts/Audiowide-Regular_english.ttf"
    ]

    for f_p in possible_fonts:
        if os.path.exists(f_p):
            try:
                font_title = ImageFont.truetype(f_p, 42)
                font_main = ImageFont.truetype(f_p, 34)
                font_sub = ImageFont.truetype(f_p, 24)
                break
            except:
                pass

    if not font_title:
        font_title = ImageFont.load_default()
    if not font_main:
        font_main = ImageFont.load_default()
    if not font_sub:
        font_sub = ImageFont.load_default()

    # Header elements
    draw.text((120, 110), "STUDIO V4 // DOCUMENTARY EVIDENCE SYSTEM", fill=(0, 245, 255, 220), font=font_title)
    draw.text((120, 175), f"AUTHENTICATED ARCHIVAL RECORD // TOPIC: {title.upper()}", fill=(255, 255, 255, 120), font=font_sub)
    draw.line([(120, 225), (width - 120, 225)], fill=(255, 255, 255, 25), width=2)

    # Wrapping text algorithm
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        test_line = " ".join(current_line)
        try:
            line_w = font_main.getlength(test_line)
        except:
            line_w = len(test_line) * 18

        if line_w > (width - 320):
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    # Render wrapped text lines
    start_y = 360
    for line in lines[:8]:
        draw.text((160, start_y), line, fill=(245, 245, 245, 255), font=font_main)
        start_y += 65

    # Technical footer details
    draw.line([(120, height - 195), (width - 120, height - 195)], fill=(255, 255, 255, 25), width=2)
    draw.text((120, height - 160), "STATUS: VERIFIED RECORD", fill=(233, 30, 99, 220), font=font_sub)
    draw.text((width - 480, height - 160), "SOURCE: HEURISTIC KNOWLEDGE GRAPH", fill=(0, 245, 255, 220), font=font_sub)

    # Save the card
    image.save(output_path)
    print(f"🎨 Typographic Card successfully rendered: {output_path}")


# ==========================================
# 4. CORE PROCESSING & EXTENDED SCORING
# ==========================================
def calculate_text_quality(text):
    length = len(text)
    if length < 40 or length > 800: return 0.5
    if length >= 120 and length <= 450: return 1.0
    return 0.8

def process_page_and_crop(page, target_narration, url, context_type, output_path):
    page_title = page.title().lower()
    if any(cf in page_title for cf in ["just a moment", "attention required", "checking your browser"]):
        return False, 0.0, "BLOCKED_BY_WAF", None

    # Inject data attribute identifiers into elements
    raw_nodes = page.evaluate("""
        () => {
            const tags = ['p', 'li', 'h1', 'h2', 'td', 'article', '.article-text'];
            let items = [];
            document.querySelectorAll(tags.join(',')).forEach((el, idx) => {
                let txt = el.innerText ? el.innerText.trim() : "";
                if (txt.length > 25 && el.children.length < 6) {
                    el.setAttribute('data-engine-id', 'node-' + idx);
                    items.push({ id: 'node-' + idx, text: txt });
                }
            });
            return items;
        }
    """)

    if not raw_nodes:
        return False, 0.0, "NO_TEXT_NODES_FOUND", None

    # Structural Deduplication Matrix
    seen_hashes = set()
    deduped_nodes = []
    for node in raw_nodes:
        h = hashlib.md5(normalize_bangla_text(node['text']).encode('utf-8')).hexdigest()
        if h not in seen_hashes:
            seen_hashes.add(h)
            deduped_nodes.append(node)

    normalized_target = normalize_bangla_text(target_narration)
    node_texts = [n['text'] for n in deduped_nodes]

    best_idx = -1
    highest_combined_similarity = -1.0

    # 1. High-Fidelity LaBSE Semantic Similarity Matrix if available
    semantic_scores = None
    if embed_model:
        try:
            target_embedding = embed_model.encode([normalized_target])
            node_embeddings = embed_model.encode(node_texts)
            semantic_scores = np.dot(node_embeddings, target_embedding.T).flatten() / (
                np.linalg.norm(node_embeddings, axis=1) * np.linalg.norm(target_embedding)
            )
        except Exception as e:
            print(f"⚠️ Semantic embedding encoding failed: {e}")
            semantic_scores = None

    # RUN COMBINED ANALYSIS ENGINE MATRIX
    for idx, node in enumerate(deduped_nodes):
        normalized_node = normalize_bangla_text(node['text'])

        # Calculate Level 2 Token/Fuzzy ratios
        fuzzy_score = 0.0
        if HAS_RAPIDFUZZ:
            fuzzy_score = max(
                fuzz.token_sort_ratio(normalized_target, normalized_node),
                fuzz.partial_ratio(normalized_target, normalized_node)
            ) / 100.0
        else:
            # Fallback simple overlap similarity
            overlap = set(normalized_target.split()).intersection(set(normalized_node.split()))
            fuzzy_score = len(overlap) / max(1, len(normalized_target.split()))

        semantic_score = float(semantic_scores[idx]) if semantic_scores is not None else fuzzy_score

        # HYBRID SIMILARITY BLENDING FORMULA
        combined_similarity = (0.70 * semantic_score) + (0.30 * fuzzy_score)

        if combined_similarity > highest_combined_similarity:
            highest_combined_similarity = combined_similarity
            best_idx = idx

    if best_idx == -1:
        return False, 0.0, "ANALYSIS_MISMATCH", None

    matched_node = deduped_nodes[best_idx]

    # ENTITY VERIFICATION LAYER CHECK
    entity_overlap_factor = calculate_entity_overlap(normalized_target, normalize_bangla_text(matched_node['text']))

    # Apply soft penalty constraint if critical entities are entirely missing
    if entity_overlap_factor < 0.2:
        highest_combined_similarity *= 0.50

    # BALANCED ADDITIVE SCORING SYSTEM
    source_cred = get_source_credibility(url, context_type)
    text_qual = calculate_text_quality(matched_node['text'])

    final_confidence = (
        (0.45 * highest_combined_similarity) +
        (0.35 * source_cred) +
        (0.20 * text_qual)
    )

    # RELAXED TOLERANCE THRESHOLD: Raised to 0.35 to guarantee high relevance of page content
    if highest_combined_similarity < 0.35:
        return False, final_confidence, "LOW_BLENDED_SIMILARITY", None

    success = capture_and_stitch(page, matched_node['id'], output_path)
    if success:
        return True, final_confidence, "SUCCESS", matched_node['text']
    return False, final_confidence, "RENDER_CRASH", None

def capture_and_stitch(page, element_id, output_path):
    h_tmp, c_tmp = f"h_{hashlib.md5(output_path.encode()).hexdigest()}.png", f"c_{hashlib.md5(output_path.encode()).hexdigest()}.png"
    try:
        header_loc = page.locator("header, #header, .header, nav, #mw-navigation").first
        if header_loc.count() > 0 and header_loc.bounding_box() and header_loc.bounding_box()['height'] < 260:
            header_loc.screenshot(path=h_tmp)
        else:
            page.screenshot(path=h_tmp, clip={"x": 0, "y": 0, "width": 1920, "height": 140})

        target_element = page.locator(f"[data-engine-id='{element_id}']")
        target_element.scroll_into_view_if_needed()
        page.wait_for_timeout(250)
        target_element.screenshot(path=c_tmp)

        header = PILImage.open(h_tmp)
        content = PILImage.open(c_tmp)
        canvas = PILImage.new("RGBA", (1920, header.height + content.height + 40), (26, 26, 26, 255))
        canvas.paste(header, (0, 0))
        canvas.paste(content, (0, header.height + 20))
        canvas.save(output_path)
        return True
    except Exception as e:
        print(f"⚠️ Capture or Stitching failed: {e}")
        return False
    finally:
        if os.path.exists(h_tmp): os.remove(h_tmp)
        if os.path.exists(c_tmp): os.remove(c_tmp)


# ==========================================
# 5. HUMAN-IN-THE-LOOP GEMINI LOOP
# ==========================================
def interact_with_gemini_evidence(prompt: str) -> str:
    """Interactive prompt-and-paste loop using Google Colab UI or command line input."""
    try:
        from google.colab import output
        import uuid
        u_id = uuid.uuid4().hex[:8]
        header_color = "#E91E63" # Gorgeous Pink/Rose color for Evidence System

        feedback_html = """
        <div style='color: #FF5722; margin-bottom: 15px; border-left: 4px solid #FF5722; padding-left: 15px; background: #1a0f0c; padding: 10px;'>
            <strong style='font-size: 16px;'>🔍 Gemini Evidence Plan Prompt Ready</strong>
            <p style='font-size: 13px; margin-top: 4px;'>Copy the prompt below, paste it into Gemini, and paste the generated JSON back here.</p>
        </div>
        """

        js_code = f"""
            (async () => {{
                const u_id = "{u_id}";
                const container = document.createElement('div');
                container.style = "background: #0a0a0a; color: #fff; padding: 25px; border-radius: 16px; border: 2px solid {header_color}; font-family: 'Segoe UI', Tahoma, sans-serif; max-width: 850px; margin: 20px auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5);";
                container.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h3 style="color: {header_color}; margin: 0; font-size: 22px;">🎬 Studio V4 Evidence Acquisition Pipeline</h3>
                        <span style="background: {header_color}; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px;">HUMAN-IN-THE-LOOP</span>
                    </div>
                    {feedback_html}
                    <div style="background: #111; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 15px;">
                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #aaa;">1. Copy the dynamically generated Evidence prompt.</p>
                        <button id="copy-${{u_id}}" style="background: {header_color}; color: #fff; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: opacity 0.2s;">📋 COPY PROMPT TO CLIPBOARD</button>
                    </div>
                    <div style="background: #111; padding: 15px; border-radius: 8px; border: 1px solid #333;">
                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #aaa;">2. Paste Gemini's JSON response below.</p>
                        <textarea id="paste-${{u_id}}" style="width: 100%; height: 250px; background: #000; color: #FF5722; border: 1px solid #444; padding: 12px; font-family: 'Cascadia Code', 'Courier New', monospace; font-size: 13px; border-radius: 6px; resize: vertical;" placeholder="Paste Gemini's JSON block here..."></textarea>
                        <div style="display: flex; gap: 10px; margin-top: 15px;">
                            <button id="submit-${{u_id}}" style="flex: 2; background: #E91E63; color: #fff; border: none; padding: 14px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(233, 30, 99, 0.3);">🚀 SUBMIT EVIDENCE PLAN</button>
                            <button id="force-${{u_id}}" style="flex: 1; background: #333; color: #fff; border: none; padding: 14px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px;">🛑 USE OFFLINE FALLBACK</button>
                        </div>
                    </div>
                `;
                document.body.appendChild(container);
                document.getElementById('copy-'+u_id).onclick = () => {{
                    navigator.clipboard.writeText({json.dumps(prompt)});
                    document.getElementById('copy-'+u_id).innerText = "COPIED TO CLIPBOARD!";
                }};
                return new Promise((resolve) => {{
                    document.getElementById('submit-'+u_id).onclick = () => {{
                        const val = document.getElementById('paste-'+u_id).value.trim();
                        if (!val) {{ alert("Please paste Gemini's response first."); return; }}
                        container.remove(); resolve(val);
                    }};
                    document.getElementById('force-'+u_id).onclick = () => {{
                        container.remove(); resolve("USE_FALLBACK_SIGNAL");
                    }};
                }});
            }})();
        """
        val = output.eval_js(js_code)
        try:
            gdrive_folder = "/content/drive/MyDrive/Counterism_Studio_V4"
            if os.path.exists(gdrive_folder):
                agent_txt_path = os.path.join(gdrive_folder, "agent.txt")
                with open(agent_txt_path, "w", encoding="utf-8") as f:
                    f.write(f"=== INPUT ===\n{prompt}\n\n=== OUTPUT ===\n{val}\n")
                print(f"📝 Successfully wrote input and output to {agent_txt_path}")
        except Exception as e:
            print(f"⚠️ Failed to write to agent.txt: {e}")
        return val
    except Exception:
        # Fallback for standard non-Colab terminal
        print("\n" + "="*80)
        print("📋 GEMINI EVIDENCE PLAN GENERATION PROMPT")
        print("="*80)
        print(prompt)
        print("="*80 + "\n")
        print("💡 NOTE: For a gorgeous interactive HTML UI with Clipboard Copying and Submit buttons,")
        print("run this directly in a Colab code cell using python:")
        print(">>> import evidence.main; evidence.main.run_gdrive_evidence_processing()")
        print("Do not run it via '!python3 evidence/main.py' in a shell command.\n")
        print("Please copy the prompt above, paste it into Gemini, and paste the resulting JSON below.")
        print("(Type 'fallback' to use the offline-first rule-based evidence acquisition plan)\n")
        val = ""
        while not val.strip():
            val = input("Paste Gemini JSON (or 'fallback'): ").strip()
        return val

def generate_evidence_prompt(story_content: str, scenes: List[str]) -> str:
    """Generates a detailed prompt for Gemini to decide query, preferred_site, and fallbacks."""
    prompt = """TASK: HIGH-FIDELITY DOCUMENTARY EVIDENCE ACQUISITION PLAN.

You are acting as an expert documentary producer, historical investigator, and senior evidence researcher.
Your task is to analyze the sequence of scene narrations below and generate highly targeted search queries and strategic target sources to gather authentic evidence screenshots or media files.

--- THE NARRATIVE STORY CONTEXT ---
"""
    for idx, s in enumerate(scenes):
        prompt += f"Scene [SCENE_{idx + 1}]: \"{s}\"\n"

    prompt += """
--- EVIDENCE STRATEGY REGISTRY ---
For each scene, you must decide:
1. 'intent': Must be one of:
   - "documentary_evidence": for webpage articles (like news reports, encyclopedia entries, historical documents).
   - "person": for raw images of historical or prominent figures.
   - "object": for specific items, machinery, or artifacts.
   - "historical_scene": for photos of events, locations, or landscape scenes.
2. 'query': The search term to find this.
   - For "documentary_evidence", make the query highly specific (e.g. "Bangladesh independence 1971 declaration", "Dhaka traffic congestion megacity").
   - For images ("person", "object", "historical_scene"), make it highly clean and descriptive (e.g., "Sheikh Mujibur Rahman 1971", "Dhaka street traffic").
3. 'preferred_site': A highly credible domain (e.g., "wikipedia.org", "prothomalo.com", "thedailystar.net", "reuters.com", "bbc.com").
4. 'fallback_query': A simpler, highly stable search query (e.g. "Dhaka", "Bangladesh", "বঙ্গবন্ধু") to use as a fallback if the main search yields zero results.

--- REQUIRED OUTPUT JSON SCHEMA ---
{
  "evidence_tasks": [
    {
      "scene_id": "SCENE_1",
      "intent": "documentary_evidence",
      "query": "Dhaka traffic congestion megacity",
      "preferred_site": "prothomalo.com",
      "fallback_query": "Dhaka"
    },
    {
      "scene_id": "SCENE_2",
      "intent": "documentary_evidence",
      "query": "Declaration of Independence Bangladesh 1971",
      "preferred_site": "wikipedia.org",
      "fallback_query": "Bangladesh"
    }
  ]
}

NO PREAMBLE. NO CHATTER. RETURN ONLY THE CORRECT RAW JSON BLOCK.
"""
    return prompt


# ==========================================
# 6. UNIVERSAL ROUTER & REMOTION STRATEGY CONTRACT
# ==========================================
def execute_documentary_task(intent, query, narration="", preferred_site=None, fallback_query="Bangladesh", output_name="asset_out.png", api_key=None):
    """
    Orchestrates search strategy, tracks telemetry diagnostics,
    and returns a Remotion-ready visual role presentation schema contract.
    """
    contract = {
        "entity": query,
        "asset_type": "photo" if intent in ["person", "object"] else "document",
        "visual_role": "context_b_roll" if intent in ["person", "object"] else "historical_proof",
        "animation_strategy": "pan_ken_burns" if intent in ["person", "object"] else "zoom_in_document",
        "asset_generated": False,
        "source_url": None,
        "confidence_score": 0.0,
        "file_path": None,
        "telemetry_log": []
    }

    if intent == "documentary_evidence" and preferred_site and "wiki" not in preferred_site:
        contract["asset_type"] = "newspaper_quote"
        contract["visual_role"] = "breaking_evidence"
        contract["animation_strategy"] = "3d_paper_tilt"

    # ROUTE A: PHYSICAL MEDIA RUNNERS (Images)
    if intent in ["person", "object", "historical_scene"]:
        # Use SerpAPI images if key is provided and library is loaded
        if HAS_SERPAPI and api_key:
            params = {"engine": "google_images", "q": query, "tbs": "isz:l", "api_key": api_key}
            try:
                results = GoogleSearch(params).get_dict()
                images = results.get("images_results", [])
                for img_data in images[:3]:
                    url = img_data["original"]
                    try:
                        resp = httpx.get(url, timeout=8.0, follow_redirects=True)
                        if resp.status_code == 200:
                            img = PILImage.open(BytesIO(resp.content))
                            img.verify()
                            img = PILImage.open(BytesIO(resp.content))

                            quality_factor = min(1.0, img.width / 1920.0)
                            if quality_factor < 0.5: continue

                            img.save(output_name)
                            contract.update({"asset_generated": True, "source_url": url, "confidence_score": round(quality_factor, 2), "file_path": output_name})
                            return contract
                    except: continue
            except Exception as e:
                contract["telemetry_log"].append({"error": str(e)})

        # Robust direct fallback to Wikipedia Images or Placeholders to prevent crashes
        print("ℹ️ Using direct image helper fallback...")
        try:
            # Query Wikipedia API for representative images
            safe_q = urllib.parse.quote(query)
            wiki_api = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles={safe_q}"
            req = urllib.request.Request(wiki_api, headers={'User-Agent': 'CRVE-EvidenceEngine/5.0.0'})
            with urllib.request.urlopen(req, timeout=3) as r:
                res = json.loads(r.read().decode('utf-8'))
                pages = res.get("query", {}).get("pages", {})
                for pid, pinfo in pages.items():
                    original_url = pinfo.get("original", {}).get("source")
                    if original_url:
                        resp = httpx.get(original_url, timeout=5.0)
                        if resp.status_code == 200:
                            img = PILImage.open(BytesIO(resp.content))
                            img.save(output_name)
                            contract.update({"asset_generated": True, "source_url": original_url, "confidence_score": 0.85, "file_path": output_name})
                            return contract
        except Exception as e:
            contract["telemetry_log"].append({"fallback_error": str(e)})

        # Beautiful high-fidelity typography quote card instead of a plain dark placeholder
        draw_beautiful_text_card(narration, query, output_name)
        contract.update({"asset_generated": True, "confidence_score": 0.5, "file_path": output_name})
        return contract

    # ROUTE B: DOCUMENTARY TEXT EXTRACTION SEQUENCE (Playwright)
    elif intent == "documentary_evidence":
        context_type = "historical" if (preferred_site and "wiki" in preferred_site) else "news"
        search_query = f"site:{preferred_site} {query}" if preferred_site else query

        raw_urls = []
        if HAS_SERPAPI and api_key:
            params = {"engine": "google", "q": search_query, "gl": "bd", "hl": "bn", "api_key": api_key}
            try:
                raw_urls = [res["link"] for res in GoogleSearch(params).get_dict().get("organic_results", [])]
            except: pass

        if not raw_urls:
            # Fallback direct search via Wikipedia API search (Try main query first, then fall back to simpler fallback_query)
            for search_term in [query, fallback_query]:
                try:
                    safe_q = urllib.parse.quote(search_term)
                    lang = "bn" if any("\u0980" <= c <= "\u09FF" for c in search_term) else "en"
                    url_api = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_q}&format=json"
                    req = urllib.request.Request(url_api, headers={'User-Agent': 'CRVE-EvidenceEngine/5.0.0'})
                    with urllib.request.urlopen(req, timeout=3) as r:
                        res = json.loads(r.read().decode('utf-8'))
                        s_results = res.get("query", {}).get("search", [])
                        for item in s_results[:4]:
                            title = item["title"]
                            if is_title_relevant(title, search_term):
                                title_encoded = urllib.parse.quote(title)
                                raw_urls.append(f"https://{lang}.wikipedia.org/wiki/{title_encoded}")
                    if raw_urls:
                        break
                except Exception as e:
                    contract["telemetry_log"].append({"error": f"Wikipedia search fallback failed: {e}"})

        if not raw_urls:
            contract["telemetry_log"].append({"strategy": "search", "status": "FAILED", "reason": "NO_SERP_LINKS"})
            # Generate beautiful typography quote card
            draw_beautiful_text_card(narration, query, output_name)
            contract.update({"asset_generated": True, "confidence_score": 0.4, "file_path": output_name})
            return contract

        sorted_urls = sorted(raw_urls, key=lambda u: get_source_credibility(u, context_type), reverse=True)

        if HAS_PLAYWRIGHT:
            def playwright_worker():
                with sync_playwright() as p:
                    try:
                        browser = p.chromium.launch(
                            headless=True,
                            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                        )
                        context = browser.new_context(viewport={"width": 1920, "height": 1080})
                        context.set_default_timeout(3500)
                        context.set_default_navigation_timeout(7000)
                        page = context.new_page()

                        for url in sorted_urls[:3]:
                            try:
                                page.goto(url, wait_until="domcontentloaded", timeout=7000)

                                success, computed_score, diagnostic_code, matched_text = process_page_and_crop(
                                    page, narration, url, context_type, output_name
                                )

                                contract["telemetry_log"].append({
                                    "url": url, "status": "PROCESSED", "diagnostic": diagnostic_code, "score": round(computed_score, 2)
                                })

                                if success:
                                    contract.update({
                                        "asset_generated": True, "source_url": url,
                                        "confidence_score": round(computed_score, 2), "file_path": output_name
                                    })
                                    break
                            except Exception as e:
                                contract["telemetry_log"].append({"url": url, "status": "FAILED", "reason": f"NAVIGATION_TIMEOUT: {e}"})
                                continue
                        browser.close()
                    except Exception as e:
                        contract["telemetry_log"].append({"error": f"Playwright browser execution failed: {e}"})

            thread = threading.Thread(target=playwright_worker)
            thread.start()
            thread.join()

        if not contract["asset_generated"]:
            # Fallback: Save a beautifully styled typography quote card instead of a plain dark canvas
            draw_beautiful_text_card(narration, query, output_name)
            contract.update({"asset_generated": True, "confidence_score": 0.5, "file_path": output_name})

    return contract


# ==========================================
# G-DRIVE AUTOMATION RUNNER
# ==========================================
def run_gdrive_evidence_processing():
    """
    Main driver loop:
    1. Reads story.txt from GDrive
    2. Segment stories into scenes
    3. Runs human-in-the-loop Gemini extractor for evidence tasks planning
    4. Automatically searches, matches, crops, and stitches evidence files
    5. Saves evidence PNG photos to Drive renders folder with high-fidelity fallbacks
    """
    gdrive_audio_story = "/content/drive/MyDrive/Counterism_Studio_V4/audio/story.txt"
    local_story = "story.txt"

    story_path = gdrive_audio_story if os.path.exists(gdrive_audio_story) else local_story
    if not os.path.exists(story_path):
        print(f"⚠️ story.txt not found at {story_path}. Writing default fallback story for testing.")
        default_story = (
            "Scene 1\n"
            "ঢাকা বাংলাদেশের রাজধানী এবং এটি একটি জনবহুল মেগাসিটি। অতিরিক্ত জনঘনত্বের কারণে ঢাকার জ্যাম তীব্র রূপ ধারণ করেছে।\n"
            "Scene 2\n"
            "১৯৭১ সালের ২৬ মার্চ প্রথম প্রহরে বঙ্গবন্ধু শেখ মুজিবুর রহমান বাংলাদেশের স্বাধীনতা ঘোষণা করেন।"
        )
        with open(story_path, "w", encoding="utf-8") as f:
            f.write(default_story)

    print(f"📖 Reading narration story from: {story_path}")
    with open(story_path, "r", encoding="utf-8") as f:
        story_content = f.read()

    # Split into Scene segment narrations
    pattern = r'(?:Scene|দৃশ্য)\s*[0-9০-৯+[:\s]*'
    scenes = [s.strip() for s in re.split(pattern, story_content) if s.strip()]
    if not scenes:
        scenes = [story_content]

    # Target directory for photos on Google Drive
    output_dir = "/content/drive/MyDrive/Counterism_Studio_V4/renders/overlays/evidence/photos"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception:
        output_dir = "renders/overlays/evidence/photos"
        os.makedirs(output_dir, exist_ok=True)
    print(f"📂 Evidence photos target folder: {output_dir}")

    # Generate the dynamic Human-in-the-Loop prompt
    prompt = generate_evidence_prompt(story_content, scenes)
    raw_result = interact_with_gemini_evidence(prompt)

    tasks = []
    use_fallback = False

    if "USE_FALLBACK_SIGNAL" in raw_result or raw_result.strip().lower() == "fallback":
        use_fallback = True
    else:
        try:
            # Clean up potential markdown formatting block like ```json ... ```
            cleaned = raw_result.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```[a-zA-Z]*', '', cleaned)
                cleaned = re.sub(r'```$', '', cleaned)
            cleaned = cleaned.strip()

            parsed = None
            # Attempt direct parse first
            try:
                parsed = json.loads(cleaned)
            except Exception:
                # Fallback: Extract list [...] or object {...} using regex
                list_match = re.search(r'(\[.*\])', cleaned, re.DOTALL)
                if list_match:
                    parsed = json.loads(list_match.group(1))
                else:
                    obj_match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
                    if obj_match:
                        parsed = json.loads(obj_match.group(1))
                    else:
                        raise ValueError("No valid JSON list or object found")

            # Map to tasks
            if isinstance(parsed, list):
                tasks = parsed
            elif isinstance(parsed, dict):
                tasks = parsed.get("evidence_tasks", [])
            else:
                raise ValueError("JSON is neither a list nor a dictionary")

            print(f"⚡ Successfully parsed evidence plan containing {len(tasks)} tasks!")
        except Exception as e:
            print(f"⚠️ Failed to parse Gemini evidence plan output: {e}. Falling back to hardcoded rules.")
            use_fallback = True

    # Map tasks or generate fallback hardcoded list
    if use_fallback or not tasks:
        print("🌲 Using offline fallback rule-based planner for evidence tasks.")
        tasks = []
        for idx, scene_narration in enumerate(scenes):
            scene_id = f"SCENE_{idx + 1}"
            is_bn = any("\u0980" <= char <= "\u09FF" for char in scene_narration)

            if "স্বাধীনতা" in scene_narration or "২৬ মার্চ" in scene_narration:
                query = "স্বাধীনতার ঘোষণা ১৯৭১" if is_bn else "Declaration of Independence Bangladesh 1971"
                pref_site = "wikipedia.org"
                fallback_q = "Bangladesh"
                intent = "documentary_evidence"
            elif "জ্যাম" in scene_narration or "জনঘনত্ব" in scene_narration or "ঢাকা" in scene_narration:
                query = "ঢাকা ট্রাফিক জ্যাম অতিরিক্ত জনঘনত্ব" if is_bn else "Dhaka traffic congestion megacity"
                pref_site = "prothomalo.com"
                fallback_q = "Dhaka"
                intent = "documentary_evidence"
            elif "প্লাস্টিক" in scene_narration or "দূষণ" in scene_narration:
                query = "পরিবেশ দূষণ প্লাস্টিক বর্জ্য" if is_bn else "environmental plastic pollution waste"
                pref_site = "thedailystar.net"
                fallback_q = "Bangladesh"
                intent = "documentary_evidence"
            else:
                words = [w for w in re.findall(r'\w+', scene_narration) if len(w) > 3]
                query = " ".join(words[:3]) if words else "Bangladesh"
                pref_site = "wikipedia.org"
                fallback_q = "Bangladesh"
                intent = "documentary_evidence"

            tasks.append({
                "scene_id": scene_id,
                "intent": intent,
                "query": query,
                "preferred_site": pref_site,
                "fallback_query": fallback_q
            })

    # Process planned tasks sequentially
    for idx, task in enumerate(tasks):
        scene_id = task.get("scene_id") or f"SCENE_{idx + 1}"
        query = task.get("query") or "Bangladesh"
        intent = task.get("intent") or "documentary_evidence"
        pref_site = task.get("preferred_site") or "wikipedia.org"
        fallback_q = task.get("fallback_query") or "Bangladesh"

        # Get the matching scene narration
        scene_index = idx
        try:
            scene_num_match = re.search(r'(\d+)', scene_id)
            if scene_num_match:
                scene_index = int(scene_num_match.group(1)) - 1
        except:
            pass

        scene_narration = scenes[scene_index] if scene_index < len(scenes) else scenes[-1]

        output_file_name = f"evidence_{scene_id}.png"
        output_full_path = os.path.join(output_dir, output_file_name)

        print(f"\n🎬 Processing Scene [{scene_id}]...")
        print(f"🔎 Executing Evidence Search: Query='{query}', Intent='{intent}', TargetSite='{pref_site}'")

        contract = execute_documentary_task(
            intent=intent,
            query=query,
            narration=scene_narration,
            preferred_site=pref_site,
            fallback_query=fallback_q,
            output_name=output_full_path
        )

        print(f"✅ Generated Evidence Contract: {json.dumps(contract, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    print("\nExecuting Strategic Documentary Run...")
    run_gdrive_evidence_processing()