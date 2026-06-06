import os
import tempfile
import unittest
from io import BytesIO

import server


class PythonBackendTest(unittest.TestCase):
    def test_load_env_file_preserves_existing_values_and_parses_quotes(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as env_file:
            env_file.write("OPENAI_API_KEY='from-file'\n")
            env_file.write("OPENAI_IMAGE_MODEL=gpt-image-1.5\n")
            env_path = env_file.name

        try:
            values = {"OPENAI_API_KEY": "already-set"}
            server.load_env_file(env_path, values)

            self.assertEqual(values["OPENAI_API_KEY"], "already-set")
            self.assertEqual(values["OPENAI_IMAGE_MODEL"], "gpt-image-1.5")
        finally:
            os.unlink(env_path)

    def test_build_generation_payload_returns_fallback_metadata_shape(self):
        payload = server.build_generation_payload(
            {
                "productName": "Glow Ritual Set",
                "category": "beauty gift set",
                "brandTone": "premium warm",
                "audience": "urban shoppers",
                "targetGeo": "SG",
                "count": 1,
            }
        )

        self.assertEqual(len(payload["plans"]), 1)
        self.assertEqual(payload["plans"][0]["geo"]["market"], "Singapore")
        self.assertIn("Singapore", payload["prompts"][0]["prompt"])
        self.assertEqual(payload["metadata"][0]["sceneType"], "home")
        self.assertIn("shopee", payload["metadata"][0]["platformTemplates"])

    def test_build_generation_payload_includes_background_prompt(self):
        payload = server.build_generation_payload(
            {
                "productName": "Glow Ritual Set",
                "category": "skincare",
                "backgroundPrompt": "premium bathroom shelf with soft daylight",
                "count": 1,
            }
        )

        self.assertIn("premium bathroom shelf", payload["prompts"][0]["prompt"])
        self.assertIn("keep the product unchanged", payload["prompts"][0]["prompt"])

    def test_model_selection_accepts_known_options_and_falls_back(self):
        self.assertEqual(server.image_model({"imageModel": "gpt-image-2"}), "gpt-image-2")
        self.assertEqual(server.text_model({"textModel": "gpt-5.4-mini"}), "gpt-5.4-mini")
        self.assertEqual(server.image_model({"imageModel": "not-real"}), server.DEFAULT_IMAGE_MODEL)

    def test_create_openai_image_request_uses_latest_model_defaults(self):
        body = server.create_openai_image_request("Make a product scene", "gpt-image-1.5")

        self.assertEqual(body["model"], "gpt-image-1.5")
        self.assertEqual(body["prompt"], "Make a product scene")
        self.assertEqual(body["size"], "1024x1024")
        self.assertEqual(body["quality"], "medium")
        self.assertEqual(body["n"], 1)

    def test_create_openai_product_preview_request_preserves_uploaded_object(self):
        body = server.create_openai_product_preview_request("Polish this listing", "gpt-image-1.5")

        self.assertEqual(body["model"], "gpt-image-1.5")
        self.assertEqual(body["quality"], "medium")
        self.assertIn("preserve the exact uploaded product", body["prompt"])
        self.assertIn("Do not redesign", body["prompt"])
        self.assertIn("marketplace", body["prompt"])

    def test_multipart_body_uses_image_array_fields_for_multiple_references(self):
        body = server.build_multipart_body(
            "boundary",
            {"model": "gpt-image-1.5", "prompt": "Polish previews"},
            [
                {"name": "front", "mimeType": "image/png", "data": b"front"},
                {"name": "side", "mimeType": "image/png", "data": b"side"},
            ],
        )

        text = body.decode("latin1")
        self.assertEqual(text.count('name="image[]"'), 2)
        self.assertIn('filename="front.png"', text)
        self.assertIn('filename="side.png"', text)

    def test_select_generation_item_returns_single_plan_for_progressive_generation(self):
        item = server.select_generation_item(
            {
                "productName": "Glow Ritual Set",
                "category": "beauty gift set",
                "targetGeo": "SG",
                "count": 4,
                "planId": "02-summer",
            }
        )

        self.assertEqual(item["plan"]["id"], "02-summer")
        self.assertEqual(item["metadata"]["id"], "02-summer")
        self.assertIn("Singapore", item["prompt"])

    def test_create_openai_background_removal_request_uses_transparent_edit(self):
        body = server.create_openai_background_removal_request("gpt-image-1.5")

        self.assertEqual(body["model"], "gpt-image-1.5")
        self.assertEqual(body["background"], "transparent")
        self.assertEqual(body["quality"], "medium")
        self.assertIn("transparent background", body["prompt"])

    def test_normalize_uploaded_image_rejects_non_image_payloads(self):
        with self.assertRaises(ValueError):
            server.normalize_uploaded_image({"name": "notes.txt", "mimeType": "text/plain", "b64": "abc"})

    def test_build_category_paths_reconstructs_shopee_tree(self):
        categories = server.build_category_paths([
            {"category_id": 10, "parent_category_id": 0, "original_category_name": "Health & Beauty", "has_children": True},
            {"category_id": 11, "parent_category_id": 10, "original_category_name": "Skincare", "has_children": False},
            {"category_id": 20, "parent_category_id": 0, "original_category_name": "Electronics & Gadgets", "has_children": True},
            {"category_id": 21, "parent_category_id": 20, "original_category_name": "Mobile Accessories", "has_children": False},
        ])

        self.assertEqual(categories[11]["display_path"], "Health & Beauty > Skincare")
        self.assertEqual(categories[21]["display_path"], "Electronics & Gadgets > Mobile Accessories")
        self.assertFalse(categories[11]["has_children"])

    def test_generate_listing_draft_requires_price_stock_and_omits_sku(self):
        draft = server.generate_listing_draft({
            "productName": "Glow Ritual Set",
            "categoryHint": "skincare",
            "brand": "Glow Co",
            "price": "24.90",
            "stock": "12",
            "weight": "0.5",
            "dimensions": "20 x 10 x 5",
            "targetGeo": "SG",
            "imagesCount": 1,
            "categoryConfirmed": True,
        })

        self.assertEqual(draft["listing_draft"]["price"]["value"], "24.90")
        self.assertEqual(draft["listing_draft"]["stock"]["value"], "12")
        self.assertNotIn("sku", draft["listing_draft"])
        self.assertNotIn("sku", draft["missing_fields"])
        self.assertGreaterEqual(draft["readiness"]["score"], 70)

    def test_generate_listing_draft_flags_missing_required_price_and_stock(self):
        draft = server.generate_listing_draft({
            "productName": "USB-C Cable",
            "categoryHint": "electronics",
            "targetGeo": "SG",
        })

        missing = {item["field"] for item in draft["missing_fields"]}
        self.assertIn("price", missing)
        self.assertIn("stock", missing)
        self.assertEqual(draft["readiness"]["status"], "Needs Review")

    def test_generate_listing_draft_uses_xlsx_template_requirements_for_readiness(self):
        draft = server.generate_listing_draft({
            "productName": "USB-C Cable",
            "categoryHint": "electronics",
            "price": "9.90",
            "stock": "20",
            "weight": "0.2",
            "dimensions": "18 x 7 x 2",
            "targetGeo": "SG",
            "imagesCount": 1,
        })

        required_missing = {item["field"] for item in draft["missing_fields"] if item["importance"] == "required"}
        self.assertNotIn("category", required_missing)
        self.assertEqual(draft["readiness"]["status"], "Ready to Export")

    def test_generate_listing_draft_flags_xlsx_logistics_columns(self):
        draft = server.generate_listing_draft({
            "productName": "USB-C Cable",
            "categoryHint": "electronics",
            "price": "9.90",
            "stock": "20",
            "targetGeo": "SG",
            "imagesCount": 1,
        })

        required_missing = {item["field"] for item in draft["missing_fields"] if item["importance"] == "required"}
        self.assertIn("weight", required_missing)
        self.assertIn("length", required_missing)
        self.assertEqual(draft["readiness"]["status"], "Needs Review")

    def test_suggest_category_uses_existing_category_id_only(self):
        suggestion = server.suggest_category("phone charger electronics", server.default_categories())

        self.assertIsNotNone(suggestion)
        self.assertIn("category_id", suggestion["value"])
        self.assertIn("Electronics", suggestion["value"]["category_path"])

    def test_extract_shopee_template_categories_reads_upload_sample(self):
        categories = server.extract_shopee_template_categories()
        category_ids = {category["category_id"] for category in categories}

        self.assertIn(120039, category_ids)
        self.assertTrue(any("Template category 120039" in category["display_path"] for category in categories))

    def test_extract_shopee_template_fields_reads_basic_template(self):
        fields = server.extract_shopee_template_fields()
        keys = [field["key"] for field in fields]
        labels = {field["key"]: field["label"] for field in fields}
        requirements = {field["key"]: field["requirement"] for field in fields}

        self.assertIn("ps_category", keys)
        self.assertIn("ps_product_name", keys)
        self.assertIn("ps_product_description", keys)
        self.assertIn("ps_price", keys)
        self.assertIn("ps_stock", keys)
        self.assertEqual(labels["ps_category"], "Category")
        self.assertEqual(requirements["ps_product_name"], "Mandatory")

    def test_map_listing_to_template_row_uses_required_shopee_fields(self):
        row = server.map_listing_to_template_row({
            "listing": {
                "product_name": "USB-C Cable | Electronics Accessory | SG Ready",
                "category_id": 100001,
                "description": "A durable USB-C cable prepared for listing review.",
                "price": "9.90",
                "stock": "20",
            },
            "logistics": {
                "weight": "0.2",
                "length": "18",
                "width": "7",
                "height": "2",
            },
            "images": {
                "main_image": "https://example.com/cover.png",
                "gallery_images": ["https://example.com/1.png"],
            },
        })

        self.assertEqual(row["ps_category"], "100001")
        self.assertEqual(row["ps_product_name"], "USB-C Cable | Electronics Accessory | SG Ready")
        self.assertEqual(row["ps_price"], "9.90")
        self.assertEqual(row["ps_stock"], "20")
        self.assertEqual(row["ps_weight"], "0.2")
        self.assertEqual(row["ps_length"], "18")
        self.assertEqual(row["channel_id.1000"], "On")
        self.assertEqual(row["ps_item_cover_image"], "https://example.com/cover.png")

    def test_build_shopee_template_xlsx_fills_template_row(self):
        workbook = server.build_shopee_template_xlsx({
            "listing": {
                "product_name": "USB-C Cable | Electronics Accessory | SG Ready",
                "category_id": 100001,
                "description": "A durable USB-C cable prepared for listing review.",
                "price": "9.90",
                "stock": "20",
            },
            "logistics": {
                "weight": "0.2",
                "length": "18",
                "width": "7",
                "height": "2",
            },
            "images": {
                "main_image": "https://example.com/cover.png",
                "gallery_images": ["https://example.com/1.png"],
            },
        })

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as output:
            output.write(workbook)
            output_path = output.name

        try:
            rows = server.read_xlsx_sheet_rows(output_path, "Template", max_rows=8)
            template_row = rows[6]

            self.assertEqual(template_row[0], "100001")
            self.assertEqual(template_row[1], "USB-C Cable | Electronics Accessory | SG Ready")
            self.assertEqual(template_row[10], "9.90")
            self.assertEqual(template_row[11], "20")
            self.assertEqual(template_row[25], "0.2")
            self.assertEqual(template_row[29], "On")
        finally:
            os.unlink(output_path)

    def test_upload_imgur_image_returns_direct_link(self):
        requests = []

        class FakeResponse:
            def __enter__(self):
                return BytesIO(b'{"success": true, "data": {"link": "https://i.imgur.com/demo.png"}}')

            def __exit__(self, exc_type, exc, traceback):
                return False

        def fake_urlopen(req, timeout=0):
            requests.append(req)
            return FakeResponse()

        link = server.upload_imgur_image(
            {
                "name": "cover.png",
                "b64": "abc123",
                "mimeType": "image/png",
            },
            "client-id-123",
            opener=fake_urlopen,
        )

        self.assertEqual(link, "https://i.imgur.com/demo.png")
        self.assertEqual(requests[0].headers["Authorization"], "Client-ID client-id-123")
        self.assertIn(b"image=abc123", requests[0].data)

    def test_upload_imgur_image_rejects_missing_client_id(self):
        with self.assertRaises(RuntimeError):
            server.upload_imgur_image({"name": "cover.png", "b64": "abc123"}, "")


if __name__ == "__main__":
    unittest.main()
