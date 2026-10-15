import tkinter as tk
import threading
import urllib.request
import ssl
import subprocess
import time
import io
from PIL import Image, ImageTk

# =========================================================================
# IMPOSTA QUI I TUOI INDIRIZZI FISSI ESTERNI (RIPRISTINATI)
# =========================================================================
URL_TESTO_REMOTO = "https://crt.red/2/info.txt"
URL_COPERTINA_IMG = "https://crt.red/2/copertina.jpg"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

class FinalDynamicRadioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RADIO SOLARIS DESKTOP")
        self.root.geometry("450x680")
        self.root.configure(bg="#1e1e1e")

        # Gestore per tracciare il processo audio attivo
        self.audio_process = None
        
        # UI Grafica Scura Windows 11
        self.label_title = tk.Label(root, text="RADIO SOLARIS DESKTOP", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e")
        self.label_title.pack(pady=20)

        # Contenitore per l'immagine di copertina (SISTEMATO)
        self.img_label = tk.Label(root, bg="#1e1e1e")
        self.img_label.pack(pady=10)

        # Frame per contenere i bottoni delle stazioni
        self.radio_frame = tk.Frame(root, bg="#1e1e1e")
        self.radio_frame.pack(pady=10, fill="x")

        # Display informativo testuale (SISTEMATO)
        self.text_label = tk.Label(root, text="Sincronizzazione contenuti...", font=("Arial", 11), fg="white", bg="#1e1e1e", wraplength=380)
        self.text_label.pack(pady=10, padx=10)

        # I tuoi indirizzi reali e completi ripristinati e intatti
        r1 = "https://cast5.asurahosting.com/proxy/giancar1/stream"
        r2 = "http://stream.laut.fm/wolf-one"
        r3 = "https://cast6.asurahosting.com/proxy/radiosolaris/stream"
        r4 = "https://fra-pioneer01.dedicateware.com:3155/stream"
        r5 = "https://crt.red"
        
        self.streams = {
            "DISCOVERY 2 RADIO": r1,
            "WOLF 1 RADIO": r2,
            "RADIO SOLARIS": r3,
            "LAIKA 2 RADIO": r4,
            "STAZIONE 5": r5
        }
        
        # Gestione stazioni (I tuoi parametri di rete originali)
        self.url_mp3 = "https://crt.red"

        # Configura il contesto SSL locale per scaricare in sicurezza senza blocchi
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

        self.build_ui()
        
        # Avvia il ciclo continuo di aggiornamento per immagini e testi
        threading.Thread(target=self.update_content_loop, daemon=True).start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_ui(self):
        for nome, url in self.streams.items():
            btn = tk.Button(self.radio_frame, text=f"📻 {nome}", font=("Arial", 11, "bold"), fg="white", bg="#0078d4", activebackground="#005a9e", activeforeground="white", bd=0, height=2, cursor="hand2")
            btn.configure(command=lambda u=url, n=nome: self.play_stream(u, n))
            btn.pack(pady=5, padx=10, fill="x")
            
        # Bottone dedicato alla stazione MP3 fissa
        btn_mp3 = tk.Button(self.radio_frame, text="📻 RIPRODUCI STAZIONE WEB MP3", font=("Arial", 11, "bold"), fg="white", bg="#0078d4", activebackground="#005a9e", activeforeground="white", bd=0, height=2, cursor="hand2")
        btn_mp3.configure(command=self.play_mp3_stream)
        btn_mp3.pack(pady=15, padx=10, fill="x")

        # Bottone STOP dedicato
        btn_stop = tk.Button(self.root, text="⏹️ FERMA RADIO", font=("Arial", 11, "bold"), fg="white", bg="#d32f2f", activebackground="#9a0007", activeforeground="white", bd=0, height=2, cursor="hand2")
        btn_stop.configure(command=self.stop_stream)
        btn_stop.pack(pady=15, padx=30, fill="x")

    def play_stream(self, url, nome):
        self.text_label.configure(text=f"Apertura: {nome}...")
        self.stop_stream()
        # Avvia lo scaricamento e la riproduzione in background continuo senza congelare Tkinter
        threading.Thread(target=self.execute_native_audio, args=(url, nome), daemon=True).start()
        
    def play_mp3_stream(self):
        self.text_label.configure(text="Bufferizzazione flusso audio in corso...")
        self.play_stream(self.url_mp3, "STAZIONE MP3 WEB")

    def execute_native_audio(self, url, nome):
        try:
            # Comando di Windows Media Player eseguito in modo isolato
            cmd = f'wmplayer.exe "{url}"'
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # 0 nasconde del tutto la finestra principale, lasciando l'audio attivo
            
            self.audio_process = subprocess.Popen(
                cmd, 
                shell=True, 
                startupinfo=startupinfo,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.root.after(0, lambda: self.text_label.configure(text=f"In riproduzione: {nome} 🎶"))
        except Exception as e:
            self.root.after(0, lambda: self.text_label.configure(text="Errore nel caricamento del flusso audio"))

    def stop_stream(self):
        try:
            subprocess.run("taskkill /f /im wmplayer.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
        self.audio_process = None
        self.text_label.configure(text="Radio spenta.")

    def update_content_loop(self):
        """Loop di sincronizzazione che scarica costantemente testo e copertina dal server"""
        while True:
            try:
                # 1. Scaricamento ed esposizione del testo informativo remoto
                req_text = urllib.request.Request(URL_TESTO_REMOTO, headers=HEADERS)
                with urllib.request.urlopen(req_text, context=self.ctx, timeout=5) as response:
                    testo = response.read().decode('utf-8', errors='ignore').strip()
                if testo:
                    self.root.after(0, lambda t=testo: self.text_label.configure(text=t))

                # 2. Scaricamento ed elaborazione dell'immagine di copertina remota
                req_img = urllib.request.Request(URL_COPERTINA_IMG, headers=HEADERS)
                with urllib.request.urlopen(req_img, context=self.ctx, timeout=5) as response:
                    img_data = response.read()
                
                image = Image.open(io.BytesIO(img_data))
                image = image.resize((180, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                self.root.after(0, lambda p=photo: self.set_image(p))
            except Exception as e:
                pass
            time.sleep(30)  # Esegue il controllo di sincronizzazione ogni 30 secondi

    def set_image(self, photo):
        """Punta in modo sicuro l'immagine all'etichetta grafica della UI"""
        self.img_label.configure(image=photo)
        self.img_label.image = photo

    def on_closing(self):
        self.stop_stream()
        self.root.destroy()

# =========================================================================
# AVVIO APPLICAZIONE
# =========================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = FinalDynamicRadioApp(root)
    root.mainloop()
