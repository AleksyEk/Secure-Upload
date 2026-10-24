"""Usuwanie w obu wersjach, także po ręcznym skasowaniu pliku z dysku."""
from io import BytesIO
from pathlib import Path
import re
import tempfile
import unittest

from PIL import Image
from app import create_app


class DeleteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.client = create_app(self.root, {"TESTING": True}).test_client()

    def tearDown(self):
        self.temp.cleanup()

    def upload(self, version, name="test.png"):
        image = BytesIO()
        Image.new("RGB", (10, 10)).save(image, format="PNG")
        image.seek(0)
        response = self.client.post(f"/{version}/upload", data={"file": (image, name, "image/png")},
                                    headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def token(self, version):
        page = self.client.get(f"/{version}/").data
        return re.search(rb'name="delete_token" value="([^"]+)"', page).group(1).decode()

    def delete(self, version, record):
        return self.client.post(f"/{version}/delete/{record['id']}",
                                data={"delete_token": self.token(version)}, follow_redirects=True)

    def test_delete_removes_file_and_record_in_both_versions(self):
        for version in ["before", "after"]:
            with self.subTest(version=version):
                record = self.upload(version)
                file = self.root / version / "uploads" / record["stored_name"]
                response = self.delete(version, record)
                self.assertEqual(response.status_code, 200)
                self.assertIn("Plik został usunięty".encode(), response.data)
                self.assertFalse(file.exists())
                self.assertIn("Magazyn jest pusty".encode(), response.data)

    def test_delete_removes_stale_record(self):
        for version in ["before", "after"]:
            record = self.upload(version)
            (self.root / version / "uploads" / record["stored_name"]).unlink()
            response = self.delete(version, record)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Magazyn jest pusty".encode(), response.data)

    def test_delete_requires_post_and_valid_token(self):
        record = self.upload("after")
        url = f"/after/delete/{record['id']}"
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue((self.root / "after" / "uploads" / record["stored_name"]).exists())

    def test_delete_cannot_access_other_version(self):
        before = self.upload("before")
        after = self.upload("after")
        response = self.client.post(f"/after/delete/{before['id']}", data={"delete_token": self.token("after")})
        self.assertEqual(response.status_code, 404)
        self.assertTrue((self.root / "before" / "uploads" / before["stored_name"]).exists())
        self.assertTrue((self.root / "after" / "uploads" / after["stored_name"]).exists())

    def test_before_duplicate_keeps_file_until_last_record_deleted(self):
        first = self.upload("before")
        second = self.upload("before")
        file = self.root / "before" / "uploads" / first["stored_name"]
        self.delete("before", first)
        self.assertTrue(file.exists())
        self.delete("before", second)
        self.assertFalse(file.exists())

    def test_before_delete_never_removes_file_outside_uploads(self):
        record = self.upload("before", "../control.txt")
        fixture = self.root / "before" / "control.txt"
        content = fixture.read_bytes()
        response = self.delete("before", record)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fixture.read_bytes(), content)
        self.assertIn("Magazyn jest pusty".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
