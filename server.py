#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, parse, request
import base64
import json
import mimetypes
import os
import re
import uuid


ROOT = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT / "public"
SRC_DIR = ROOT / "src"
DEFAULT_IMAGE_MODEL = "gpt-image-1.5"
OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
OPENAI_IMAGE_EDITS_URL = "https://api.openai.com/v1/images/edits"


GEO_PRESETS = {
    "SEA": {
        "code": "SEA",
        "market": "Southeast Asia",
        "region": "Southeast Asia",
        "aesthetic": "warm tropical daylight, compact city apartments, lush greenery, marketplace-friendly styling",
        "seasonalMarkers": ["monsoon freshness", "humid summer light", "festival gifting", "urban balcony greenery"],
        "culturalMarkers": ["modest casual clothing", "shared meals", "mobile-first shopping cues"],
        "colorNotes": "fresh greens, coral accents, warm neutrals",
    },
    "SG": {
        "code": "SG",
        "market": "Singapore",
        "region": "Southeast Asia",
        "aesthetic": "clean urban apartment, HDB and condo lifestyle cues, modern city greenery, polished retail lighting",
        "seasonalMarkers": ["year-round summer", "rain-ready monsoon details", "Lunar New Year gifting", "National Day accents"],
        "culturalMarkers": ["multicultural dining table", "neat compact storage", "commuter workday routines"],
        "colorNotes": "jade green, soft red accents, concrete neutrals, daylight white",
    },
    "PH": {
        "code": "PH",
        "market": "Philippines",
        "region": "Southeast Asia",
        "aesthetic": "tropical home, bright natural light, palm textures, casual family lifestyle, warm social energy",
        "seasonalMarkers": ["sunny summer", "rainy season", "holiday gifting", "beach weekend cues"],
        "culturalMarkers": ["family dining", "woven textures", "light casual clothing"],
        "colorNotes": "mango yellow, palm green, sky blue, warm white",
    },
    "IN": {
        "code": "IN",
        "market": "India",
        "region": "South Asia",
        "aesthetic": "rich home textures, festive retail styling, warm indoor light, colorful but premium composition",
        "seasonalMarkers": ["summer heat", "monsoon freshness", "winter gifting", "Diwali-inspired festive glow"],
        "culturalMarkers": ["brass accents", "rangoli-inspired patterns", "gift-ready presentation"],
        "colorNotes": "saffron, marigold, teal, ivory, warm gold",
    },
    "US": {
        "code": "US",
        "market": "United States",
        "region": "Western",
        "aesthetic": "bright editorial lifestyle, suburban home and studio settings, clean DTC product photography",
        "seasonalMarkers": ["summer outdoor use", "fall gifting", "winter cozy interior", "holiday packaging"],
        "culturalMarkers": ["minimal home decor", "commuter work setup", "gift wrap and unboxing cues"],
        "colorNotes": "navy, sage, white, graphite, seasonal accent colors",
    },
}

SCENE_CATALOG = [
    ("Lifestyle", "home", "styled on a tidy home surface with everyday context"),
    ("Lifestyle", "work", "placed in a focused desk or workday environment"),
    ("Lifestyle", "outdoor", "shown outdoors with natural regional light"),
    ("Lifestyle", "travel", "packed or carried for a short trip"),
    ("Lifestyle", "dining", "integrated into a meal or cafe moment"),
    ("Lifestyle", "leisure", "shown during a relaxed weekend activity"),
    ("Seasonal", "summer", "adapted for warm-weather seasonal demand"),
    ("Seasonal", "monsoon", "styled with rain-season freshness and practical cues"),
    ("Seasonal", "winter", "styled for cozy gifting and cooler-season shopping"),
    ("Seasonal", "festival", "styled with market-appropriate festive markers"),
    ("Use-case", "product detail", "close-up detail scene emphasizing texture and key features"),
    ("Use-case", "hands-on", "shown being held or used naturally"),
    ("Use-case", "scale", "shown with familiar objects to communicate size"),
    ("Use-case", "gift packaging", "styled as a gift or premium unboxing moment"),
    ("Geo-variant", "southeast asia", "regional Southeast Asian visual language"),
    ("Geo-variant", "south asia", "regional South Asian visual language"),
    ("Geo-variant", "western", "regional Western marketplace visual language"),
]


def load_env_file(env_path=ROOT / ".env", environ=os.environ):
    path = Path(env_path)
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
            continue
        key, raw_value = trimmed.split("=", 1)
        key = key.strip()
        value = raw_value.strip().strip("\"'")
        if key and key not in environ:
            environ[key] = value


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower())
    return slug.strip("-")


def get_geo_preset(target_geo="SEA"):
    return GEO_PRESETS.get(str(target_geo).strip().upper(), GEO_PRESETS["SEA"])


def build_scene_plans(input_data):
    count = max(1, min(10, int(input_data.get("count") or 8)))
    geo = get_geo_preset(input_data.get("targetGeo"))
    product_name = clean(input_data.get("productName") or "Product")
    product_category = clean(input_data.get("category") or "general product")
    brand_tone = clean(input_data.get("brandTone") or "marketplace-ready")
    audience = clean(input_data.get("audience") or "online shoppers")

    plans = []
    for index, scene in enumerate(select_balanced_scenes(count), start=1):
        category, scene_type, description = scene
        plans.append(
            {
                "id": f"{index:02d}-{slugify(scene_type)}",
                "index": index,
                "category": category,
                "sceneType": scene_type,
                "description": description,
                "productName": product_name,
                "productCategory": product_category,
                "brandTone": brand_tone,
                "audience": audience,
                "geo": geo,
                "dimensions": {
                    "square": "1200x1200",
                    "shopee": "1200x1200",
                    "lazada": "1200x1200",
                    "tiktokShop": "1200x1200",
                },
            }
        )
    return plans


def build_scene_prompt(plan):
    geo = plan["geo"]
    return " ".join(
        [
            f"Create a square 1200x1200 Shopee product preview image for {plan['productName']}, a {plan['productCategory']}.",
            "Use the uploaded product photo as the source of truth: preserve the exact uploaded product shape, color, material, label, logo, text, packaging, proportions, and visible details.",
            "Do not redesign the product, do not invent new packaging, do not change branding, and do not turn it into a different object.",
            "Only polish listing presentation: cleaner lighting, sharper edges, natural shadows, tidy marketplace composition, and an appropriate subtle background or context.",
            f"Scene type: {plan['category']} / {plan['sceneType']}. {plan['description']}.",
            f"Target market: {geo['market']}, {geo['region']}. Use {geo['aesthetic']}.",
            f"Seasonal and cultural filters: {', '.join(geo['seasonalMarkers'])}; {', '.join(geo['culturalMarkers'])}.",
            f"Brand tone: {plan['brandTone']}. Audience: {plan['audience']}.",
            f"Visual direction: Shopee listing hero, product remains the clear subject, realistic lighting, no fake logos, no unreadable text, {geo['colorNotes']}.",
        ]
    )


def generate_image_metadata(plan, input_data):
    product_name = clean(input_data.get("productName") or plan["productName"])
    keywords = unique(
        [
            plan["productCategory"],
            plan["sceneType"],
            plan["geo"]["market"],
            plan["geo"]["region"],
            plan["brandTone"],
            "ecommerce product photo",
            "marketplace listing",
            "lifestyle product image",
        ]
    )[:10]
    seo_tags = [slugify(keyword) for keyword in keywords if slugify(keyword)][:10]

    return {
        "id": plan["id"],
        "fileBaseName": f"{slugify(product_name)}-{plan['id']}",
        "sceneType": plan["sceneType"],
        "sceneCategory": plan["category"],
        "geo": {
            "code": plan["geo"]["code"],
            "market": plan["geo"]["market"],
            "region": plan["geo"]["region"],
        },
        "keywords": keywords,
        "seoTags": seo_tags,
        "altText": f"{product_name} shown in a {plan['sceneType']} {plan['geo']['market']} product scene for {plan['audience']}.",
        "shopeeDescription": f"{product_name} styled for {plan['geo']['market']} shoppers in a {plan['sceneType']} scene. Designed for {plan['brandTone']} brand positioning and fast marketplace listing creation.",
        "tiktokHashtags": [f"#{tag.replace('-', '')}" for tag in seo_tags[:6]],
        "platformTemplates": {
            "shopee": {"imageSize": plan["dimensions"]["shopee"], "usage": "Main listing image or variation gallery"},
            "lazada": {"imageSize": plan["dimensions"]["lazada"], "usage": "Product gallery image"},
            "tiktokShop": {"imageSize": plan["dimensions"]["tiktokShop"], "usage": "Product card, short-form commerce creative, or carousel"},
        },
    }


def build_generation_payload(input_data):
    plans = build_scene_plans(input_data)
    return {
        "plans": plans,
        "prompts": [{"id": plan["id"], "prompt": build_scene_prompt(plan)} for plan in plans],
        "metadata": [generate_image_metadata(plan, input_data) for plan in plans],
    }


def select_generation_item(input_data):
    payload = build_generation_payload(input_data)
    requested_id = input_data.get("planId")
    index = int(input_data.get("index") or 0)

    if requested_id:
        for offset, plan in enumerate(payload["plans"]):
            if plan["id"] == requested_id:
                return {
                    "plan": plan,
                    "prompt": payload["prompts"][offset]["prompt"],
                    "metadata": payload["metadata"][offset],
                }

    index = max(0, min(index, len(payload["plans"]) - 1))
    return {
        "plan": payload["plans"][index],
        "prompt": payload["prompts"][index]["prompt"],
        "metadata": payload["metadata"][index],
    }


def create_openai_image_request(prompt, model):
    return {
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "quality": "medium",
        "n": 1,
    }


def create_openai_product_preview_request(prompt, model):
    return {
        "model": model,
        "prompt": " ".join(
            [
                prompt,
                "Critical source-image constraint: preserve the exact uploaded product. Do not redesign, recolor, relabel, repackage, replace, or invent product details.",
                "Make it look like a polished Shopee product preview image while keeping the object recognizably identical to the original photo.",
            ]
        ),
        "quality": "medium",
        "size": "1024x1024",
        "n": 1,
    }


def create_openai_background_removal_request(model):
    return {
        "model": model,
        "prompt": "Isolate the main product exactly as photographed and remove the background. Return a clean PNG with a real transparent background and preserved product shape, color, label details, and edges.",
        "background": "transparent",
        "quality": "medium",
        "size": "1024x1024",
        "n": 1,
    }


def normalize_uploaded_image(image):
    mime_type = image.get("mimeType") or "application/octet-stream"
    if not mime_type.startswith("image/"):
        raise ValueError("Only image uploads are supported")
    raw_b64 = image.get("b64") or ""
    if "," in raw_b64:
        raw_b64 = raw_b64.split(",", 1)[1]
    data = base64.b64decode(raw_b64, validate=True)
    if len(data) > 50 * 1024 * 1024:
        raise ValueError("Image upload must be under 50MB")
    return {
        "name": slugify(Path(image.get("name") or "product.png").stem) or "product",
        "mimeType": mime_type,
        "data": data,
    }


def generate_openai_image(prompt, api_key, model):
    body = json.dumps(create_openai_image_request(prompt, model)).encode("utf-8")
    req = request.Request(
        OPENAI_IMAGES_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(detail).get("error", {}).get("message") or detail
        except json.JSONDecodeError:
            message = detail or f"OpenAI image request failed with HTTP {exc.code}"
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc

    b64 = (data.get("data") or [{}])[0].get("b64_json")
    if not b64:
        raise RuntimeError("OpenAI image response did not include b64_json")
    return b64


def remove_background_openai(image, api_key, model):
    fields = create_openai_background_removal_request(model)
    boundary = f"----codex-boundary-{uuid.uuid4().hex}"
    body = build_multipart_body(boundary, fields, image)
    req = request.Request(
        OPENAI_IMAGE_EDITS_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )

    try:
        with request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(detail).get("error", {}).get("message") or detail
        except json.JSONDecodeError:
            message = detail or f"OpenAI background removal failed with HTTP {exc.code}"
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc

    b64 = (data.get("data") or [{}])[0].get("b64_json")
    if not b64:
        raise RuntimeError("OpenAI edit response did not include b64_json")
    return b64


def polish_product_preview_openai(prompt, images, api_key, model):
    fields = create_openai_product_preview_request(prompt, model)
    boundary = f"----codex-boundary-{uuid.uuid4().hex}"
    body = build_multipart_body(boundary, fields, images[0])
    req = request.Request(
        OPENAI_IMAGE_EDITS_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )

    try:
        with request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(detail).get("error", {}).get("message") or detail
        except json.JSONDecodeError:
            message = detail or f"OpenAI product preview edit failed with HTTP {exc.code}"
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc

    b64 = (data.get("data") or [{}])[0].get("b64_json")
    if not b64:
        raise RuntimeError("OpenAI edit response did not include b64_json")
    return b64


def build_multipart_body(boundary, fields, image):
    chunks = []
    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    extension = mimetypes.guess_extension(image["mimeType"]) or ".png"
    filename = f"{image['name']}{extension}"
    chunks.append(f"--{boundary}\r\n".encode("utf-8"))
    chunks.append(f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode("utf-8"))
    chunks.append(f"Content-Type: {image['mimeType']}\r\n\r\n".encode("utf-8"))
    chunks.append(image["data"])
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)


class ScenarioRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = parse.urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json(
                200,
                {
                    "ok": True,
                    "imageModel": image_model(),
                    "openaiConfigured": bool(os.environ.get("OPENAI_API_KEY")),
                },
            )
            return
        self.serve_static(parsed.path)

    def do_HEAD(self):
        parsed = parse.urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            return
        self.serve_static(parsed.path, head_only=True)

    def do_POST(self):
        parsed = parse.urlparse(self.path)
        if parsed.path == "/api/generate-scenes":
            self.handle_generate_scenes()
            return
        if parsed.path == "/api/generate-scene":
            self.handle_generate_scene()
            return
        if parsed.path == "/api/remove-background":
            self.handle_remove_background()
            return
        if parsed.path not in ("/api/generate-scenes", "/api/generate-scene", "/api/remove-background"):
            self.send_json(404, {"error": "Not found"})
            return

    def handle_generate_scenes(self):
        try:
            body = self.read_json_body()
            payload = build_generation_payload(body)
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self.send_json(200, {"mode": "fallback", "reason": "OPENAI_API_KEY is not configured", **payload, "images": []})
                return

            images = []
            prompts_by_id = {item["id"]: item["prompt"] for item in payload["prompts"]}
            for plan in payload["plans"]:
                try:
                    image = generate_openai_image(prompts_by_id[plan["id"]], api_key, image_model())
                    images.append({"id": plan["id"], "source": "openai", "model": image_model(), "mimeType": "image/png", "b64": image})
                except RuntimeError as exc:
                    images.append({"id": plan["id"], "source": "fallback", "error": str(exc)})

            mode = "openai" if any(image["source"] == "openai" for image in images) else "fallback"
            self.send_json(200, {"mode": mode, "model": image_model(), **payload, "images": images})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_generate_scene(self):
        try:
            body = self.read_json_body(max_size=80_000_000)
            item = select_generation_item(body)
            api_key = os.environ.get("OPENAI_API_KEY")
            image = None
            uploaded_images = []
            for uploaded in (body.get("productImages") or [])[:4]:
                try:
                    uploaded_images.append(normalize_uploaded_image(uploaded))
                except ValueError:
                    continue

            if api_key:
                try:
                    if uploaded_images:
                        b64 = polish_product_preview_openai(item["prompt"], uploaded_images, api_key, image_model())
                    else:
                        b64 = generate_openai_image(item["prompt"], api_key, image_model())
                    image = {
                        "id": item["plan"]["id"],
                        "source": "openai",
                        "model": image_model(),
                        "mimeType": "image/png",
                        "b64": b64,
                        "method": "edit" if uploaded_images else "generation",
                    }
                except RuntimeError as exc:
                    image = {"id": item["plan"]["id"], "source": "fallback", "error": str(exc)}
            else:
                image = {"id": item["plan"]["id"], "source": "fallback", "error": "OPENAI_API_KEY is not configured"}
            mode = "openai" if image["source"] == "openai" else "fallback"
            self.send_json(200, {"mode": mode, "model": image_model(), **item, "image": image})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_remove_background(self):
        try:
            body = self.read_json_body(max_size=80_000_000)
            images = body.get("images") or []
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self.send_json(200, {"mode": "fallback", "reason": "OPENAI_API_KEY is not configured", "images": []})
                return

            outputs = []
            for image in images[:4]:
                try:
                    normalized = normalize_uploaded_image(image)
                    b64 = remove_background_openai(normalized, api_key, image_model())
                    outputs.append({
                        "name": image.get("name") or normalized["name"],
                        "source": "openai",
                        "mimeType": "image/png",
                        "b64": b64,
                    })
                except (RuntimeError, ValueError) as exc:
                    outputs.append({
                        "name": image.get("name") or "image",
                        "source": "fallback",
                        "error": str(exc),
                    })

            mode = "openai" if any(item["source"] == "openai" for item in outputs) else "fallback"
            self.send_json(200, {"mode": mode, "model": image_model(), "images": outputs})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def serve_static(self, raw_path, head_only=False):
        base_dir = SRC_DIR if raw_path.startswith("/src/") else PUBLIC_DIR
        relative = raw_path[len("/src/") :] if raw_path.startswith("/src/") else raw_path.lstrip("/")
        relative = "index.html" if relative in ("", "/") else relative
        file_path = (base_dir / parse.unquote(relative)).resolve()

        if not str(file_path).startswith(str(base_dir.resolve())):
            self.send_json(403, {"error": "Forbidden"})
            return
        if not file_path.exists() or not file_path.is_file():
            self.send_json(404, {"error": "Not found"})
            return

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        if file_path.suffix == ".js":
            content_type = "text/javascript; charset=utf-8"
        elif file_path.suffix in (".html", ".css", ".json"):
            content_type = f"{content_type}; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        if not head_only:
            self.wfile.write(file_path.read_bytes())

    def read_json_body(self, max_size=1_000_000):
        length = int(self.headers.get("Content-Length", "0"))
        if length > max_size:
            raise json.JSONDecodeError("Request body too large", "", 0)
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def send_json(self, status_code, body):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        return


def image_model():
    return os.environ.get("OPENAI_IMAGE_MODEL", DEFAULT_IMAGE_MODEL)


def select_balanced_scenes(count):
    groups = {}
    for scene in SCENE_CATALOG:
        groups.setdefault(scene[0], []).append(scene)

    selected = []
    used = set()
    for scenes in groups.values():
        if len(selected) >= count:
            break
        selected.append(scenes[0])
        used.add(scenes[0])

    for scene in SCENE_CATALOG:
        if len(selected) >= count:
            break
        if scene not in used:
            selected.append(scene)
            used.add(scene)
    return selected


def clean(value):
    return re.sub(r"\s+", " ", str(value).strip())


def unique(values):
    seen = set()
    output = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output


def main():
    load_env_file()
    port = int(os.environ.get("PORT", "3000"))
    server = ThreadingHTTPServer(("localhost", port), ScenarioRequestHandler)
    print(f"Product scenario generator running at http://localhost:{port}")
    print(f"OpenAI image model: {image_model()}")
    server.serve_forever()


if __name__ == "__main__":
    main()
