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


if __name__ == "__main__":
    unittest.main()
