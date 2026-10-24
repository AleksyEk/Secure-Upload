"""Lokalne laboratorium Secure Upload. BEFORE nigdy nie jest wersją produkcyjną."""
import argparse
import os
import secrets
import sqlite3
import warnings
from io import BytesIO
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from PIL import Image, UnidentifiedImageError

# Walidacja wersji AFTER
ALLOWED = {".png": ("PNG", "image/png"), ".jpg": ("JPEG", "image/jpeg"),
           ".jpeg": ("JPEG", "image/jpeg")}


class UploadError(Exception):
    def __init__(self, message, code, status=400):
        super().__init__(message)
        self.code, self.status = code, status


def validate_upload(file, config):
    name = file.filename
    if len(name) > 200 or any(c in name for c in '/\\:') or any(ord(c) < 32 for c in name):
        raise UploadError("Nazwa zawiera ścieżkę lub niedozwolone znaki.", "filename")
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED:
        raise UploadError("Dozwolone rozszerzenia: PNG, JPG i JPEG.", "extension")
    expected_format, expected_mime = ALLOWED[suffix]
    if file.mimetype != expected_mime:
        raise UploadError("Deklarowany MIME nie odpowiada rozszerzeniu.", "mime")
    content = file.stream.read(config["MAX_FILE_BYTES"] + 1)
    if len(content) > config["MAX_FILE_BYTES"]:
        limit_mb = f"{config['MAX_FILE_BYTES'] / 1_000_000:.2f}".replace(".", ",")
        raise UploadError(f"Plik przekracza maksymalny rozmiar {limit_mb} MB.", "file_size", 413)
    if not content:
        raise UploadError("Plik jest pusty.", "empty")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                if image.format != expected_format:
                    raise UploadError("Zawartość nie odpowiada rozszerzeniu i MIME.", "content_type")
                if image.width * image.height > config["MAX_PIXELS"]:
                    raise UploadError("Obraz ma zbyt wiele pikseli.", "pixels")
                image.verify()
            with Image.open(BytesIO(content)) as image:
                image.load()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError,
            Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise UploadError("Zawartość nie jest poprawnym obrazem PNG/JPEG.", "invalid_image") from exc
    # Nie skanujemy malware i nie usuwamy metadanych. Zachowujemy bajty oryginału.
    return content, ".png" if expected_format == "PNG" else ".jpg", expected_mime


# Granica bezpiecznego laboratorium dla wersji BEFORE
def laboratory_path(uploads, client_name, laboratory_root):
    target = (uploads / client_name.replace("\\", "/")).resolve()
    if not target.is_relative_to(Path(laboratory_root).resolve()):
        raise ValueError("Poza granicą laboratorium")
    # Metadane nie są celem demonstracji; chronimy bazę przed przypadkowym uszkodzeniem.
    if target.name.startswith("files.sqlite3"):
        raise ValueError("Chroniony plik laboratorium")
    return target


def create_version_app(mode="secure", data_dir=None, test_config=None):
    if mode not in {"secure", "vulnerable"}:
        raise ValueError("Tryb musi być secure albo vulnerable")
    app = Flask(__name__)
    folder = "after" if mode == "secure" else "before"
    default_dir = Path(__file__).resolve().parent / "dane" / folder
    root = Path(data_dir or default_dir).resolve()
    app.config.update(MODE=mode, DATA_DIR=root, MAX_FILE_BYTES=5 * 1024 * 1024,
                      MAX_FILES=20, MAX_PIXELS=20_000_000,
                      MAX_CONTENT_LENGTH=(6 if mode == "secure" else 16) * 1024 * 1024,
                      MAX_FORM_PARTS=10)
    if test_config:
        app.config.update(test_config)
    root.mkdir(parents=True, exist_ok=True)
    uploads = root / "uploads"
    uploads.mkdir(exist_ok=True)
    fixture = root / "control.txt"
    if not fixture.exists():
        fixture.write_text("PLIK KONTROLNY: poza magazynem uploadu. Bezpieczny dowód laboratoryjny.\n", encoding="utf-8")
    database = root / "files.sqlite3"
    delete_token = secrets.token_urlsafe(32)

    @contextmanager
    def connect():
        conn = sqlite3.connect(database, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY, original_name TEXT NOT NULL, stored_name TEXT NOT NULL,
            mime TEXT NOT NULL, size INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

    def rows():
        with connect() as db:
            return db.execute("SELECT * FROM files ORDER BY created_at DESC, rowid DESC").fetchall()

    def result(message, status, code, **extra):
        app.logger.warning("mode=%s event=%s status=%s", mode, code, status)
        if request.accept_mimetypes.best == "application/json":
            return jsonify(message=message, code=code, **extra), status
        if status < 400:
            if code == "deleted":
                return redirect(url_for("index", deleted="1"), code=303)
            return redirect(url_for("index", uploaded="1"), code=303)
        return render_template("index.html", files=rows(), error=message), status

    @app.context_processor
    def settings():
        return {"mode": mode, "delete_token": delete_token, "max_files": app.config["MAX_FILES"],
                "max_mib": app.config["MAX_FILE_BYTES"] // (1024 * 1024)}

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(HTTPException)
    def http_error(exc):
        if exc.code == 413:
            request_limit = f"{app.config['MAX_CONTENT_LENGTH'] / 1_000_000:.2f}".replace(".", ",")
            message = f"Przekroczono maksymalny rozmiar całego żądania: {request_limit} MB."
            if mode == "secure":
                file_limit = f"{app.config['MAX_FILE_BYTES'] / 1_000_000:.2f}".replace(".", ",")
                message += f" Maksymalny rozmiar pojedynczego pliku to {file_limit} MB."
        else:
            message = "Nie znaleziono zasobu lub żądanie jest niepoprawne."
        return result(message, exc.code, f"http_{exc.code}")

    @app.get("/")
    def index():
        return render_template("index.html", files=rows(), uploaded=request.args.get("uploaded") == "1",
                               deleted=request.args.get("deleted") == "1")

    @app.get("/health")
    def health():
        return jsonify(status="ok", mode=mode)

    @app.post("/upload")
    def upload():
        incoming = request.files.getlist("file")
        if len(incoming) != 1 or not incoming[0].filename:
            return result("Wybierz dokładnie jeden plik.", 400, "missing_file")
        file = incoming[0]
        file_id = secrets.token_hex(16)
        try:
            if mode == "secure":
                content, suffix, mime = validate_upload(file, app.config)
                stored_name = file_id + suffix
                target = uploads / stored_name
            else:
                # Celowe błędy BEFORE: zaufanie nazwie i MIME, brak limitu pliku/liczby.
                content = file.read()
                stored_name = file.filename
                mime = file.mimetype or "application/octet-stream"
                target = laboratory_path(uploads, stored_name, root)
            with connect() as db:
                # Transakcja obejmuje kontrolę liczby i zapis, także przy równoległych uploadach.
                db.execute("BEGIN IMMEDIATE")
                if mode == "secure" and db.execute("SELECT COUNT(*) FROM files").fetchone()[0] >= app.config["MAX_FILES"]:
                    raise UploadError("Osiągnięto limit liczby plików.", "file_count", 409)
                # BEFORE może nadpisać plik w obszarze ćwiczenia; AFTER używa unikalnej nazwy.
                with target.open("xb" if mode == "secure" else "wb") as output:
                    output.write(content)
                try:
                    db.execute("INSERT INTO files(id, original_name, stored_name, mime, size) VALUES (?, ?, ?, ?, ?)",
                               (file_id, file.filename, stored_name, mime, len(content)))
                    db.commit()
                except Exception:
                    if mode == "secure":
                        target.unlink(missing_ok=True)
                    raise
        except UploadError as exc:
            return result(str(exc), exc.status, exc.code)
        except (OSError, ValueError):
            return result("Nie można zapisać pliku w podanym miejscu.", 400, "invalid_path")
        return result("Plik zapisany.", 201, "accepted", id=file_id, stored_name=stored_name)

    @app.post("/delete/<file_id>")
    def delete(file_id):
        if not secrets.compare_digest(request.form.get("delete_token", ""), delete_token):
            return result("Odśwież stronę i ponownie wybierz Usuń.", 403, "invalid_token")
        try:
            with connect() as db:
                db.execute("BEGIN IMMEDIATE")
                record = db.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
                if record is None:
                    return result("Nie znaleziono wpisu pliku.", 404, "not_found")
                target = (uploads / record["stored_name"].replace("\\", "/")).resolve()
                other_records = db.execute("SELECT COUNT(*) FROM files WHERE stored_name = ? AND id != ?",
                                           (record["stored_name"], file_id)).fetchone()[0]
                # Usuwanie nigdy nie dziedziczy podatności BEFORE: nie kasuje plików poza uploads.
                # Przy wielokrotnym uploadzie tej samej nazwy BEFORE plik zostaje do ostatniego wpisu.
                if target.parent == uploads.resolve() and not other_records:
                    target.unlink(missing_ok=True)
                db.execute("DELETE FROM files WHERE id = ?", (file_id,))
        except (OSError, ValueError):
            return result("Nie udało się usunąć pliku. Sprawdź, czy nie jest używany przez inny program.",
                          409, "delete_failed")
        return result("Usunięto plik i jego wpis z magazynu.", 200, "deleted")

    @app.get("/download")
    def download():
        if mode == "secure":
            if "name" in request.args:
                return result("Pobieranie wymaga identyfikatora, nie ścieżki.", 400, "path_rejected")
            file_id = request.args.get("id", "")
            if len(file_id) != 32 or any(c not in "0123456789abcdef" for c in file_id):
                return result("Niepoprawny identyfikator pliku.", 400, "invalid_id")
            with connect() as db:
                record = db.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
            if record is None:
                return result("Nie znaleziono pliku.", 404, "not_found")
            target = (uploads / record["stored_name"]).resolve()
            if target.parent != uploads.resolve() or not target.is_file():
                return result("Nie znaleziono pliku.", 404, "not_found")
            # Nazwa odpowiedzi także jest generowana przez serwer.
            name, mime = record["stored_name"], record["mime"]
        else:
            try:
                name = request.args.get("name", "")
                target = laboratory_path(uploads, name, root)
                if not target.is_file():
                    raise ValueError("missing")
                name, mime = target.name, "application/octet-stream"
            except (ValueError, OSError):
                return result("Nie znaleziono pliku w laboratorium.", 404, "not_found")
        app.logger.warning("mode=%s event=download", mode)
        return send_file(target, as_attachment=True, download_name=name, mimetype=mime)

    return app


def create_app(data_dir=None, test_config=None):
    """Jeden serwer, ekran wyboru i dwie niezależne wersje pod osobnymi adresami."""
    app = Flask(__name__)
    base = Path(data_dir or os.environ.get("DATA_DIR", Path(__file__).resolve().parent / "dane"))
    before = create_version_app("vulnerable", base / "before", test_config)
    after = create_version_app("secure", base / "after", test_config)
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def choose_version():
        return render_template("choose.html")

    @app.get("/health")
    def health():
        return jsonify(status="ok", versions=["before", "after"])

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers["Cache-Control"] = "no-store"
        return response

    # Wybór zależy od adresu, a nie wspólnej zmiennej lub sesji użytkownika.
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        "/before": before, "/after": after,
    })
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lokalne laboratorium Secure Upload")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--open-browser", action="store_true", help="Otworz aplikacje w przegladarce")
    args = parser.parse_args()
    from waitress import create_server
    import webbrowser
    try:
        server = create_server(create_app(), host="127.0.0.1", port=args.port)
    except OSError as exc:
        print(f"Nie mozna uruchomic serwera na porcie {args.port}: {exc}")
        print("Sprawdz, czy aplikacja nie jest juz uruchomiona w innym oknie.")
        raise SystemExit(1)
    print(f"Aplikacja: http://127.0.0.1:{args.port}/", flush=True)
    print("Zatrzymanie: Ctrl+C w tym oknie. Zamkniecie karty nie zatrzymuje serwera.", flush=True)
    try:
        if args.open_browser:
            try:
                webbrowser.open(f"http://127.0.0.1:{args.port}/")
            except webbrowser.Error:
                print("Otworz powyzszy adres recznie w przegladarce.")
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        print("Serwer zatrzymany.", flush=True)
