
import io
import ssl
import subprocess
import threading
import time
import urllib.request
import tkinter as tk
from PIL import Image, ImageTk
import sounddevice as sd
import imageio_ffmpeg

URL_TESTO_REMOTO = "https://crt.red/2/info.txt"
URL_COPERTINA_IMG = "https://crt.red/2/copertina.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
}

STREAMS = {
    "DISCOVERY 2 RADIO": "https://cast5.asurahosting.com/proxy/giancar1/stream",
    "WOLF 1 RADIO": "http://stream.laut.fm/wolf-one",
    "RADIO SOLARIS": "https://cast6.asurahosting.com/proxy/radiosolaris/stream",
    "LAIKA 2 RADIO": "https://fra-pioneer01.dedicateware.com:3155/stream",
    "RADIO SENZA CONFINI": "https://www.crt.red/2/A.mp3",
}


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

        tk.Label(
            root,
            text="RADIO SOLARIS DESKTOP",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(pady=(14, 8))

        self.img_label = tk.Label(root, bg="#1e1e1e")
        self.img_label.pack(pady=5)

        self.radio_frame = tk.Frame(root, bg="#1e1e1e")
        self.radio_frame.pack(fill="x", padx=10, pady=5)

        for name, url in STREAMS.items():
            tk.Button(
                self.radio_frame,
                text=f"📻 {name}",
                font=("Arial", 10, "bold"),
                fg="white",
                bg="#0078d4",
                activebackground="#005a9e",
                bd=0,
                height=2,
                cursor="hand2",
                command=lambda u=url, n=name: self.play_stream(u, n)
            ).pack(fill="x", pady=3)

        # Etichetta separata per lo stato della radio.
        # Gli avvisi di riproduzione non cancellano più il testo del sito.
        self.status_label = tk.Label(
            root,
            text="Pronto. Seleziona una stazione.",
            font=("Arial", 9, "bold"),
            fg="#8bd5ff",
            bg="#1e1e1e",
            wraplength=405,
            justify="left",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=14, pady=(5, 2))

        # Questa etichetta è riservata al testo remoto del sito.
        self.text_label = tk.Label(
            root,
            text="Caricamento testo dal sito...",
            font=("Arial", 10),
            fg="white",
            bg="#1e1e1e",
            wraplength=405,
            justify="left",
            anchor="nw"
        )
        self.text_label.pack(
            fill="both", expand=True, padx=14, pady=(2, 8)
        )

        tk.Button(
            root,
            text="⏹ FERMA RADIO",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#d32f2f",
            activebackground="#9a0007",
            bd=0,
            height=2,
            cursor="hand2",
            command=self.stop_stream
        ).pack(fill="x", padx=30, pady=(4, 14))

        self.ctx = ssl.create_default_context()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        threading.Thread(
            target=self.update_content_loop,
            daemon=True
        ).start()

    def set_status(self, text, generation=None):
        if self.closing:
            return
        self.root.after(
            0, lambda: self._safe_status(text, generation)
        )

    def _safe_status(self, text, generation):
        if self.closing:
            return
        if generation is not None and generation != self.generation:
            return

        # Aggiorna soltanto lo stato della radio.
        self.status_label.configure(text=text)

    def play_stream(self, url, name):
        self.stop_stream(update_status=False)
        self.generation += 1
        generation = self.generation
        self.current_station = name

        self.set_status(f"Connessione a {name}…", generation)

        threading.Thread(
            target=self._audio_worker,
            args=(url, name, generation),
            daemon=True
        ).start()

    def _audio_worker(self, url, name, generation):
        process = None
        output = None

        try:
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

            command = [
                ffmpeg, "-hide_banner", "-loglevel", "error",
                "-nostdin", "-i", url,
                "-vn", "-f", "s16le",
                "-acodec", "pcm_s16le",
                "-ar", "44100", "-ac", "2",
                "pipe:1"
            ]

            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                creationflags=getattr(
                    subprocess, "CREATE_NO_WINDOW", 0
                )
            )

            with self.audio_lock:
                if generation != self.generation or self.closing:
                    process.terminate()
                    return
                self.process = process

            output = sd.RawOutputStream(
                samplerate=44100,
                channels=2,
                dtype="int16",
                blocksize=4096
            )
            output.start()

            self.set_status(f"▶ In riproduzione: {name}", generation)

            # Audio PCM: 16 bit, stereo = 4 byte per fotogramma.
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
                    detail = error.decode(
                        "utf-8", errors="replace"
                    ).strip()
                except Exception:
                    pass

                message = (
                    f"La riproduzione di {name} "
                    "è terminata o si è interrotta."
                )
                if detail:
                    message += "\nDettaglio: " + detail[:300]

                self.set_status(message, generation)

        except Exception as exc:
            self.set_status(
                f"Errore audio per {name}.\n"
                f"Controlla URL e uscita audio di Windows.\n{exc}",
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
            # Aggiorna il testo remoto senza interrompere la radio.
            try:
                req = urllib.request.Request(
                    URL_TESTO_REMOTO,
                    headers=HEADERS
                )
                with urllib.request.urlopen(
                    req, context=self.ctx, timeout=5
                ) as response:
                    text = response.read().decode(
                        "utf-8", errors="ignore"
                    ).strip()

                if text and len(text) < 5000 and not text.lower().startswith(
                    ("<!doctype html", "<html")
                ):
                    self.root.after(
                        0, lambda t=text: self._set_remote_text(t)
                    )
            except Exception:
                pass

            # Copertina leggermente più grande: 230 x 230.
            try:
                req = urllib.request.Request(
                    URL_COPERTINA_IMG,
                    headers=HEADERS
                )
                with urllib.request.urlopen(
                    req, context=self.ctx, timeout=5
                ) as response:
                    data = response.read()

                image = Image.open(io.BytesIO(data)).convert("RGB")
                image.thumbnail((230, 230), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)

                self.root.after(
                    0, lambda p=photo: self.set_image(p)
                )
            except Exception:
                pass

            time.sleep(30)

    def _set_remote_text(self, text):
        # Il testo resta visibile anche mentre una radio suona.
        if not self.closing:
            self.text_label.configure(text=text[:4000])

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
