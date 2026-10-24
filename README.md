# Bezpieczne przesyłanie plików — BEFORE / AFTER

Projekt P6 z przedmiotu **Bezpieczeństwo Aplikacji Internetowych**.
Lokalna aplikacja internetowa umożliwia porównanie podatnego i zabezpieczonego
mechanizmu przesyłania oraz pobierania plików. Obie wersje działają w jednym
procesie serwera, pod oddzielnymi adresami i z niezależnymi magazynami danych.

## Wymagania

- System Windows — dla uruchamiania dwuklikiem przez plik BAT.
- Python **3.12 lub nowszy**. Instalację i działanie zweryfikowano na Pythonie 3.12.
- Przeglądarka internetowa.
- Dostęp do internetu podczas pierwszej instalacji bibliotek lub zmiany ich wersji.
- Uprawnienia do zapisu w rozpakowanym katalogu projektu.
- Wolny port lokalny **5000**.

Nie jest wymagany Docker ani osobny serwer bazy danych. SQLite jest obsługiwany
przez standardową bibliotekę Pythona. Flask, Pillow i pozostałe zależności są
instalowane automatycznie na podstawie `requirements.txt`.

## Pobranie i instalacja

1. Należy zainstalować Pythona ze [strony oficjalnej](https://www.python.org/downloads/windows/).
   Jeżeli instalator udostępnia opcję **Add python.exe to PATH**, należy ją zaznaczyć.
   Plik uruchamiający rozpoznaje polecenie `py` lub `python`.
2. Na stronie repozytorium GitHub należy wybrać **Code → Download ZIP**.
   Alternatywnie można sklonować repozytorium za pomocą Git.
3. Archiwum należy w całości rozpakować do katalogu z prawem zapisu.
   Uruchamianie bezpośrednio z podglądu archiwum ZIP nie jest obsługiwane.
4. W rozpakowanym katalogu, obok `app.py` i `requirements.txt`, należy uruchomić
   dwuklikiem plik **`Uruchom aplikacje.bat`**.
5. Przy pierwszym uruchomieniu automatycznie następuje:
   - wykrycie dostępnego interpretera Pythona;
   - utworzenie lokalnego środowiska wirtualnego `.venv`;
   - instalacja wymaganych wersji bibliotek;
   - uruchomienie serwera;
   - otwarcie ekranu wyboru BEFORE / AFTER w domyślnej przeglądarce.

Jeżeli Python nie zostanie wykryty, w oknie zostanie wyświetlona instrukcja
instalacji. Python nie jest instalowany automatycznie przez aplikację.

## Kolejne uruchomienia

Aplikację należy uruchamiać tym samym plikiem **`Uruchom aplikacje.bat`**.
Jeżeli zainstalowane biblioteki odpowiadają `requirements.txt`, ich instalacja
jest pomijana i dostęp do internetu nie jest wymagany. Po zmianie wymagań
skrypt instaluje wskazane wersje zależności.

Dostępne adresy:

| Widok | Adres |
| --- | --- |
| Wybór wersji | [http://127.0.0.1:5000/](http://127.0.0.1:5000/) |
| BEFORE — wersja podatna | [http://127.0.0.1:5000/before/](http://127.0.0.1:5000/before/) |
| AFTER — wersja zabezpieczona | [http://127.0.0.1:5000/after/](http://127.0.0.1:5000/after/) |

Serwer nasłuchuje wyłącznie na `127.0.0.1`, czyli na komputerze, na którym
został uruchomiony. W przypadku braku automatycznego otwarcia przeglądarki
należy otworzyć pierwszy adres ręcznie.

## Zatrzymanie aplikacji

Okno terminala pozostaje widoczne przez cały czas działania serwera.
Zatrzymanie następuje po naciśnięciu **Ctrl+C** w tym oknie. Jeżeli system
wyświetli pytanie o zakończenie zadania wsadowego, należy je potwierdzić.

**Zamknięcie karty przeglądarki nie zatrzymuje serwera.** Skrypt nie instaluje
usługi systemowej i nie dodaje aplikacji do autostartu. Przesłane pliki i wpisy
bazy danych pozostają zapisane po zatrzymaniu oraz ponownym uruchomieniu.

Po zmianie kodu wymagane jest ponowne uruchomienie serwera. W celu odświeżenia
stylów i skryptów w przeglądarce można użyć **Ctrl+F5**.

## Obsługa i funkcjonalność

- Ekran główny umożliwia wybór wersji BEFORE lub AFTER.
- Formularz „Prześlij plik” obsługuje przesyłanie pojedynczego pliku.
- „Magazyn plików” prezentuje nazwę oryginalną, nazwę magazynową i rozmiar w MB.
- „Pobierz” udostępnia plik jako załącznik.
- „Usuń” trwale usuwa wpis i plik z magazynu. Wpis można usunąć także po
  wcześniejszym ręcznym skasowaniu pliku. W BEFORE współdzielony plik o tej samej
  nazwie pozostaje do usunięcia ostatniego odwołującego się do niego wpisu.
- Link „Wybór wersji” prowadzi do ekranu głównego.
- Komunikaty powodzenia i błędów pojawiają się u góry, na środku ekranu.
  Znikają po 5 sekundach; najechanie myszką lub ustawienie fokusu w komunikacie
  wstrzymuje odliczanie. Przycisk „×” umożliwia wcześniejsze zamknięcie.

Obie wersje mogą być otwarte jednocześnie w osobnych kartach. Wybór jest związany
z adresem, a nie globalnym przełącznikiem. Dane obu wersji pozostają niezależne.

### AFTER — mechanizmy ochrony

| Mechanizm | Zasada |
| --- | --- |
| Dozwolone rozszerzenia | `.png`, `.jpg`, `.jpeg` |
| Deklarowany MIME | `image/png` lub `image/jpeg`, zgodnie z rozszerzeniem |
| Rzeczywista zawartość | Rozpoznanie formatu, sprawdzenie struktury i odczyt obrazu przez Pillow |
| Rozmiar pojedynczego pliku | Maksymalnie 5 MiB, czyli 5 242 880 bajtów — około 5,24 MB |
| Rozmiar całego żądania | Maksymalnie 6 MiB, czyli około 6,29 MB |
| Liczba plików | Jeden plik na operację i maksymalnie 20 zapisanych plików |
| Wymiary obrazu | Maksymalnie 20 milionów pikseli |
| Nazwa magazynowa | Losowy identyfikator i rozszerzenie nadawane przez serwer |
| Zapis | Poza publicznym katalogiem `static` |
| Pobieranie | Po identyfikatorze z bazy, z kontrolą katalogu docelowego |

W tabeli interfejsu obowiązuje przelicznik **1 MB = 1 000 000 bajtów**;
limity w kodzie wykorzystują **1 MiB = 1 048 576 bajtów**. Komunikat błędu podaje
maksymalny rozmiar w MB, zaokrąglony do dwóch miejsc po przecinku.

Nazwy zawierające ścieżkę są odrzucane. Nazwa `obraz.jpg.jpg` sama w sobie nie
powoduje odrzucenia: sprawdzane są końcowe rozszerzenie i zawartość. Plik WEBP
nazwany `.png` zostanie odrzucony. Zmiana rozszerzenia nie konwertuje formatu.

### BEFORE — mechanizm podatny

Wersja BEFORE celowo pomija walidację formatu, limit rozmiaru pojedynczego pliku
oraz limit liczby zapisanych plików. Wykorzystuje nazwę i deklarację MIME klienta.
Techniczny limit całego żądania wynosi 16 MiB.

Manipulacja ścieżką w ramach demonstracji jest ograniczona do własnego katalogu
`dane/before`. Baza jest chroniona przed nadpisaniem. Plik `control.txt`, znajdujący
się poza katalogiem `uploads`, stanowi bezpieczny cel testu path traversal.
Funkcja usuwania nie pozwala kasować plików poza magazynem `uploads`.

## Zakres i ograniczenia

Aplikacja jest przeznaczona wyłącznie do autoryzowanego, lokalnego laboratorium.
Do demonstracji wystarczają bezpieczne pliki testowe i dowody działania ochrony.
Wykonywanie rzeczywistego złośliwego kodu nie jest wymagane.

Poza zakresem pozostają konta użytkowników, uprawnienia między użytkownikami,
skanowanie antywirusowe oraz kwarantanna. Walidacja obrazu nie zastępuje skanowania
malware; oryginalne bajty, metadane i ewentualne dodatkowe dane są zachowywane.
Testy funkcjonalne nie stanowią potwierdzenia odporności na wszystkie ataki.

## Struktura projektu i przechowywanie danych

```text
Uruchom aplikacje.bat     uruchamianie dwuklikiem w systemie Windows
uruchom.py               przygotowanie środowiska i uruchomienie serwera
app.py                   logika BEFORE / AFTER i serwer
templates/
  choose.html            ekran wyboru wersji
  index.html             formularz i magazyn
static/
  style.css              wygląd aplikacji
  notifications.js       automatyczne zamykanie komunikatów i odliczanie
requirements.txt         wymagane wersje bibliotek
README.md                instrukcja instalacji i obsługi
tests/                   testy automatyczne
testy-reczne/            przykładowe pliki do testów przez formularz
dane/                    dane lokalne, tworzone automatycznie
  after/
    uploads/             zaakceptowane pliki AFTER
    files.sqlite3        metadane AFTER
    control.txt          plik kontrolny
  before/                analogiczny, niezależny magazyn BEFORE
.venv/                   lokalne środowisko Pythona, tworzone automatycznie
```

Foldery `dane`, `.venv` i `__pycache__` nie są przeznaczone do publikacji.
Nowa kopia pobrana z repozytorium tworzy własne środowisko i puste magazyny.
Kod i zależności są dostarczane jako źródła; projekt nie jest samodzielnym
plikiem EXE zawierającym interpreter Pythona.

Ręczne usunięcie obrazu z `uploads` nie usuwa wpisu z bazy `files.sqlite3`.
Do usuwania obu elementów służy przycisk „Usuń” w interfejsie.

## Uruchomienie z terminala

Poniższe polecenia należy wykonywać w głównym katalogu projektu.

Przygotowanie zależności i uruchomienie aplikacji z otwarciem przeglądarki:

```powershell
python uruchom.py
```

Jeżeli instalacja Pythona udostępnia polecenie `py`, odpowiednikiem jest
`py -3 uruchom.py`.

Przygotowanie wyłącznie środowiska, bez uruchamiania serwera i przeglądarki:

```powershell
python uruchom.py --prepare-only
```

Bezpośrednie uruchomienie po przygotowaniu środowiska:

```powershell
.\.venv\Scripts\python.exe app.py
```

Bezpośrednie uruchomienie z otwarciem przeglądarki i innym portem:

```powershell
.\.venv\Scripts\python.exe app.py --open-browser --port 5001
```

W ostatnim przypadku ekran główny jest dostępny pod adresem
[http://127.0.0.1:5001/](http://127.0.0.1:5001/).

## Testy automatyczne

Po przygotowaniu środowiska testy można uruchomić poleceniem:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Testy korzystają z oddzielnych katalogów tymczasowych. Nie uruchamiają serwera
HTTP ani przeglądarki i nie zmieniają ręcznie przesłanych plików. Obejmują m.in.
przesyłanie i pobieranie, trwałość danych, nawigację, rozdzielenie magazynów,
różnicę walidacji między wersjami oraz usuwanie plików i pozostałych wpisów.

## Rozwiązywanie problemów

| Problem | Postępowanie |
| --- | --- |
| Brak interpretera Pythona | Należy zainstalować Python 3.12+ i ponownie uruchomić plik BAT. |
| Błąd instalacji bibliotek | Należy sprawdzić połączenie z internetem oraz komunikat w terminalu. |
| Uszkodzone lub przeniesione `.venv` | Po zatrzymaniu aplikacji należy zmienić nazwę folderu na `.venv-stare` i ponownie uruchomić BAT. Magazyny w `dane` pozostają zachowane. |
| Zajęty port 5000 | Należy zatrzymać poprzedni serwer albo wybrać inny port przy bezpośrednim uruchomieniu. Skrypt nie zatrzymuje innych procesów. |
| Brak automatycznego otwarcia przeglądarki | Należy ręcznie otworzyć adres wyświetlony w terminalu. |
| Nieaktualny wygląd strony | Należy odświeżyć stronę przez Ctrl+F5; po zmianie kodu należy też ponownie uruchomić serwer. |
