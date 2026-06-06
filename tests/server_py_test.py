import os
import tempfile
import unittest

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
        self.assertIn("Shopee", body["prompt"])

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

    def test_suggest_category_uses_existing_category_id_only(self):
        suggestion = server.suggest_category("phone charger electronics", server.default_categories())

        self.assertIsNotNone(suggestion)
        self.assertIn("category_id", suggestion["value"])
        self.assertIn("Electronics", suggestion["value"]["category_path"])


if __name__ == "__main__":
    unittest.main()
