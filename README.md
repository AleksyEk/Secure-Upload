# Bezpieczne przesyłanie plików — BEFORE / AFTER

Lokalna aplikacja do projektu P6 z Bezpieczeństwa Aplikacji Internetowych.
Pozwala porównać podatne i zabezpieczone przesyłanie oraz pobieranie plików.
Jeden serwer obsługuje ekran wyboru i dwa niezależne magazyny danych.

## Pobranie z GitHuba i pierwsze uruchomienie na Windowsie

1. Zainstaluj **Python 3.12 lub nowszy** z https://www.python.org/downloads/windows/.
   Podczas instalacji zaznacz **Add python.exe to PATH**, jeśli ta opcja jest dostępna.
   Projekt zweryfikowano na Pythonie 3.12.
2. W repozytorium wybierz **Code → Download ZIP** albo sklonuj repozytorium.
3. **Rozpakuj cały ZIP** do własnego folderu, np. Dokumenty\STUDIA_BAI.
   Nie uruchamiaj aplikacji bezpośrednio z podglądu archiwum ZIP.
4. Kliknij dwukrotnie **Uruchom aplikacje.bat**.
5. Przy pierwszym starcie poczekaj na utworzenie `.venv` i instalację bibliotek.
   Wymagane są internet oraz możliwość zapisu w folderze projektu.
6. Przeglądarka otworzy ekran wyboru BEFORE / AFTER.

Nie trzeba osobno instalować Flask, Pillow ani SQLite. Wymagane biblioteki
są instalowane automatycznie z `requirements.txt`. Nie instalujemy Pythona
bez wiedzy użytkownika: jeśli go brakuje, okno pokaże instrukcję.

Kolejne uruchomienia wykonujesz tym samym dwuklikiem. Jeśli wersje bibliotek są
zgodne z `requirements.txt`, instalacja jest pomijana i internet nie jest potrzebny.
Po aktualizacji wymagań launcher ponownie zainstaluje wskazane wersje.
Możesz utworzyć skrót do pliku BAT na pulpicie.

## Zatrzymanie i kontrola serwera

**Okno terminala pozostaje widoczne przez cały czas działania aplikacji.**
Naciśnij **Ctrl+C** w tym oknie, aby zatrzymać serwer. Jeżeli Windows zapyta
o zakończenie zadania wsadowego, potwierdź. Samo zamknięcie karty przeglądarki
nie zatrzymuje serwera. Po zatrzymaniu możesz zamknąć okno terminala.
Launcher nie instaluje usługi i nie dodaje aplikacji do autostartu.

Adresy:

- wybór wersji: http://127.0.0.1:5000/
- BEFORE: http://127.0.0.1:5000/before/
- AFTER: http://127.0.0.1:5000/after/

Serwer nasłuchuje wyłącznie na `127.0.0.1`, czyli na tym komputerze.
Jeśli port 5000 jest zajęty, okno pokaże błąd. Zatrzymaj poprzednią instancję.
Po zmianach w kodzie uruchom aplikację ponownie; w razie potrzeby odśwież stronę Ctrl+F5.

## Funkcjonalność

1. Wybierz BEFORE albo AFTER.
2. Wybierz plik i kliknij „Prześlij plik”.
3. Odczytaj komunikat i sprawdź wpis w magazynie.
4. Kliknij „Pobierz”, aby pobrać plik jako załącznik.
5. Przycisk „Usuń” usuwa plik i jego wpis z magazynu. Działa również, gdy plik
   wcześniej skasowano ręcznie z folderu. Usunięcie jest trwałe.
6. Link „Wybór wersji” przenosi na ekran główny.

Obie wersje możesz otworzyć jednocześnie w różnych kartach. Dane i walidacja
nie mieszają się między wersjami. Pliki pozostają po ponownym uruchomieniu.

### AFTER — zastosowane zabezpieczenia

| Mechanizm | Zasada |
| --- | --- |
| Lista rozszerzeń | `.png`, `.jpg`, `.jpeg` |
| Deklarowany MIME | `image/png` lub `image/jpeg`, zgodnie z rozszerzeniem |
| Zawartość | Pillow rozpoznaje format, sprawdza strukturę i odczytuje obraz |
| Rozmiar | 5 MiB na plik, 6 MiB na całe żądanie |
| Liczba | Jeden plik w operacji, maksymalnie 20 zapisanych plików |
| Wymiary | Maksymalnie 20 milionów pikseli |
| Nazwa | Losowy identyfikator i rozszerzenie nadawane przez serwer |
| Przechowywanie | Poza publicznym katalogiem `static` |
| Pobieranie | Po identyfikatorze z bazy, z kontrolą katalogu docelowego |

Nazwa zawierająca ścieżkę jest odrzucana. Nazwy takie jak `obraz.jpg.jpg` nie są
same w sobie błędem: sprawdzane jest ostatnie rozszerzenie i faktyczna zawartość.
Plik WEBP nazwany `.png` zostanie odrzucony. Zmiana rozszerzenia nie konwertuje obrazu.

### BEFORE — wersja podatna

Celowo pomija walidację formatu, limit pojedynczego pliku i limit liczby.
Ufa nazwie i deklaracji MIME klienta. Techniczny limit żądania wynosi 16 MiB.
Manipulacja ścieżką jest ograniczona do własnego katalogu `dane/before`, a baza
jest chroniona przed nadpisaniem w ramach demonstracji. `control.txt` poza
magazynem uploadu jest bezpiecznym celem testu path traversal.

Wyłącznie własne lokalne laboratorium i bezpieczne pliki testowe. Bez wykonywania
złośliwego kodu, kont użytkowników, antywirusa i kwarantanny. Walidacja obrazu
nie jest skanowaniem malware; zachowuje oryginalne bajty i metadane.

## Pliki projektu

```text
Uruchom aplikacje.bat     start dwuklikiem na Windowsie
uruchom.py               tworzenie środowiska, instalacja bibliotek, start aplikacji
app.py                   cała logika BEFORE / AFTER i serwer
templates/
  choose.html            ekran wyboru wersji
  index.html             formularz i magazyn
static/style.css         wygląd
requirements.txt         wersje bibliotek
README.md                ta instrukcja
tests/                   testy automatyczne
testy-reczne/            pliki do prób przez formularz
dane/                    tworzone automatycznie, nie trafia do GitHuba
  after/
    uploads/             zaakceptowane pliki AFTER
    files.sqlite3        metadane AFTER
    control.txt          plik kontrolny
  before/                analogiczny, oddzielny magazyn BEFORE
.venv/                   tworzone lokalnie, nie trafia do GitHuba
```

`__pycache__` tworzy Python automatycznie. Nie trzeba go przesyłać.
Do repozytorium dodaj kod, szablony, style, launcher, wymagania, instrukcję i testy.
Pliki testowe dołączaj wyłącznie, jeśli są bezpieczne i przeznaczone do udostępnienia.
Nie dołączaj `.venv`, `dane` ani własnych prywatnych plików.
Odbiorca otrzymuje pusty magazyn, który aplikacja utworzy przy pierwszym starcie.

## Ręczne uruchomienie i testy

W terminalu, z folderu projektu:

```powershell
python uruchom.py
```

Przygotowanie samych zależności, bez serwera i przeglądarki:

```powershell
python uruchom.py --prepare-only
```

Jeśli środowisko już istnieje, można nadal uruchamiać aplikację bezpośrednio:

```powershell
.\.venv\Scripts\python.exe app.py
```

Opcja `--open-browser` otwiera przeglądarkę, a `--port 5001` pozwala zmienić port.

Testy automatyczne:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Używają oddzielnych katalogów tymczasowych i nie zmieniają ręcznie przesłanych
plików. Pełne scenariusze bezpieczeństwa i dowody do raportu stanowią osobny etap.

## Typowe problemy

- **Brak Pythona:** zainstaluj Python 3.12+ i uruchom ponownie plik BAT.
- **Błąd pobierania bibliotek:** sprawdź internet; pełny komunikat pozostaje w oknie.
- **Przeniesione lub uszkodzone `.venv`:** zatrzymaj aplikację, zmień nazwę tego
  folderu na `.venv-stare` i uruchom BAT ponownie. Dane w `dane` pozostaną zachowane.
- **Zajęty port 5000:** zatrzymaj wcześniejszy serwer. Launcher nie wyłącza cudzych procesów.
- **Przeglądarka się nie otworzyła:** wpisz ręcznie http://127.0.0.1:5000/.

Założeniem dystrybucji jest pobranie źródeł i automatyczne przygotowanie środowiska.
To nie jest samodzielny plik EXE zawierający Pythona.
