import tkinter as tk
import threading
import urllib.request
import ssl
import subprocess
import io
from PIL import Image, ImageTk

# =========================================================================
# CONFIGURAZIONE LINK ESTERNI (CONERO RADIO TEAM)
# =========================================================================
URL_TESTO_REMOTO = "https://www.crt.red/2/info.mp3"
URL_COPERTINA_IMG = "https://crt.red/2/copertina.jpg"
URL_STAZIONE_MP3 = "https://crt.red/2/A.mp3"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

class FinalDynamicRadioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RADIO SOLARIS DESKTOP")
        self.root.geometry("450x720")
        self.root.configure(bg="#1e1e1e")

        # Gestore per il tracciamento del processo audio attivo
        self.audio_process = None
        
        # Mappa delle stazioni radio attive
        self.streams = {
            "DISCOVERY 2 RADIO": "https://cast5.asurahosting.com/proxy/giancar1/stream",
            "WOLF 1 RADIO": "http://stream.laut.fm/wolf-one",
            "RADIO SOLARIS": "https://cast6.asurahosting.com/proxy/radiosolaris/stream",
            "LAIKA 2 RADIO": "https://fra-pioneer01.dedicateware.com:3155/stream",
            "STAZIONE 5": "https://www.crt.red/2/A.mp3
        }

        # UI Grafica Scura Stile Windows 11
        self.label_title = tk.Label(root, text="RADIO SOLARIS DESKTOP", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e")
        self.label_title.pack(pady=15)

        # Contenitore per l'immagine di copertina
        self.img_label = tk.Label(root, bg="#1e1e1e")
        self.img_label.pack(pady=10)

        # Frame per i bottoni delle stazioni
        self.radio_frame = tk.Frame(root, bg="#1e1e1e")
        self.radio_frame.pack(pady=10, fill="x")

        # Display informativo testuale
        self.text_label = tk.Label(root, text="Sincronizzazione contenuti...", font=("Arial", 11), fg="#00ccff", bg="#1e1e1e", wraplength=380)
        self.text_label.pack(pady=10, padx=10)

        # Costruisce i componenti grafici e avvia i loop asincroni
        self.build_ui()
        
        # Configura il contesto SSL per evitare errori di certificati su vecchie macchine
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

        # Avvia il thread per aggiornare testo e immagini dal web in background
        threading.Thread(target=self.update_content_loop, daemon=True).start()
        
        # Intercetta la chiusura della finestra per spegnere l'audio residuo
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_ui(self):
        """Genera i bottoni delle stazioni radio e i controlli di stop."""
        for nome, url in self.streams.items():
            btn = tk.Button(self.radio_frame, text=f"📻 {nome}", font=("Arial", 11, "bold"), 
                            fg="white", bg="#0078d4", activebackground="#005a9e", 
                            activeforeground="white", bd=0, height=2, cursor="hand2")
            btn.configure(command=lambda u=url, n=nome: self.play_stream(u, n))
            btn.pack(pady=4, padx=30, fill="x")
            
        # Bottone dedicato alla stazione MP3 fissa
        btn_mp3 = tk.Button(self.radio_frame, text="📻 RIPRODUCI STAZIONE WEB MP3", font=("Arial", 11, "bold"), 
                            fg="white", bg="#2b88d8", activebackground="#005a9e", 
                            activeforeground="white", bd=0, height=2, cursor="hand2")
        btn_mp3.configure(command=self.play_mp3_stream)
        btn_mp3.pack(pady=10, padx=30, fill="x")

        # Bottone STOP Generale
        btn_stop = tk.Button(self.root, text="⏹️ FERMA RADIO", font=("Arial", 11, "bold"), 
                             fg="white", bg="#d32f2f", activebackground="#9a0007", 
                             activeforeground="white", bd=0, height=2, cursor="hand2")
        btn_stop.configure(command=self.stop_stream)
        btn_stop.pack(pady=15, padx=50, fill="x")

    def play_stream(self, url, nome):
        """Interrompe l'audio precedente e avvia il nuovo streaming su thread separato."""
        self.text_label.configure(text=f"Apertura: {nome}...")
        self.stop_stream()
        threading.Thread(target=self.execute_native_audio, args=(url, nome), daemon=True).start()

    def play_mp3_stream(self):
        """Avvia la riproduzione diretta dell'MP3 fisso sul server."""
        self.play_stream(URL_STAZIONE_MP3, "STAZIONE MP3 WEB")

    def execute_native_audio(self, url, nome):
        """Esegue il motore audio di Windows Presentation Foundation in background."""
        try:
            # Script PowerShell per inizializzare il MediaPlayer nativo invisibile di Windows
            ps_cmd = (
                f"[Reflection.Assembly]::LoadWithPartialName('PresentationCore') | Out-Null; "
                f"$player = New-Object System.Windows.Media.MediaPlayer; "
                f"$player.Open('{url}'); "
                f"$player.Play(); "
                f"while ($true) {{ Start-Sleep -Seconds 1 }}"
            )
            
            # Nasconde del tutto la finestra di PowerShell a livello di kernel
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # Equivalente a SW_HIDE
            
            self.audio_process = subprocess.Popen(
                ["powershell", "-Command", ps_cmd],
                startupinfo=startupinfo,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.root.after(0, lambda: self.text_label.configure(text=f"In riproduzione: {nome} 🎶"))
        except Exception as e:
            self.root.after(0, lambda: self.text_label.configure(text="Errore nel caricamento del flusso audio"))

    def stop_stream(self):
        """Uccide qualsiasi processo audio o di controllo rimasto attivo in background."""
        try:
            subprocess.run("taskkill /f /im powershell.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run("taskkill /f /im wmplayer.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
        self.audio_process = None
        self.text_label.configure(text="Radio spenta.")

    def update_content_loop(self):
        """Loop infinito in background per scaricare e aggiornare costantemente testo e copertina."""
        while True:
            try:
                # 1. Aggiornamento Testo Informativo
                req_text = urllib.request.Request(URL_TESTO_REMOTO, headers=HEADERS)
                with urllib.request.urlopen(req_text, context=self.ctx, timeout=5) as response:
                    testo = response.read().decode('utf-8', errors='ignore').strip()
                if testo:
                    self.root.after(0, lambda t=testo: self.text_label.configure(text=t))

                # 2. Aggiornamento Immagine Copertina
                req_img = urllib.request.Request(URL_COPERTINA_IMG, headers=HEADERS)
                with urllib.request.urlopen(req_img, context=self.ctx, timeout=5) as response:
                    img_data = response.read()
                
                image = Image.open(io.BytesIO(img_data))
                image = image.resize((180, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                self.root.after(0, lambda p=photo: self.set_image(p))
            except Exception as e:
                # In caso di errore o server offline, non blocca l'app
                pass
            
            time.sleep(30) # Sincronizza i dati dal sito ogni 30 secondi

    def set_image(self, photo):
        """Aggiorna l'immagine di copertina tenendo il riferimento in memoria."""
        self.img_label.configure(image=photo)
        self.img_label.image = photo

    def on_closing(self):
        """Gestisce l'uscita pulita chiudendo i flussi audio attivi."""
        self.stop_stream()
        self.root.destroy()

# =========================================================================
# AVVIO APPLICAZIONE
# =========================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = FinalDynamicRadioApp(root)
    root.mainloop()
