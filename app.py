import io
import json
import ssl
import subprocess
import threading
import time
import urllib.request
import tkinter as tk
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from PIL import Image, ImageTk
import sounddevice as sd
import imageio_ffmpeg

BASE_URL = "https://www.crt.red/2/"
URL_TESTO_REMOTO = BASE_URL + "info.txt"
URL_COPERTINA_IMG = BASE_URL + "copertina.jpg"  # Ripiego se media.json non è disponibile
URL_MEDIA_JSON = BASE_URL + "media.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

STREAMS = {
    "DISCOVERY 2 RADIO": "https://cast5.asurahosting.com/proxy/giancar1/stream",
    "WOLF 1 RADIO": "http://stream.laut.fm/wolf-one",
    "RADIO SOLARIS": "https://cast6.asurahosting.com/proxy/radiosolaris/stream",
    "LAIKA 2 RADIO": "https://fra-pioneer01.dedicateware.com:3155/stream",
    "RADIO SENZA CONFINI": "https://www.crt.red/2/A.mp3",  # Ripiego se media.json non è disponibile
}


def no_cache_url(url):
    """Aggiunge un parametro temporale per evitare copie in cache."""
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["_ts"] = str(int(time.time() * 1000))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class RadioSolarisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RADIO SOLARIS DESKTOP")
        self.root.geometry("450x780")
        self.root.minsize(450, 780)
        self.root.configure(bg="#1e1e1e")

        self.process = None
        self.audio_lock = threading.Lock()
        self.generation = 0
        self.closing = False
        self.current_station = None
        self.photo = None
        self.ctx = ssl.create_default_context()
        self.media_lock = threading.Lock()
        self.media_data = {}

        tk.Label(
            root, text="RADIO SOLARIS DESKTOP", font=("Arial", 16, "bold"),
            fg="white", bg="#1e1e1e"
        ).pack(pady=(14, 8))

        self.img_label = tk.Label(root, bg="#1e1e1e")
        self.img_label.pack(pady=5)

        self.radio_frame = tk.Frame(root, bg="#1e1e1e")
        self.radio_frame.pack(fill="x", padx=10, pady=3)

        for name, url in STREAMS.items():
            tk.Button(
                self.radio_frame, text=f"📻 {name}", font=("Arial", 10, "bold"),
                fg="white", bg="#0078d4", activebackground="#005a9e", bd=0,
                height=2, cursor="hand2",
                command=lambda u=url, n=name: self.play_stream(u, n)
            ).pack(fill="x", pady=1)  # Spazio fra i pulsanti ridotto da 3 a 1

        self.status_label = tk.Label(
            root, text="Pronto. Seleziona una stazione.", font=("Arial", 9, "bold"),
            fg="#8bd5ff", bg="#1e1e1e", wraplength=405, justify="left", anchor="w"
        )
        self.status_label.pack(fill="x", padx=14, pady=(4, 2))

        # Casella di testo con barra di scorrimento verticale.
        text_frame = tk.Frame(root, bg="#1e1e1e")
        text_frame.pack(fill="both", expand=True, padx=14, pady=(2, 8))
        scrollbar = tk.Scrollbar(text_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.text_box = tk.Text(
            text_frame, font=("Arial", 10), fg="white", bg="#1e1e1e",
            wrap="word", relief="flat", borderwidth=0, padx=2, pady=2,
            yscrollcommand=scrollbar.set, insertbackground="white"
        )
        self.text_box.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.text_box.yview)
        self.text_box.insert("1.0", "Caricamento testo dal sito...")
        self.text_box.configure(state="disabled")

        tk.Button(
            root, text="⏹ FERMA RADIO", font=("Arial", 11, "bold"), fg="white",
            bg="#d32f2f", activebackground="#9a0007", bd=0, height=2,
            cursor="hand2", command=self.stop_stream
        ).pack(fill="x", padx=30, pady=(4, 14))

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.update_content_loop, daemon=True).start()

    def set_status(self, text, generation=None):
        if self.closing:
            return
        self.root.after(0, lambda: self._safe_status(text, generation))

    def _safe_status(self, text, generation):
        if self.closing:
            return
        if generation is not None and generation != self.generation:
            return
        self.status_label.configure(text=text)

    def fetch_media_data(self):
        """Legge media.json senza cache; in caso di errore conserva i dati precedenti."""
        try:
            req = urllib.request.Request(no_cache_url(URL_MEDIA_JSON), headers=HEADERS)
            with urllib.request.urlopen(req, context=self.ctx, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
            if isinstance(data, dict):
                with self.media_lock:
                    self.media_data = data
        except Exception:
            pass

    def get_active_audio_url(self, fallback_url):
        self.fetch_media_data()
        with self.media_lock:
            audio = self.media_data.get("audio", {})
            active_url = audio.get("url") if isinstance(audio, dict) else None
        if isinstance(active_url, str) and active_url.startswith(("https://", "http://")):
            return no_cache_url(active_url)
        return no_cache_url(fallback_url)

    def play_stream(self, url, name):
        self.stop_stream(update_status=False)
        self.generation += 1
        generation = self.generation
        self.current_station = name
        self.set_status(f"Connessione a {name}…", generation)
        threading.Thread(
            target=self._audio_worker, args=(url, name, generation), daemon=True
        ).start()

    def _audio_worker(self, url, name, generation):
        process = None
        output = None
        try:
            if name == "RADIO SENZA CONFINI":
                url = self.get_active_audio_url(url)

            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            command = [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-i", url,
                "-vn", "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", "pipe:1"
            ]
            process = subprocess.Popen(
                command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, bufsize=0,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            with self.audio_lock:
                if generation != self.generation or self.closing:
                    process.terminate()
                    return
                self.process = process

            output = sd.RawOutputStream(
                samplerate=44100, channels=2, dtype="int16", blocksize=4096
            )
            output.start()
            self.set_status(f"▶ In riproduzione: {name}", generation)

            pending = b""
            while not self.closing and generation == self.generation:
                chunk = process.stdout.read(16384)
                if not chunk:
                    break
                pending += chunk
                usable = len(pending) - (len(pending) % 4)
                if usable:
                    output.write(pending[:usable])
                    pending = pending[usable:]

            if generation == self.generation and not self.closing:
                detail = ""
                try:
                    if process.poll() is None:
                        process.terminate()
                    error = process.stderr.read(1000)
                    detail = error.decode("utf-8", errors="replace").strip()
                except Exception:
                    pass
                message = f"La riproduzione di {name} è terminata o si è interrotta."
                if detail:
                    message += "\nDettaglio: " + detail[:300]
                self.set_status(message, generation)

        except Exception as exc:
            self.set_status(
                f"Errore audio per {name}.\nControlla URL e uscita audio di Windows.\n{exc}",
                generation
            )
        finally:
            if output is not None:
                try:
                    output.stop()
                    output.close()
                except Exception:
                    pass
            if process is not None:
                try:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                except Exception:
                    pass
            with self.audio_lock:
                if self.process is process:
                    self.process = None

    def stop_stream(self, update_status=True):
        self.generation += 1
        with self.audio_lock:
            process = self.process
            self.process = None
        if process is not None:
            try:
                process.terminate()
            except Exception:
                pass
        self.current_station = None
        if update_status and not self.closing:
            self.set_status("Radio spenta.")

    def update_content_loop(self):
        while not self.closing:
            try:
                req = urllib.request.Request(no_cache_url(URL_TESTO_REMOTO), headers=HEADERS)
                with urllib.request.urlopen(req, context=self.ctx, timeout=8) as response:
                    text = response.read().decode("utf-8", errors="ignore").strip()
                if text and len(text) < 5000 and not text.lower().startswith(("<!doctype html", "<html")):
                    self.root.after(0, lambda t=text: self._set_remote_text(t))
            except Exception:
                pass

            self.fetch_media_data()
            with self.media_lock:
                cover = self.media_data.get("copertina", {})
                cover_url = cover.get("url") if isinstance(cover, dict) else None
            if not isinstance(cover_url, str) or not cover_url.startswith(("https://", "http://")):
                cover_url = URL_COPERTINA_IMG

            try:
                req = urllib.request.Request(no_cache_url(cover_url), headers=HEADERS)
                with urllib.request.urlopen(req, context=self.ctx, timeout=8) as response:
                    data = response.read()
                image = Image.open(io.BytesIO(data)).convert("RGB")
                image.thumbnail((230, 230), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.root.after(0, lambda p=photo: self.set_image(p))
            except Exception:
                pass
            time.sleep(30)

    def _set_remote_text(self, text):
        if self.closing:
            return
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", text[:4000])
        self.text_box.configure(state="disabled")

    def set_image(self, photo):
        if self.closing:
            return
        self.photo = photo
        self.img_label.configure(image=photo)

    def on_closing(self):
        self.closing = True
        self.stop_stream(update_status=False)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RadioSolarisApp(root)
    root.mainloop()

                
