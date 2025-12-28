# KjG Pizza Stand - Raspberry Pi Installation

Diese Anleitung beschreibt, wie man die Software auf einem Raspberry Pi installiert und einrichtet.

## Voraussetzungen

*   Raspberry Pi mit Raspberry Pi OS (Lite oder Desktop)
*   Internetverbindung (für die Installation)

## Installation

1.  **Repository klonen (oder Dateien kopieren):**
    Kopiere den Ordner `KjG-Pizza` in das Home-Verzeichnis des Benutzers `pi` (`/home/pi/KjG-Pizza`).

    Wenn du git verwendest:
    ```bash
    cd /home/pi
    git clone <DEIN_REPO_URL> KjG-Pizza
    ```

2.  **System-Abhängigkeiten installieren:**
    ```bash
    sudo apt update
    sudo apt install python3-venv python3-pip -y
    ```

3.  **Start-Skript ausführbar machen:**
    ```bash
    cd /home/pi/KjG-Pizza
    chmod +x start_server.sh
    ```

4.  **Erster Start (Test):**
    Führe das Skript einmal manuell aus, um sicherzustellen, dass alles funktioniert:
    ```bash
    ./start_server.sh
    ```
    Wenn der Server startet (du siehst Ausgaben von Gunicorn), kannst du ihn mit `Ctrl+C` beenden.

## Autostart einrichten (Systemd)

Damit der Server automatisch beim Booten startet:

1.  **Service-Datei kopieren:**
    ```bash
    sudo cp kjg-pizza.service /etc/systemd/system/
    ```

2.  **Service aktivieren und starten:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable kjg-pizza.service
    sudo systemctl start kjg-pizza.service
    ```

3.  **Status prüfen:**
    ```bash
    sudo systemctl status kjg-pizza.service
    ```

## Zugriff

Der Server ist nun im Netzwerk unter der IP-Adresse des Raspberry Pi erreichbar:

*   **Kasse:** `http://<RASPBERRY_PI_IP>:8000/kasse/`
*   **Küche:** `http://<RASPBERRY_PI_IP>:8000/kueche/`
*   **Auswertung:** `http://<RASPBERRY_PI_IP>:8000/auswertung/`
*   **Admin:** `http://<RASPBERRY_PI_IP>:8000/admin/`

## Admin-Benutzer erstellen

Um auf den Admin-Bereich zugreifen zu können, musst du einmalig einen Superuser erstellen:

```bash
cd /home/pi/KjG-Pizza
source .venv/bin/activate
python manage.py createsuperuser
```
