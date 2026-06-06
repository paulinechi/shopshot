#!/usr/bin/env python3
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import parse

from backend.services import *

SERVICES = ShopShotServices()


class ScenarioRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = parse.urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json(
                200,
                {
                    "ok": True,
                    "imageModel": SERVICES.config.image_model(),
                    "textModel": SERVICES.config.text_model(),
                    "imageModelOptions": IMAGE_MODEL_OPTIONS,
                    "textModelOptions": TEXT_MODEL_OPTIONS,
                    "openaiConfigured": bool(os.environ.get("OPENAI_API_KEY")),
                },
            )
            return
        if parsed.path == "/api/categories":
            self.send_json(200, {"categories": SERVICES.categories.public_categories()})
            return
        if parsed.path == "/api/template-fields":
            self.send_json(200, {"fields": SERVICES.templates.fields()})
            return
        if parsed.path == "/api/mobile-upload-url":
            query = parse.parse_qs(parsed.query)
            requested_host = (query.get("host") or [self.headers.get("Host", "")])[0]
            session_id = (query.get("session") or [""])[0]
            self.send_json(
                200,
                SERVICES.mobile_uploads.create_session(
                    requested_host, session_id=session_id
                ),
            )
            return
        if parsed.path == "/api/mobile-uploads":
            query = parse.parse_qs(parsed.query)
            session_id = (query.get("session") or [""])[0]
            after = (query.get("after") or [""])[0]
            images = SERVICES.mobile_uploads.list_uploads(session_id, after)
            self.send_json(200, {"session": session_id, "images": images})
            return
        if parsed.path == "/mobile-upload":
            self.serve_mobile_upload_page(parsed)
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
        if parsed.path == "/api/upload-imgur":
            self.handle_upload_imgur()
            return
        if parsed.path == "/api/map-template-row":
            self.handle_map_template_row()
            return
        if parsed.path == "/api/export-template-xlsx":
            self.handle_export_template_xlsx()
            return
        if parsed.path == "/api/mobile-uploads":
            self.handle_mobile_uploads()
            return
        if parsed.path not in (
            "/api/generate-scenes",
            "/api/generate-scene",
            "/api/remove-background",
            "/api/generate-listing-draft",
            "/api/upload-imgur",
            "/api/map-template-row",
            "/api/export-template-xlsx",
            "/api/mobile-uploads",
        ):
            self.send_json(404, {"error": "Not found"})
            return

    def handle_generate_scenes(self):
        try:
            body = self.read_json_body()
            payload = SERVICES.scenes.build_payload(body)
            selected_image_model = SERVICES.config.image_model(body)
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
                    image = SERVICES.openai.generate_image(
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
            item = SERVICES.scenes.select_item(body)
            selected_image_model = SERVICES.config.image_model(body)
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
                        b64 = SERVICES.openai.polish_product_preview(
                            item["prompt"],
                            uploaded_images,
                            api_key,
                            selected_image_model,
                        )
                    else:
                        b64 = SERVICES.openai.generate_image(
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
            selected_image_model = SERVICES.config.image_model(body)
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
                    b64 = SERVICES.openai.remove_background(
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
            selected_text_model = SERVICES.config.text_model(body)
            draft = SERVICES.listings.generate(body)
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                try:
                    ai_copy = SERVICES.openai.generate_listing_copy(
                        body, draft, api_key, selected_text_model
                    )
                    draft = SERVICES.listings.apply_openai_copy(
                        draft, ai_copy, selected_text_model
                    )
                    self.send_json(
                        200,
                        {"mode": "openai", "model": selected_text_model, **draft},
                    )
                    return
                except RuntimeError as exc:
                    draft["text_generation"] = {
                        "source": "fallback",
                        "model": selected_text_model,
                        "error": str(exc),
                    }
            self.send_json(
                200, {"mode": "fallback", "model": selected_text_model, **draft}
            )
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_upload_imgur(self):
        try:
            body = self.read_json_body(max_size=80_000_000)
            client_id = os.environ.get("IMGUR_CLIENT_ID", "")
            if not client_id:
                self.send_json(
                    200,
                    {
                        "mode": "fallback",
                        "reason": "IMGUR_CLIENT_ID is not configured",
                        "images": [],
                    },
                )
                return

            outputs = []
            for image in (body.get("images") or [])[:9]:
                try:
                    outputs.append(
                        {
                            "id": image.get("id") or "",
                            "name": image.get("name") or "product-preview.png",
                            "source": "imgur",
                            "url": upload_imgur_image(image, client_id),
                        }
                    )
                except RuntimeError as exc:
                    outputs.append(
                        {
                            "id": image.get("id") or "",
                            "name": image.get("name") or "product-preview.png",
                            "source": "fallback",
                            "error": str(exc),
                        }
                    )

            mode = (
                "imgur"
                if any(item["source"] == "imgur" for item in outputs)
                else "fallback"
            )
            self.send_json(200, {"mode": mode, "images": outputs})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_map_template_row(self):
        try:
            body = self.read_json_body(max_size=5_000_000)
            row = SERVICES.templates.map_row(body)
            self.send_json(
                200,
                {
                    "fields": SERVICES.templates.fields(),
                    "row": row,
                    "tsv": template_row_to_tsv(row),
                },
            )
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_export_template_xlsx(self):
        try:
            body = self.read_json_body(max_size=5_000_000)
            workbook = SERVICES.templates.build_xlsx(body)
            filename = f"{slugify(((body.get('listing') or {}).get('product_name') or 'product'))}-shopee-template.xlsx"
            self.send_binary(
                200,
                workbook,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename,
            )
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def handle_mobile_uploads(self):
        try:
            body = self.read_json_body(max_size=80_000_000)
            session_id = clean(body.get("session") or "")
            images = body.get("images") or []
            stored = SERVICES.mobile_uploads.add_uploads(session_id, images)
            self.send_json(200, {"ok": True, "count": len(stored)})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON body"})

    def serve_mobile_upload_page(self, parsed):
        query = parse.parse_qs(parsed.query)
        session_id = clean((query.get("session") or [""])[0])
        html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ShopShot Phone Upload</title>
    <style>
      body {{ margin: 0; padding: 28px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f7f8fc; color: #171d31; }}
      main {{ max-width: 520px; margin: 0 auto; display: grid; gap: 18px; }}
      h1 {{ margin: 0; font-size: 30px; }}
      p {{ margin: 0; color: #51607d; line-height: 1.5; }}
      label {{ display: grid; gap: 10px; padding: 22px; border: 1px dashed #cbd4ec; border-radius: 18px; background: #fff; font-weight: 800; }}
      input {{ font: inherit; }}
      button {{ min-height: 48px; border: 0; border-radius: 14px; background: #6467f2; color: #fff; font: inherit; font-weight: 850; }}
      output {{ min-height: 24px; color: #15be78; font-weight: 800; }}
    </style>
  </head>
  <body>
    <main>
      <h1>Upload product photos</h1>
      <p>Select or take product photos here. They will appear on the desktop Create Listing screen.</p>
      <label>
        Product photos
        <input id="photos" type="file" accept="image/*" multiple>
      </label>
      <button id="uploadButton" type="button">Send to desktop</button>
      <output id="status"></output>
    </main>
    <script>
      const session = {json.dumps(session_id)};
      const photos = document.querySelector("#photos");
      const status = document.querySelector("#status");
      document.querySelector("#uploadButton").addEventListener("click", async () => {{
        const files = [...photos.files].filter((file) => file.type.startsWith("image/"));
        if (!files.length) {{
          status.textContent = "Choose at least one image.";
          return;
        }}
        status.textContent = "Uploading...";
        const images = await Promise.all(files.map((file) => new Promise((resolve) => {{
          const reader = new FileReader();
          reader.onload = () => resolve({{ name: file.name, mimeType: file.type, b64: String(reader.result).split(",", 2)[1], uploadedAt: new Date().toISOString() }});
          reader.readAsDataURL(file);
        }})));
        const response = await fetch("/api/mobile-uploads", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ session, images }})
        }});
        status.textContent = response.ok ? `Sent ${{images.length}} photo${{images.length === 1 ? "" : "s"}}.` : "Upload failed.";
      }});
    </script>
  </body>
</html>"""
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

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


def main():
    SERVICES.config.load_env_file()
    port = int(os.environ.get("PORT", "3000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), ScenarioRequestHandler)
    print(f"Product scenario generator running at http://localhost:{port}")
    print(f"Phone upload URL base: http://{get_lan_ip()}:{port}")
    print(f"OpenAI image model: {SERVICES.config.image_model()}")
    server.serve_forever()


if __name__ == "__main__":
    main()
