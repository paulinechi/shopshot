import base64
import json
import mimetypes
import os
import re
import socket
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib import error, parse, request
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"
SRC_DIR = ROOT / "src"
CATEGORY_SAMPLE_PATH = ROOT / "data" / "shopee_categories.sample.json"
SHOPEE_TEMPLATE_PATH = (
    ROOT / "team_docs" / "Shopee_mass_upload_2026-06-06_basic_template.xlsx"
)
DEFAULT_IMAGE_MODEL = "gpt-image-1.5"
DEFAULT_TEXT_MODEL = "gpt-5.5"
IMAGE_MODEL_OPTIONS = [
    "gpt-image-2",
    "gpt-image-1.5",
    "gpt-image-1",
    "gpt-image-1-mini",
]
TEXT_MODEL_OPTIONS = ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.1"]
OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
OPENAI_IMAGE_EDITS_URL = "https://api.openai.com/v1/images/edits"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
MOBILE_UPLOAD_SESSIONS = {}


GEO_PRESETS = {
    "SEA": {
        "code": "SEA",
        "market": "Southeast Asia",
        "region": "Southeast Asia",
        "aesthetic": "warm tropical daylight, compact city apartments, lush greenery, marketplace-friendly styling",
        "seasonalMarkers": [
            "monsoon freshness",
            "humid summer light",
            "festival gifting",
            "urban balcony greenery",
        ],
        "culturalMarkers": [
            "modest casual clothing",
            "shared meals",
            "mobile-first shopping cues",
        ],
        "colorNotes": "fresh greens, coral accents, warm neutrals",
    },
    "SG": {
        "code": "SG",
        "market": "Singapore",
        "region": "Southeast Asia",
        "aesthetic": "clean urban apartment, HDB and condo lifestyle cues, modern city greenery, polished retail lighting",
        "seasonalMarkers": [
            "year-round summer",
            "rain-ready monsoon details",
            "Lunar New Year gifting",
            "National Day accents",
        ],
        "culturalMarkers": [
            "multicultural dining table",
            "neat compact storage",
            "commuter workday routines",
        ],
        "colorNotes": "jade green, soft red accents, concrete neutrals, daylight white",
    },
    "PH": {
        "code": "PH",
        "market": "Philippines",
        "region": "Southeast Asia",
        "aesthetic": "tropical home, bright natural light, palm textures, casual family lifestyle, warm social energy",
        "seasonalMarkers": [
            "sunny summer",
            "rainy season",
            "holiday gifting",
            "beach weekend cues",
        ],
        "culturalMarkers": ["family dining", "woven textures", "light casual clothing"],
        "colorNotes": "mango yellow, palm green, sky blue, warm white",
    },
    "IN": {
        "code": "IN",
        "market": "India",
        "region": "South Asia",
        "aesthetic": "rich home textures, festive retail styling, warm indoor light, colorful but premium composition",
        "seasonalMarkers": [
            "summer heat",
            "monsoon freshness",
            "winter gifting",
            "Diwali-inspired festive glow",
        ],
        "culturalMarkers": [
            "brass accents",
            "rangoli-inspired patterns",
            "gift-ready presentation",
        ],
        "colorNotes": "saffron, marigold, teal, ivory, warm gold",
    },
    "US": {
        "code": "US",
        "market": "United States",
        "region": "Western",
        "aesthetic": "bright editorial lifestyle, suburban home and studio settings, clean DTC product photography",
        "seasonalMarkers": [
            "summer outdoor use",
            "fall gifting",
            "winter cozy interior",
            "holiday packaging",
        ],
        "culturalMarkers": [
            "minimal home decor",
            "commuter work setup",
            "gift wrap and unboxing cues",
        ],
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
    (
        "Use-case",
        "product detail",
        "close-up detail scene emphasizing texture and key features",
    ),
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


def default_categories():
    if CATEGORY_SAMPLE_PATH.exists():
        records = json.loads(CATEGORY_SAMPLE_PATH.read_text(encoding="utf-8"))
    else:
        records = [
            {
                "category_id": 100000,
                "parent_category_id": 0,
                "original_category_name": "Electronics & Gadgets",
                "has_children": True,
            },
            {
                "category_id": 100001,
                "parent_category_id": 100000,
                "original_category_name": "Mobile Accessories",
                "has_children": False,
            },
            {
                "category_id": 200000,
                "parent_category_id": 0,
                "original_category_name": "Health & Beauty",
                "has_children": True,
            },
            {
                "category_id": 200001,
                "parent_category_id": 200000,
                "original_category_name": "Skincare",
                "has_children": False,
            },
        ]
    categories = build_category_paths(records)
    for category in extract_shopee_template_categories():
        categories[category["category_id"]] = category
    return categories


def extract_shopee_template_categories(template_path=SHOPEE_TEMPLATE_PATH):
    rows = read_xlsx_sheet_rows(template_path, "Pre-order DTS Range", max_rows=20000)
    if not rows:
        return []
    headers = [split_template_key(value) for value in rows[0]]
    try:
        name_index = headers.index("et_title_category_name")
        category_index = headers.index("et_title_category_id")
    except ValueError:
        return []
    dts_index = headers.index("et_title_dts_range") if "et_title_dts_range" in headers else -1

    categories = {}
    for row in rows[6:]:
        if category_index >= len(row):
            continue
        raw_id = clean(row[category_index])
        if not raw_id.isdigit():
            continue
        category_id = int(raw_id)
        raw_name = clean(row[name_index]) if name_index < len(row) else ""
        path = parse_template_category_path(raw_name, category_id)
        if not path:
            continue
        dts_range = clean(row[dts_index]) if dts_index >= 0 and dts_index < len(row) else ""
        categories[category_id] = {
            "category_id": category_id,
            "parent_category_id": 0,
            "original_category_name": path.split(" > ")[-1],
            "display_path": path,
            "has_children": False,
            "pre_order_dts_range": dts_range,
            "source": "xlsx",
        }
    return sorted(categories.values(), key=lambda item: item["display_path"])


def parse_template_category_path(raw_name, category_id):
    value = clean(raw_name)
    if not value:
        return ""
    prefix = f"{category_id}-"
    if value.startswith(prefix):
        value = value[len(prefix):]
    elif "-" in value and value.split("-", 1)[0].isdigit():
        value = value.split("-", 1)[1]
    parts = [clean(part) for part in value.split("/") if clean(part)]
    return " > ".join(parts)


def build_category_paths(records):
    categories = {}
    for record in records:
        category_id = int(record["category_id"])
        categories[category_id] = {
            "category_id": category_id,
            "parent_category_id": int(record.get("parent_category_id") or 0),
            "original_category_name": record.get("original_category_name")
            or record.get("category_name")
            or "Unnamed",
            "has_children": bool(record.get("has_children")),
        }

    def display_path(category_id):
        record = categories[category_id]
        parent_id = record["parent_category_id"]
        if parent_id and parent_id in categories:
            return f"{display_path(parent_id)} > {record['original_category_name']}"
        return record["original_category_name"]

    for category_id in categories:
        categories[category_id]["display_path"] = display_path(category_id)
    return categories


def public_categories():
    return sorted(default_categories().values(), key=lambda item: item["display_path"])


def build_mobile_upload_url(host, session_id, fallback_host=""):
    clean_host = clean(host).split(",", 1)[0] or f"{get_lan_ip()}:3000"
    if clean_host.startswith("localhost") or clean_host.startswith("127.0.0.1"):
        port = clean_host.split(":", 1)[1] if ":" in clean_host else "3000"
        clean_host = f"{get_lan_ip()}:{port}"
    elif ":" not in clean_host:
        fallback = clean(fallback_host).split(",", 1)[0]
        port = fallback.split(":", 1)[1] if ":" in fallback else "3000"
        clean_host = f"{clean_host}:{port}"
    query = parse.urlencode({"session": session_id})
    return f"http://{clean_host}/mobile-upload?{query}"


def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def create_mobile_upload_session(host, session_id=""):
    session_id = clean(session_id) or uuid.uuid4().hex[:12]
    MOBILE_UPLOAD_SESSIONS.setdefault(session_id, [])
    upload_url = build_mobile_upload_url(host, session_id, fallback_host=host)
    qr_image_url = (
        "https://api.qrserver.com/v1/create-qr-code/?"
        + parse.urlencode({"size": "180x180", "data": upload_url})
    )
    return {
        "session": session_id,
        "uploadUrl": upload_url,
        "qrImageUrl": qr_image_url,
    }


def add_mobile_uploads(session_id, images):
    if not session_id or session_id not in MOBILE_UPLOAD_SESSIONS:
        MOBILE_UPLOAD_SESSIONS[session_id] = []
    stored = MOBILE_UPLOAD_SESSIONS[session_id]
    for image in images[:12]:
        normalized = {
            "id": uuid.uuid4().hex,
            "name": clean(image.get("name") or "phone-photo.jpg") or "phone-photo.jpg",
            "mimeType": clean(image.get("mimeType") or "image/jpeg"),
            "b64": image.get("b64") or "",
            "uploadedAt": image.get("uploadedAt") or "",
        }
        if normalized["mimeType"].startswith("image/") and normalized["b64"]:
            stored.append(normalized)
    del stored[80:]
    return stored


def suggest_category(text, categories=None):
    categories = categories or default_categories()
    query = clean(text).lower()
    if not query:
        return None

    keyword_map = [
        (
            (
                "skincare",
                "beauty",
                "cosmetic",
                "makeup",
                "serum",
                "cream",
                "cleanser",
                "health",
            ),
            "Health & Beauty",
        ),
        (
            (
                "phone",
                "charger",
                "cable",
                "usb",
                "electronic",
                "gadget",
                "earbud",
                "audio",
                "computer",
            ),
            "Electronics & Gadgets",
        ),
    ]

    preferred_root = None
    for keywords, root in keyword_map:
        if any(keyword in query for keyword in keywords):
            preferred_root = root
            break

    candidates = [item for item in categories.values() if not item["has_children"]]
    if preferred_root:
        candidates = [
            item
            for item in candidates
            if item["display_path"].startswith(preferred_root)
        ] or candidates

    scored = []
    tokens = set(re.findall(r"[a-z0-9]+", query))
    for item in candidates:
        path = item["display_path"].lower()
        score = sum(1 for token in tokens if token in path)
        if preferred_root and item["display_path"].startswith(preferred_root):
            score += 3
        if (
            any(token in query for token in ["phone", "charger", "cable", "usb"])
            and "mobile accessories" in path
        ):
            score += 4
        if (
            any(token in query for token in ["serum", "cream", "cleanser", "skincare"])
            and "skincare" in path
        ):
            score += 4
        scored.append((score, item))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["display_path"]))
    if not scored or scored[0][0] <= 0:
        return None
    item = scored[0][1]
    return {
        "value": {
            "category_id": item["category_id"],
            "category_path": item["display_path"],
        },
        "source": "inferred",
        "confidence": "medium" if scored[0][0] >= 3 else "low",
        "needs_user_review": True,
    }


def field(value, source="generated", confidence="medium", needs_user_review=True):
    return {
        "value": value,
        "source": source,
        "confidence": confidence,
        "needs_user_review": needs_user_review,
    }


def generate_listing_draft(input_data):
    product_name = clean(
        input_data.get("productName")
        or input_data.get("product_name")
        or "Your Product"
    )
    product_note = clean(
        input_data.get("productNote") or input_data.get("product_note") or ""
    )
    category_hint = clean(
        input_data.get("categoryHint") or input_data.get("category") or ""
    )
    brand = clean(input_data.get("brand") or "")
    price = clean_seller_value(input_data.get("price") or "")
    stock = clean_seller_value(input_data.get("stock") or "")
    weight = clean_seller_value(input_data.get("weight") or "")
    dimension_parts = parse_dimensions(input_data)
    dimensions = " x ".join(
        value
        for value in [
            dimension_parts["length"],
            dimension_parts["width"],
            dimension_parts["height"],
        ]
        if value
    )
    target_geo = clean(input_data.get("targetGeo") or "SG")
    geo = get_geo_preset(target_geo)
    brand_tone = clean(input_data.get("brandTone") or "marketplace-ready")
    audience = clean(input_data.get("audience") or "online shoppers")
    category_text = " ".join([product_name, product_note, category_hint])
    selected_category_id = input_data.get("categoryId") or input_data.get("category_id")
    selected_category = (
        default_categories().get(int(selected_category_id))
        if selected_category_id
        else None
    )
    if selected_category:
        category_suggestion = {
            "value": {
                "category_id": selected_category["category_id"],
                "category_path": selected_category["display_path"],
            },
            "source": "provided",
            "confidence": "high",
            "needs_user_review": False,
        }
    else:
        category_suggestion = suggest_category(category_text)
    category_value = (
        category_suggestion["value"]
        if category_suggestion
        else {"category_id": None, "category_path": ""}
    )
    product_type = infer_product_type(
        product_name,
        product_note,
        category_hint,
        category_value.get("category_path", ""),
    )
    keywords = build_keywords(
        product_name, product_type, target_geo, category_value.get("category_path", "")
    )
    highlights = build_highlights(
        product_name,
        product_note,
        category_value.get("category_path", ""),
        brand_tone,
        audience,
        geo["market"],
        dimension_parts,
    )
    description = build_description(
        product_name,
        highlights,
        brand,
        brand_tone,
        audience,
        geo["market"],
        product_note,
        category_value.get("category_path", ""),
    )
    title = build_listing_title(product_name, product_type, target_geo, brand_tone)
    missing_fields = detect_missing_fields(
        {
            "productName": product_name,
            "category_id": category_value.get("category_id"),
            "price": price,
            "stock": stock,
            "weight": weight,
            "length": dimension_parts.get("length"),
            "width": dimension_parts.get("width"),
            "height": dimension_parts.get("height"),
            "description": description,
        }
    )
    readiness = calculate_readiness(
        {
            "productName": product_name,
            "category_id": category_value.get("category_id"),
            "category_confirmed": bool(input_data.get("categoryConfirmed")),
            "price": price,
            "stock": stock,
            "weight": weight,
            "length": dimension_parts.get("length"),
            "width": dimension_parts.get("width"),
            "height": dimension_parts.get("height"),
            "description": description,
            "images_count": int(
                input_data.get("imagesCount")
                or len(input_data.get("productImages") or [])
            ),
            "confirmed_fields": input_data.get("confirmedFields") or [],
            "missing_fields": missing_fields,
        }
    )

    return {
        "product_profile": {
            "detected_product_type": field(product_type, "inferred", "medium", True),
            "suggested_category": category_suggestion
            or field(
                {"category_id": None, "category_path": ""}, "missing", "low", True
            ),
            "visible_attributes": infer_visible_attributes(category_text),
            "provided_by_user": {
                "product_note": product_note,
                "brand": brand,
                "price": price,
                "stock": stock,
                "weight": weight,
                "dimensions": dimensions,
                "length": dimension_parts["length"],
                "width": dimension_parts["width"],
                "height": dimension_parts["height"],
                "brand_tone": brand_tone,
                "audience": audience,
            },
            "uncertain_details": ["material", "exact dimensions", "weight", "warranty"],
        },
        "listing_draft": {
            "title": field(title, "generated", "medium", True),
            "category": category_suggestion
            or field(
                {"category_id": None, "category_path": ""}, "missing", "low", True
            ),
            "description": field(description, "generated", "medium", True),
            "highlights": [
                field(item, "generated", "medium", True) for item in highlights
            ],
            "keywords": keywords,
            "hashtags": [
                f"#{slugify(keyword).replace('-', '')}" for keyword in keywords[:6]
            ],
            "alt_text": field(
                f"{product_name} shown as a polished product preview.",
                "generated",
                "medium",
                True,
            ),
            "brand": field(
                brand,
                "provided" if brand else "missing",
                "high" if brand else "low",
                not bool(brand),
            ),
            "price": field(
                price,
                "provided" if price else "missing",
                "high" if price else "low",
                not bool(price),
            ),
            "stock": field(
                stock,
                "provided" if stock else "missing",
                "high" if stock else "low",
                not bool(stock),
            ),
            "weight": field(
                weight,
                "provided" if weight else "missing",
                "high" if weight else "low",
                not bool(weight),
            ),
            "dimensions": field(
                dimension_parts,
                "provided" if all(dimension_parts.values()) else "missing",
                "medium",
                not all(dimension_parts.values()),
            ),
            "attributes": infer_attributes(
                category_text, category_value.get("category_path", "")
            ),
            "variations": [],
        },
        "missing_fields": missing_fields,
        "category_suggestions": [category_suggestion] if category_suggestion else [],
        "readiness": readiness,
    }


def create_openai_listing_draft_request(input_data, local_draft, model):
    listing = local_draft.get("listing_draft") or {}
    profile = local_draft.get("product_profile") or {}
    category = (listing.get("category") or {}).get("value") or {}
    dimensions = (listing.get("dimensions") or {}).get("value") or {}
    geo = get_geo_preset(input_data.get("targetGeo") or "SG")
    context = {
        "product_name": clean(
            input_data.get("productName") or input_data.get("product_name") or ""
        ),
        "seller_product_notes": clean(
            input_data.get("productNote") or input_data.get("product_note") or ""
        ),
        "brand": clean(input_data.get("brand") or ""),
        "brand_tone": clean(input_data.get("brandTone") or ""),
        "audience": clean(input_data.get("audience") or ""),
        "target_geo": geo["market"],
        "category": category,
        "detected_product_type": (
            profile.get("detected_product_type") or {}
        ).get("value"),
        "visible_attributes": profile.get("visible_attributes") or [],
        "seller_owned_fields_to_preserve": {
            "price": (listing.get("price") or {}).get("value"),
            "stock": (listing.get("stock") or {}).get("value"),
            "weight": (listing.get("weight") or {}).get("value"),
            "dimensions": dimensions,
        },
        "local_fallback_copy": {
            "title": (listing.get("title") or {}).get("value"),
            "description": (listing.get("description") or {}).get("value"),
            "highlights": [
                item.get("value")
                for item in (listing.get("highlights") or [])
                if item.get("value")
            ],
            "keywords": listing.get("keywords") or [],
            "hashtags": listing.get("hashtags") or [],
        },
    }
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "highlights": {
                "type": "array",
                "items": {"type": "string"},
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
            },
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
            },
            "alt_text": {"type": "string"},
        },
        "required": [
            "title",
            "description",
            "highlights",
            "keywords",
            "hashtags",
            "alt_text",
        ],
    }
    return {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": (
                    "You are an expert e-commerce product listing copywriter. "
                    "Generate natural, specific marketplace-ready JSON copy from seller inputs. "
                    "Use the provided brand tone, audience, geo, category, product notes, and dimensions. "
                    "Do not invent certifications, warranty, medical effects, materials, compatibility, "
                    "or shipping promises unless explicitly present. Keep seller-owned facts unchanged. "
                    "Make the output feel written for a real product, not a template."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return JSON only for this listing copy task. "
                    "Title should be concise and search-friendly. "
                    "Description should be polished, buyer-facing, and grounded in the inputs. "
                    "Highlights should be benefit-led and concrete.\n\n"
                    + json.dumps(context, ensure_ascii=False)
                ),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "listing_copy",
                "description": "Marketplace listing copy fields for a product draft.",
                "strict": True,
                "schema": schema,
            }
        },
    }


def extract_openai_response_text(data):
    output_text = clean(data.get("output_text") or "")
    if output_text:
        return output_text

    for item in data.get("output") or []:
        for content in item.get("content") or []:
            if content.get("refusal"):
                raise RuntimeError(content["refusal"])
            text = clean(content.get("text") or "")
            if text:
                return text

    raise RuntimeError("OpenAI text response did not include output text")


def generate_openai_listing_draft(input_data, local_draft, api_key, model):
    body = json.dumps(
        create_openai_listing_draft_request(input_data, local_draft, model)
    ).encode("utf-8")
    req = request.Request(
        OPENAI_RESPONSES_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(detail).get("error", {}).get("message") or detail
        except json.JSONDecodeError:
            message = detail or f"OpenAI text request failed with HTTP {exc.code}"
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc

    try:
        return json.loads(extract_openai_response_text(data))
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI text response was not valid JSON") from exc


def openai_string(value):
    return clean(value) if isinstance(value, str) else ""


def apply_openai_listing_copy(local_draft, ai_copy, model):
    listing = local_draft.get("listing_draft") or {}
    title = openai_string(ai_copy.get("title"))
    description = openai_string(ai_copy.get("description"))
    highlights = [
        openai_string(item)
        for item in (ai_copy.get("highlights") or [])
        if openai_string(item)
    ][:6]
    keywords = [
        openai_string(item)
        for item in (ai_copy.get("keywords") or [])
        if openai_string(item)
    ][:10]
    hashtags = [
        openai_string(item)
        for item in (ai_copy.get("hashtags") or [])
        if openai_string(item)
    ][:10]
    alt_text = openai_string(ai_copy.get("alt_text"))

    if title:
        listing["title"] = field(title, "openai", "medium", True)
    if description:
        listing["description"] = field(description, "openai", "medium", True)
    if highlights:
        listing["highlights"] = [
            field(item, "openai", "medium", True) for item in highlights
        ]
    if keywords:
        listing["keywords"] = keywords
    if hashtags:
        listing["hashtags"] = [
            item if item.startswith("#") else f"#{slugify(item).replace('-', '')}"
            for item in hashtags
        ]
    if alt_text:
        listing["alt_text"] = field(alt_text, "openai", "medium", True)

    local_draft["listing_draft"] = listing
    local_draft["text_generation"] = {"source": "openai", "model": model}
    return local_draft


def infer_product_type(product_name, product_note, category_hint, category_path):
    text = " ".join([product_name, product_note, category_hint, category_path]).lower()
    if any(
        token in text
        for token in ["serum", "skincare", "cream", "cleanser", "makeup", "beauty"]
    ):
        return "Health & Beauty Product"
    if any(
        token in text
        for token in [
            "charger",
            "cable",
            "usb",
            "phone",
            "earbud",
            "gadget",
            "electronic",
        ]
    ):
        return "Electronics Accessory"
    return product_name.split()[0] if product_name else "Product"


def parse_dimensions(value):
    if isinstance(value, dict):
        explicit = {
            "length": clean(value.get("length") or ""),
            "width": clean(value.get("width") or ""),
            "height": clean(value.get("height") or ""),
        }
        if any(explicit.values()):
            return explicit
        value = value.get("dimensions") or ""
    numbers = re.findall(r"\d+(?:\.\d+)?", str(value or ""))
    keys = ("length", "width", "height")
    return {
        key: numbers[index] if index < len(numbers) else ""
        for index, key in enumerate(keys)
    }


def build_listing_title(product_name, product_type, target_geo, brand_tone=""):
    suffix = "SG Ready" if target_geo == "SG" else "Marketplace Ready"
    tone = clean(brand_tone).split(",", 1)[0].title() if brand_tone else ""
    parts = [product_name]
    if tone and tone.lower() not in product_name.lower():
        parts.append(tone)
    parts.extend([product_type, suffix])
    return " | ".join(part for part in parts if part)


def build_highlights(product_name, product_note, category_path, brand_tone="", audience="", market="", dimensions=None):
    dimensions = dimensions or {}
    highlights = [
        f"Designed for {audience or 'online shoppers'} with a {brand_tone or 'marketplace-ready'} brand feel"
    ]
    if product_note:
        highlights.append(f"Seller-confirmed details: {product_note}")
    if category_path:
        highlights.append(f"Recommended category: {category_path}")
    if market:
        highlights.append(f"Localized for {market} marketplace buyers")
    if all(dimensions.get(key) for key in ("length", "width", "height")):
        highlights.append(
            f"Packed size reference: {dimensions['length']} x {dimensions['width']} x {dimensions['height']}"
        )
    highlights.append("Preview images and listing copy are prepared for template export review")
    return highlights[:5]


def build_description(product_name, highlights, brand, brand_tone="", audience="", market="", product_note="", category_path=""):
    brand_line = f" from {brand}" if brand else ""
    bullet_text = "\n".join(f"- {item}" for item in highlights)
    positioning = (
        f"{product_name}{brand_line} is prepared for {market or 'marketplace'} shoppers "
        f"with a {brand_tone or 'clear, trustworthy'} tone for {audience or 'online buyers'}."
    )
    detail = f" Seller-provided product notes: {product_note}." if product_note else ""
    category = f" Drafted under {category_path}." if category_path else ""
    return (
        f"{positioning}{detail}{category}\n\n"
        f"Key selling points:\n{bullet_text}\n\n"
        "Review seller-owned facts such as warranty, ingredients, certifications, and shipping rules before publishing."
    )


def build_keywords(product_name, product_type, target_geo, category_path):
    values = [product_name, product_type, "marketplace", target_geo]
    values.extend(category_path.split(" > ") if category_path else [])
    return [
        slugify(value).replace("-", " ") for value in unique(values) if slugify(value)
    ][:10]


def infer_visible_attributes(text):
    lower = text.lower()
    attributes = []
    for color in ["black", "white", "blue", "pink", "green", "silver"]:
        if color in lower:
            attributes.append(
                {"name": "color", **field(color.title(), "detected", "medium", True)}
            )
            break
    return attributes


def infer_attributes(text, category_path):
    attributes = {}
    if category_path:
        attributes["category_family"] = field(
            category_path.split(" > ")[0], "inferred", "medium", True
        )
    for attr in infer_visible_attributes(text):
        attributes[attr["name"]] = {
            key: value for key, value in attr.items() if key != "name"
        }
    return attributes


def detect_missing_fields(values):
    missing = []
    required = {
        "productName": "Add a product name for the upload template.",
        "description": "Generate or provide the product description required by the upload template.",
        "price": "Add seller-provided product price.",
        "stock": "Add seller-provided available stock for the upload template.",
        "weight": "Add product weight for the template logistics column.",
        "length": "Add product length in the dimensions field.",
        "width": "Add product width in the dimensions field.",
        "height": "Add product height in the dimensions field.",
    }
    for key, reason in required.items():
        if not values.get(key):
            missing.append(
                {
                    "field": key.replace("productName", "product_name"),
                    "importance": "required",
                    "reason": reason,
                }
            )
    recommended = {
        "marketplace_category": "Confirm the best marketplace category before upload when available.",
        "dimensions": "Exact dimensions are not visible from image.",
        "material": "Material should be confirmed by seller.",
        "weight": "Weight is useful for marketplace logistics.",
        "warranty": "Warranty should only be added if seller provides it.",
    }
    for key, reason in recommended.items():
        missing.append({"field": key, "importance": "recommended", "reason": reason})
    return missing


def calculate_readiness(values):
    score = 0
    if values.get("productName"):
        score += 20
    if values.get("description") and len(values["description"]) >= 80:
        score += 25
    if values.get("images_count", 0) > 0:
        score += 15
    if values.get("price"):
        score += 15
    if values.get("stock"):
        score += 15
    if values.get("weight"):
        score += 10
    if values.get("length") and values.get("width") and values.get("height"):
        score += 10
    if values.get("category_id"):
        score += 6
    if values.get("category_confirmed"):
        score += 4
    confirmed = len(values.get("confirmed_fields") or [])
    score += min(10, confirmed * 2)
    required_missing = [
        item
        for item in values.get("missing_fields", [])
        if item["importance"] == "required"
    ]
    status = (
        "Ready to Export"
        if not required_missing and values.get("images_count", 0) > 0
        else "Needs Review"
    )
    suggestions = [item["reason"] for item in values.get("missing_fields", [])[:5]]
    return {
        "score": min(100, score),
        "status": status,
        "suggestions": suggestions,
    }


def extract_shopee_template_fields(template_path=SHOPEE_TEMPLATE_PATH):
    rows = read_xlsx_sheet_rows(template_path, "Template", max_rows=6)
    if len(rows) < 5:
        return []
    keys = [split_template_key(value) for value in rows[0]]
    labels = rows[2]
    requirements = rows[3]
    notes = rows[4]
    fields = []
    for index, key in enumerate(keys):
        if not key:
            continue
        fields.append(
            {
                "key": key,
                "label": labels[index] if index < len(labels) else key,
                "requirement": requirements[index] if index < len(requirements) else "",
                "description": notes[index] if index < len(notes) else "",
                "column_index": index,
            }
        )
    return fields


def map_listing_to_template_row(export_payload):
    listing = export_payload.get("listing") or {}
    images = export_payload.get("images") or {}
    gallery_images = images.get("gallery_images") or []
    row = {field["key"]: "" for field in extract_shopee_template_fields()}
    logistics = export_payload.get("logistics") or listing.get("logistics") or {}
    row.update(
        {
            "ps_category": stringify_cell(listing.get("category_id")),
            "ps_product_name": listing.get("product_name") or "",
            "ps_product_description": listing.get("description") or "",
            "ps_price": stringify_cell(listing.get("price")),
            "ps_stock": stringify_cell(listing.get("stock")),
            "ps_item_cover_image": images.get("main_image") or "",
            "ps_weight": stringify_cell(
                logistics.get("weight") or listing.get("weight")
            ),
            "ps_length": stringify_cell(
                logistics.get("length") or listing.get("length")
            ),
            "ps_width": stringify_cell(logistics.get("width") or listing.get("width")),
            "ps_height": stringify_cell(
                logistics.get("height") or listing.get("height")
            ),
            "channel_id.1000": logistics.get("shipping_channel") or "On",
        }
    )
    for index, image in enumerate(gallery_images[:8], start=1):
        key = f"ps_item_image_{index}"
        if key in row:
            row[key] = image
    return row


def template_row_to_tsv(row):
    fields = extract_shopee_template_fields()
    headers = [field["label"] for field in fields]
    values = [row.get(field["key"], "") for field in fields]
    return "\t".join(headers) + "\n" + "\t".join(escape_tsv(value) for value in values)


def build_shopee_template_xlsx(export_payload, template_path=SHOPEE_TEMPLATE_PATH):
    row_values = map_listing_to_template_row(export_payload)
    fields = extract_shopee_template_fields(template_path)
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheet_path = get_xlsx_sheet_path(template_path, "Template")
    output = BytesIO()

    with ZipFile(template_path, "r") as source, ZipFile(
        output, "w", ZIP_DEFLATED
    ) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == sheet_path:
                data = write_template_row_xml(data, fields, row_values, ns)
            target.writestr(item, data)

    return output.getvalue()


def write_template_row_xml(sheet_xml, fields, row_values, ns):
    from xml.etree import ElementTree

    namespace = ns["a"]
    ElementTree.register_namespace("", namespace)
    root = ElementTree.fromstring(sheet_xml)
    sheet_data = root.find("a:sheetData", ns)
    if sheet_data is None:
        sheet_data = ElementTree.SubElement(root, f"{{{namespace}}}sheetData")

    for existing in list(sheet_data.findall("a:row", ns)):
        if existing.attrib.get("r") == "7":
            sheet_data.remove(existing)

    row = ElementTree.Element(f"{{{namespace}}}row", {"r": "7"})
    for field in fields:
        column_index = int(field["column_index"])
        reference = f"{column_letters(column_index + 1)}7"
        value = stringify_cell(row_values.get(field["key"], ""))
        cell = ElementTree.SubElement(
            row, f"{{{namespace}}}c", {"r": reference, "t": "inlineStr"}
        )
        inline = ElementTree.SubElement(cell, f"{{{namespace}}}is")
        text = ElementTree.SubElement(inline, f"{{{namespace}}}t")
        text.text = value

    inserted = False
    rows = list(sheet_data.findall("a:row", ns))
    for index, existing in enumerate(rows):
        existing_number = int(existing.attrib.get("r", "0") or 0)
        if existing_number > 7:
            sheet_data.insert(index, row)
            inserted = True
            break
    if not inserted:
        sheet_data.append(row)

    dimension = root.find("a:dimension", ns)
    if dimension is not None:
        last_column = column_letters(
            max((int(field["column_index"]) for field in fields), default=0) + 1
        )
        dimension.set("ref", f"A1:{last_column}7")

    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)


def get_xlsx_sheet_path(template_path, sheet_name):
    ns = {
        "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    with ZipFile(template_path) as archive:
        workbook = parse_xml(archive.read("xl/workbook.xml"))
        rels = parse_xml(archive.read("xl/_rels/workbook.xml.rels"))
        relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        for sheet in workbook.find("a:sheets", ns):
            if sheet.attrib.get("name") == sheet_name:
                target = relmap[
                    sheet.attrib[
                        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                    ]
                ]
                return (
                    "xl/" + target.lstrip("/")
                    if not target.startswith("xl/")
                    else target
                )
    raise ValueError(f"Sheet not found: {sheet_name}")


def column_letters(index):
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def read_xlsx_sheet_rows(template_path, sheet_name, max_rows=20):
    ns = {
        "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    with ZipFile(template_path) as archive:
        shared_strings = read_shared_strings(archive, ns)
        workbook = parse_xml(archive.read("xl/workbook.xml"))
        rels = parse_xml(archive.read("xl/_rels/workbook.xml.rels"))
        relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        target = None
        for sheet in workbook.find("a:sheets", ns):
            if sheet.attrib.get("name") == sheet_name:
                target = relmap[
                    sheet.attrib[
                        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                    ]
                ]
                break
        if not target:
            return []
        path = "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
        root = parse_xml(archive.read(path))
        output = []
        for row in root.findall("a:sheetData/a:row", ns)[:max_rows]:
            values = []
            cells = row.findall("a:c", ns)
            for cell in cells:
                column_index = cell_column_index(cell.attrib.get("r", "A1"))
                while len(values) < column_index:
                    values.append("")
                raw = cell.find("a:v", ns)
                value = ""
                if raw is not None:
                    value = raw.text or ""
                    if cell.attrib.get("t") == "s":
                        value = shared_strings[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(
                        node.text or ""
                        for node in cell.iter(
                            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
                        )
                    )
                values.append(value)
            output.append(values)
        return output


def read_shared_strings(archive, ns):
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = parse_xml(archive.read("xl/sharedStrings.xml"))
    strings = []
    for item in root.findall("a:si", ns):
        strings.append(
            "".join(
                node.text or ""
                for node in item.iter(
                    "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
                )
            )
        )
    return strings


def parse_xml(value):
    from xml.etree import ElementTree

    return ElementTree.fromstring(value)


def cell_column_index(ref):
    letters = "".join(char for char in ref if char.isalpha())
    index = 0
    for char in letters:
        index = index * 26 + (ord(char.upper()) - ord("A") + 1)
    return max(0, index - 1)


def split_template_key(value):
    return str(value).split("|", 1)[0].strip()


def stringify_cell(value):
    if value is None:
        return ""
    return str(value)


def escape_tsv(value):
    return (
        stringify_cell(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")
    )


def build_scene_plans(input_data):
    count = max(1, min(10, int(input_data.get("count") or 8)))
    geo = get_geo_preset(input_data.get("targetGeo"))
    product_name = clean(input_data.get("productName") or "Product")
    product_category = clean(input_data.get("category") or "general product")
    brand_tone = clean(input_data.get("brandTone") or "marketplace-ready")
    audience = clean(input_data.get("audience") or "online shoppers")
    background_prompt = clean(input_data.get("backgroundPrompt") or "")

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
                "backgroundPrompt": background_prompt,
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
    parts = [
        f"Create a square 1200x1200 product preview image for {plan['productName']}, a {plan['productCategory']}.",
        "Use the uploaded product photo as the source of truth and primary visual reference.",
        "Preserve the original product exactly as shown in the uploaded photo: keep the same shape, color, material, label, logo, text, packaging, proportions, and all visible details.",
        "Do not alter, replace, distort, redraw, redesign, or modify the original product photo.",
        "Important: do not change the original product photo; only improve the presentation around it.",
        "Do not invent new packaging, change branding, add fake logos, or turn the product into a different object.",
        "You may enhance image resolution and improve clarity of fine product details, but only in a faithful way that keeps the original product unchanged.",
        "Enhance sharpness, texture visibility, edges, and small product details while preserving the true appearance of the uploaded product.",
        "If the user does not provide background input, generate a few realistic, high-quality background options relevant to the product's use scenario, category, audience, and brand tone, then choose the most suitable one.",
        "Apply a realistic, high-quality background that feels natural, polished, and visually supportive of the product.",
        "Backgrounds should remain subtle, believable, and keep the product as the main focus.",
        "Only improve the presentation with cleaner lighting, higher apparent resolution, sharper edges, natural shadows, tidy composition, and a realistic premium background that fits the intended scene.",
        f"Scene type: {plan['category']} / {plan['sceneType']}. {plan['description']}.",
        f"Target market: {geo['market']}, {geo['region']}. Use {geo['aesthetic']}.",
        f"Seasonal and cultural filters: {', '.join(geo['seasonalMarkers'])}; {', '.join(geo['culturalMarkers'])}.",
        f"Brand tone: {plan['brandTone']}. Audience: {plan['audience']}.",
        f"Visual direction: hero product image, product remains the clear focal point, realistic lighting, clean composition, no fake branding, no unreadable text, and {geo['colorNotes']}.",
    ]
    if plan.get("backgroundPrompt"):
        parts.append(
            f"User-requested commercial background direction: {plan['backgroundPrompt']}. Apply it only to the scene/background; keep the product unchanged."
        )
    return " ".join(parts)


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
        "marketplaceDescription": f"{product_name} styled for {plan['geo']['market']} shoppers in a {plan['sceneType']} scene. Designed for {plan['brandTone']} brand positioning and fast marketplace listing creation.",
        "tiktokHashtags": [f"#{tag.replace('-', '')}" for tag in seo_tags[:6]],
        "platformTemplates": {
            "shopee": {
                "imageSize": plan["dimensions"]["shopee"],
                "usage": "Main listing image or variation gallery",
            },
            "lazada": {
                "imageSize": plan["dimensions"]["lazada"],
                "usage": "Product gallery image",
            },
            "tiktokShop": {
                "imageSize": plan["dimensions"]["tiktokShop"],
                "usage": "Product card, short-form commerce creative, or carousel",
            },
        },
    }


def build_generation_payload(input_data):
    plans = build_scene_plans(input_data)
    return {
        "plans": plans,
        "prompts": [
            {"id": plan["id"], "prompt": build_scene_prompt(plan)} for plan in plans
        ],
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
                "In this same edit, remove or replace the original background as needed and compose a clean commercial listing scene around the unchanged product.",
                "If the source photo has a messy, transparent, or plain background, treat it as background material only; keep product edges, labels, colors, and proportions faithful.",
                "Make it look like a polished marketplace product preview image while keeping the object recognizably identical to the original photo.",
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
    body = build_multipart_body(boundary, fields, images)
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
            message = (
                detail or f"OpenAI product preview edit failed with HTTP {exc.code}"
            )
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc

    b64 = (data.get("data") or [{}])[0].get("b64_json")
    if not b64:
        raise RuntimeError("OpenAI edit response did not include b64_json")
    return b64


def build_multipart_body(boundary, fields, images):
    chunks = []
    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8")
        )
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    image_list = images if isinstance(images, list) else [images]
    field_name = "image[]" if len(image_list) > 1 else "image"
    for image in image_list:
        extension = mimetypes.guess_extension(image["mimeType"]) or ".png"
        filename = f"{image['name']}{extension}"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode(
                "utf-8"
            )
        )
        chunks.append(f"Content-Type: {image['mimeType']}\r\n\r\n".encode("utf-8"))
        chunks.append(image["data"])
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)


def image_model(values=None):
    requested = (
        clean((values or {}).get("imageModel") or "")
        if isinstance(values, dict)
        else ""
    )
    if requested in IMAGE_MODEL_OPTIONS:
        return requested
    configured = os.environ.get("OPENAI_IMAGE_MODEL", DEFAULT_IMAGE_MODEL)
    return configured if configured in IMAGE_MODEL_OPTIONS else DEFAULT_IMAGE_MODEL


def text_model(values=None):
    requested = (
        clean((values or {}).get("textModel") or "") if isinstance(values, dict) else ""
    )
    if requested in TEXT_MODEL_OPTIONS:
        return requested
    configured = os.environ.get("OPENAI_TEXT_MODEL", DEFAULT_TEXT_MODEL)
    return configured if configured in TEXT_MODEL_OPTIONS else DEFAULT_TEXT_MODEL


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


def clean_seller_value(value):
    cleaned = clean(value)
    if re.search(r"missing\s+.*category", cleaned, flags=re.IGNORECASE):
        return ""
    return cleaned


def unique(values):
    seen = set()
    output = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output




class ConfigService:
    def load_env_file(self, env_path=ROOT / ".env", environ=os.environ):
        return load_env_file(env_path, environ)

    def image_model(self, values=None):
        return image_model(values)

    def text_model(self, values=None):
        return text_model(values)


class CategoryService:
    def default_categories(self):
        return default_categories()

    def public_categories(self):
        return public_categories()

    def suggest_category(self, text, categories=None):
        return suggest_category(text, categories)


class ListingDraftService:
    def generate(self, input_data):
        return generate_listing_draft(input_data)

    def create_openai_request(self, input_data, local_draft, model):
        return create_openai_listing_draft_request(input_data, local_draft, model)

    def apply_openai_copy(self, local_draft, ai_copy, model):
        return apply_openai_listing_copy(local_draft, ai_copy, model)


class TemplateExportService:
    def fields(self):
        return extract_shopee_template_fields()

    def map_row(self, export_payload):
        return map_listing_to_template_row(export_payload)

    def build_xlsx(self, export_payload):
        return build_shopee_template_xlsx(export_payload)


class SceneGenerationService:
    def build_payload(self, input_data):
        return build_generation_payload(input_data)

    def select_item(self, input_data):
        return select_generation_item(input_data)


class OpenAIService:
    def generate_image(self, prompt, api_key, model):
        return generate_openai_image(prompt, api_key, model)

    def remove_background(self, image, api_key, model):
        return remove_background_openai(image, api_key, model)

    def polish_product_preview(self, prompt, images, api_key, model):
        return polish_product_preview_openai(prompt, images, api_key, model)

    def generate_listing_copy(self, input_data, local_draft, api_key, model):
        return generate_openai_listing_draft(input_data, local_draft, api_key, model)


class MobileUploadService:
    def create_session(self, host, session_id=""):
        return create_mobile_upload_session(host, session_id)

    def add_uploads(self, session_id, images):
        return add_mobile_uploads(session_id, images)

    def list_uploads(self, session_id, after=""):
        images = MOBILE_UPLOAD_SESSIONS.get(session_id, [])
        if after:
            images = [image for image in images if image["id"] > after]
        return images


class ShopShotServices:
    def __init__(self):
        self.config = ConfigService()
        self.categories = CategoryService()
        self.listings = ListingDraftService()
        self.templates = TemplateExportService()
        self.scenes = SceneGenerationService()
        self.openai = OpenAIService()
        self.mobile_uploads = MobileUploadService()
