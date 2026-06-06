#!/usr/bin/env python3
import base64
import json
import mimetypes
import os
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib import error, parse, request
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
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
        categories.setdefault(category["category_id"], category)
    return categories


def extract_shopee_template_categories(template_path=SHOPEE_TEMPLATE_PATH):
    rows = read_xlsx_sheet_rows(template_path, "Upload sample", max_rows=200)
    if not rows:
        return []
    headers = [split_template_key(value) for value in rows[0]]
    try:
        category_index = headers.index("ps_category")
        name_index = headers.index("ps_product_name")
    except ValueError:
        return []

    categories = {}
    for row in rows[6:]:
        if category_index >= len(row):
            continue
        raw_id = clean(row[category_index])
        if not raw_id.isdigit():
            continue
        category_id = int(raw_id)
        product_name = clean(row[name_index]) if name_index < len(row) else ""
        categories[category_id] = {
            "category_id": category_id,
            "parent_category_id": 0,
            "original_category_name": f"Template category {category_id}",
            "display_path": f"Template category {category_id}{f' · sample: {product_name}' if product_name else ''}",
            "has_children": False,
            "source": "xlsx",
        }
    return sorted(categories.values(), key=lambda item: item["display_path"])


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
    price = clean(input_data.get("price") or "")
    stock = clean(input_data.get("stock") or "")
    weight = clean(input_data.get("weight") or "")
    dimensions = clean(input_data.get("dimensions") or "")
    dimension_parts = parse_dimensions(dimensions)
    target_geo = clean(input_data.get("targetGeo") or "SG")
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
        product_name, product_note, category_value.get("category_path", "")
    )
    description = build_description(product_name, highlights, brand)
    title = build_listing_title(product_name, product_type, target_geo)
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
    numbers = re.findall(r"\d+(?:\.\d+)?", str(value or ""))
    keys = ("length", "width", "height")
    return {
        key: numbers[index] if index < len(numbers) else ""
        for index, key in enumerate(keys)
    }


def build_listing_title(product_name, product_type, target_geo):
    suffix = "SG Ready" if target_geo == "SG" else "Marketplace Ready"
    return f"{product_name} | {product_type} | {suffix}"


def build_highlights(product_name, product_note, category_path):
    highlights = [f"Polished marketplace-ready listing for {product_name}"]
    if product_note:
        highlights.append(f"Seller-provided note: {product_note}")
    if category_path:
        highlights.append(f"Suggested category: {category_path}")
    highlights.append("Review all generated details before export")
    return highlights[:5]


def build_description(product_name, highlights, brand):
    brand_line = f" from {brand}" if brand else ""
    bullet_text = "\n".join(f"- {item}" for item in highlights)
    return f"{product_name}{brand_line} prepared for listing review.\n\nHighlights:\n{bullet_text}\n\nPlease confirm price, stock, category, and product details before publishing."


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
            "If the user provides background input, use that background direction.",
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


class ScenarioRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = parse.urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json(
                200,
                {
                    "ok": True,
                    "imageModel": image_model(),
                    "textModel": text_model(),
                    "imageModelOptions": IMAGE_MODEL_OPTIONS,
                    "textModelOptions": TEXT_MODEL_OPTIONS,
                    "openaiConfigured": bool(os.environ.get("OPENAI_API_KEY")),
                },
            )
            return
        if parsed.path == "/api/categories":
            self.send_json(200, {"categories": public_categories()})
            return
        if parsed.path == "/api/template-fields":
            self.send_json(200, {"fields": extract_shopee_template_fields()})
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
        if parsed.path == "/api/generate-listing-draft":
            self.handle_generate_listing_draft()
            return
        if parsed.path == "/api/map-template-row":
            self.handle_map_template_row()
            return
        if parsed.path == "/api/export-template-xlsx":
            self.handle_export_template_xlsx()
            return
        if parsed.path not in (
            "/api/generate-scenes",
            "/api/generate-scene",
            "/api/remove-background",
            "/api/generate-listing-draft",
            "/api/map-template-row",
            "/api/export-template-xlsx",
        ):
            self.send_json(404, {"error": "Not found"})
            return

    def handle_generate_scenes(self):
        try:
            body = self.read_json_body()
            payload = build_generation_payload(body)
            selected_image_model = image_model(body)
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self.send_json(
                    200,
                    {
                        "mode": "fallback",
                        "reason": "OPENAI_API_KEY is not configured",
                        **payload,
                        "images": [],
                    },
                )
                return

            images = []
            prompts_by_id = {item["id"]: item["prompt"] for item in payload["prompts"]}
            for plan in payload["plans"]:
                try:
                    image = generate_openai_image(
                        prompts_by_id[plan["id"]], api_key, selected_image_model
                    )
                    images.append(
                        {
                            "id": plan["id"],
                            "source": "openai",
                            "model": selected_image_model,
                            "mimeType": "image/png",
                            "b64": image,
                        }
                    )
                except RuntimeError as exc:
                    images.append(
                        {"id": plan["id"], "source": "fallback", "error": str(exc)}
                    )

            mode = (
                "openai"
                if any(image["source"] == "openai" for image in images)
                else "fallback"
            )
            self.send_json(
                200,
                {
                    "mode": mode,
                    "model": selected_image_model,
                    **payload,
                    "images": images,
                },
            )
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_generate_scene(self):
        try:
            body = self.read_json_body(max_size=80_000_000)
            item = select_generation_item(body)
            selected_image_model = image_model(body)
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
                        b64 = polish_product_preview_openai(
                            item["prompt"],
                            uploaded_images,
                            api_key,
                            selected_image_model,
                        )
                    else:
                        b64 = generate_openai_image(
                            item["prompt"], api_key, selected_image_model
                        )
                    image = {
                        "id": item["plan"]["id"],
                        "source": "openai",
                        "model": selected_image_model,
                        "mimeType": "image/png",
                        "b64": b64,
                        "method": "edit" if uploaded_images else "generation",
                    }
                except RuntimeError as exc:
                    image = {
                        "id": item["plan"]["id"],
                        "source": "fallback",
                        "error": str(exc),
                    }
            else:
                image = {
                    "id": item["plan"]["id"],
                    "source": "fallback",
                    "error": "OPENAI_API_KEY is not configured",
                }
            mode = "openai" if image["source"] == "openai" else "fallback"
            self.send_json(
                200,
                {"mode": mode, "model": selected_image_model, **item, "image": image},
            )
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_remove_background(self):
        try:
            body = self.read_json_body(max_size=80_000_000)
            images = body.get("images") or []
            selected_image_model = image_model(body)
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self.send_json(
                    200,
                    {
                        "mode": "fallback",
                        "reason": "OPENAI_API_KEY is not configured",
                        "images": [],
                    },
                )
                return

            outputs = []
            for image in images[:4]:
                try:
                    normalized = normalize_uploaded_image(image)
                    b64 = remove_background_openai(
                        normalized, api_key, selected_image_model
                    )
                    outputs.append(
                        {
                            "name": image.get("name") or normalized["name"],
                            "source": "openai",
                            "mimeType": "image/png",
                            "b64": b64,
                        }
                    )
                except (RuntimeError, ValueError) as exc:
                    outputs.append(
                        {
                            "name": image.get("name") or "image",
                            "source": "fallback",
                            "error": str(exc),
                        }
                    )

            mode = (
                "openai"
                if any(item["source"] == "openai" for item in outputs)
                else "fallback"
            )
            self.send_json(
                200, {"mode": mode, "model": selected_image_model, "images": outputs}
            )
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_generate_listing_draft(self):
        try:
            body = self.read_json_body(max_size=80_000_000)
            draft = generate_listing_draft(body)
            self.send_json(
                200, {"mode": "fallback", "model": text_model(body), **draft}
            )
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_map_template_row(self):
        try:
            body = self.read_json_body(max_size=5_000_000)
            row = map_listing_to_template_row(body)
            self.send_json(
                200,
                {
                    "fields": extract_shopee_template_fields(),
                    "row": row,
                    "tsv": template_row_to_tsv(row),
                },
            )
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_export_template_xlsx(self):
        try:
            body = self.read_json_body(max_size=5_000_000)
            workbook = build_shopee_template_xlsx(body)
            filename = f"{slugify(((body.get('listing') or {}).get('product_name') or 'product'))}-shopee-template.xlsx"
            self.send_binary(
                200,
                workbook,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename,
            )
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def serve_static(self, raw_path, head_only=False):
        base_dir = SRC_DIR if raw_path.startswith("/src/") else PUBLIC_DIR
        relative = (
            raw_path[len("/src/") :]
            if raw_path.startswith("/src/")
            else raw_path.lstrip("/")
        )
        relative = "index.html" if relative in ("", "/") else relative
        file_path = (base_dir / parse.unquote(relative)).resolve()

        if not str(file_path).startswith(str(base_dir.resolve())):
            self.send_json(403, {"error": "Forbidden"})
            return
        if not file_path.exists() or not file_path.is_file():
            self.send_json(404, {"error": "Not found"})
            return

        content_type = (
            mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        )
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

    def send_binary(self, status_code, payload, content_type, filename):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        return


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
