"""Weryfikacja podstawowego przepływu. Testy bezpieczeństwa powstaną w kolejnym etapie."""
from io import BytesIO
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from app import create_app, create_version_app


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_version_app("secure", self.temp.name, {"TESTING": True})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_page_and_stylesheet(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Magazyn jest pusty".encode(), page.data)
        with self.client.get("/static/style.css") as css:
            self.assertEqual(css.status_code, 200)

    def test_png_and_jpeg_roundtrip(self):
        for fmt, suffix, mime in [("PNG", "png", "image/png"), ("JPEG", "jpg", "image/jpeg")]:
            with self.subTest(fmt=fmt):
                image = BytesIO()
                Image.new("RGB", (32, 32), "#183e62").save(image, format=fmt)
                content = image.getvalue()
                response = self.client.post("/upload", data={"file": (BytesIO(content), f"test.{suffix}", mime)},
                                            headers={"Accept": "application/json"})
                self.assertEqual(response.status_code, 201)
                record = response.get_json()
                self.assertTrue((Path(self.temp.name) / "uploads" / record["stored_name"]).is_file())
                with self.client.get("/download", query_string={"id": record["id"]}) as download:
                    self.assertEqual(download.status_code, 200)
                    self.assertEqual(download.data, content)
                    self.assertIn("attachment", download.headers["Content-Disposition"])
                self.assertIn(f"test.{suffix}".encode(), self.client.get("/").data)

    def test_browser_form_redirects_to_list(self):
        image = BytesIO()
        Image.new("RGB", (10, 10)).save(image, format="PNG")
        image.seek(0)
        response = self.client.post("/upload", data={"file": (image, "formularz.png", "image/png")}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Plik został zapisany".encode(), response.data)
        self.assertIn(b"formularz.png", response.data)

    def test_records_survive_application_restart(self):
        image = BytesIO()
        Image.new("RGB", (10, 10)).save(image, format="PNG")
        image.seek(0)
        self.client.post("/upload", data={"file": (image, "trwaly.png", "image/png")})
        restarted = create_version_app("secure", self.temp.name, {"TESTING": True}).test_client()
        self.assertIn(b"trwaly.png", restarted.get("/").data)


class ApplicationNavigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.client = create_app(self.temp.name, {"TESTING": True}).test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_selection_and_both_pages(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'href="/before/"', page.data)
        self.assertIn(b'href="/after/"', page.data)
        for version in ["before", "after"]:
            with self.subTest(version=version):
                page = self.client.get(f"/{version}/")
                self.assertEqual(page.status_code, 200)
                self.assertIn(f'action="/{version}/upload"'.encode(), page.data)
                self.assertIn(f'href="/{version}/static/style.css"'.encode(), page.data)
                self.assertIn(f"Wersja aplikacji: {version.upper()}".encode(), page.data)
                self.assertIn(b'href="/"', page.data)
                with self.client.get(f"/{version}/static/style.css") as css:
                    self.assertEqual(css.status_code, 200)

    def test_upload_download_and_separate_storage(self):
        image = BytesIO()
        Image.new("RGB", (16, 16), "blue").save(image, format="PNG")
        content = image.getvalue()
        for version in ["before", "after"]:
            response = self.client.post(f"/{version}/upload",
                data={"file": (BytesIO(content), f"{version}.png", "image/png")},
                headers={"Accept": "application/json"})
            self.assertEqual(response.status_code, 201)
            record = response.get_json()
            self.assertTrue((Path(self.temp.name) / version / "uploads" / record["stored_name"]).exists())
            query = {"id": record["id"]} if version == "after" else {"name": record["stored_name"]}
            with self.client.get(f"/{version}/download", query_string=query) as download:
                self.assertEqual(download.status_code, 200)
                self.assertEqual(download.data, content)
        before = self.client.get("/before/").data
        after = self.client.get("/after/").data
        self.assertIn(b"before.png", before)
        self.assertNotIn(b"after.png", before)
        self.assertIn(b"after.png", after)
        self.assertNotIn(b"before.png", after)

    def test_versions_keep_different_validation(self):
        for version, expected in [("before", 201), ("after", 400)]:
            response = self.client.post(f"/{version}/upload",
                data={"file": (BytesIO(b"Bezpieczny tekst testowy"), "tekst.png", "image/png")},
                headers={"Accept": "application/json"})
            self.assertEqual(response.status_code, expected)
        # Wizyta w BEFORE nie zmienia walidacji AFTER.
        self.client.get("/before/")
        self.assertEqual(self.client.get("/after/health").get_json()["mode"], "secure")

    def test_form_redirect_remains_in_selected_version(self):
        image = BytesIO()
        Image.new("RGB", (10, 10)).save(image, format="PNG")
        content = image.getvalue()
        for version in ["before", "after"]:
            response = self.client.post(f"/{version}/upload",
                data={"file": (BytesIO(content), "formularz.png", "image/png")})
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["Location"], f"/{version}/?uploaded=1")
            page = self.client.get(response.headers["Location"])
            self.assertIn("Plik został zapisany".encode(), page.data)


if __name__ == "__main__":
    unittest.main()
