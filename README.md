# KjG Pizza Manager 🍕

Ein einfaches, aber leistungsfähiges System zur Verwaltung von Pizza-Bestellungen, entwickelt für Vereinsfeste, Jugendgruppen (wie die KjG) und kleine Verkaufsstände.

Dieses Projekt ermöglicht die digitale Erfassung von Bestellungen, die Kommunikation zwischen Kasse und Küche sowie die Auswertung der Verkäufe. Es ist optimiert für den Betrieb auf einem Raspberry Pi, kann aber auf jedem System mit Python ausgeführt werden.

## 🚀 Funktionen

Das System ist in verschiedene Ansichten unterteilt, um den Arbeitsfluss zu optimieren:

### 🛒 Kasse (`/kasse/`)
*   **Dashboard:** Übersicht über alle aktuellen Bestellungen und deren Status.
*   **Bestellaufnahme:** Schnelles Erfassen neuer Bestellungen (`/kasse/neu/`).
*   **Status-Management:** Bestellungen als "Bezahlt" markieren oder den Status ändern (Eingegangen -> In Zubereitung -> Abholbereit -> Abgeschlossen).

### 👨‍🍳 Küche (`/kueche/`)
*   **Live-Ansicht:** Zeigt alle offenen Bestellungen an, die zubereitet werden müssen.
*   **Status-Updates:** Köche können den Status von "Eingegangen" auf "In Zubereitung" und "Abholbereit" setzen.
*   **Automatische Aktualisierung:** Die Ansicht aktualisiert sich regelmäßig (oder manuell), um neue Bestellungen anzuzeigen.

### 📊 Auswertung (`/auswertung/`)
*   **Statistiken:** Übersicht über verkaufte Pizzen, Einnahmen und Bestseller.
*   **Tagesabschluss:** Hilfreich für die Abrechnung am Ende des Events.

### 📱 Kunden-Ansicht (`/`)
*   **Digitale Speisekarte:** Kunden können das aktuelle Angebot einsehen.
*   *(Optional: Bestellstatus-Monitor für Kunden)*

## 🛠️ Technologie-Stack

*   **Backend:** Python, Django 5.0+
*   **Datenbank:** SQLite (Standard, einfach zu sichern)
*   **Server:** Gunicorn (für Produktion), Whitenoise (für statische Dateien)
*   **Frontend:** HTML, CSS (Bootstrap/Tailwind - je nach Template), JavaScript

## 📦 Installation & Einrichtung

### Voraussetzungen
*   Python 3.8 oder neuer
*   Git

### Lokale Installation (Entwicklung/Laptop)

1.  **Repository klonen:**
    ```bash
    git clone https://github.com/Ninob1610/kjg-pizza-manager.git
    cd kjg-pizza-manager
    ```

2.  **Virtuelle Umgebung erstellen und aktivieren:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/Mac
    # oder
    .venv\Scripts\activate     # Windows
    ```

3.  **Abhängigkeiten installieren:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Datenbank einrichten:**
    ```bash
    python manage.py migrate
    ```

5.  **Admin-Zugriff einrichten:**
    Beim ersten Start wird automatisch ein Standard-Admin erstellt, falls noch keiner existiert.
    Login: `admin` / `admin`

    Wenn du stattdessen oder zusätzlich einen eigenen Admin anlegen möchtest:
    ```bash
    python manage.py createsuperuser
    ```

6.  **Server starten:**
    ```bash
    python manage.py runserver
    ```
    Das System ist nun unter `http://127.0.0.1:8000` erreichbar.

### 🍓 Installation auf Raspberry Pi

Für den produktiven Einsatz auf einem Raspberry Pi gibt es ein automatisiertes Skript und eine detaillierte Anleitung.

👉 **Siehe [README_PI.md](README_PI.md) für die Raspberry Pi Anleitung.**

Kurzfassung:
```bash
chmod +x start_server.sh
./start_server.sh
```

## ⚙️ Konfiguration

### Produkte verwalten
Um Pizzen und Getränke hinzuzufügen oder Preise zu ändern:
1.  Gehe zu `http://<deine-ip>:8000/admin/`
2.  Logge dich mit dem Standard-Admin ein (`admin` / `admin`) oder mit deinem eigenen Superuser.
3.  Unter **Orders** -> **Products** kannst du das Menü bearbeiten.

### Einstellungen
Die Hauptkonfiguration befindet sich in `config/settings.py`. Hier können `ALLOWED_HOSTS`, `DEBUG` Modus und Datenbank-Einstellungen angepasst werden.

## 🤝 Mitwirken

Beiträge sind willkommen! Bitte erstelle ein Issue für Fehlerberichte oder Feature-Requests.

## 📝 Lizenz

[MIT License](LICENSE) (oder entsprechende Lizenz einfügen)
