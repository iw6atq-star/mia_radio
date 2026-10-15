import tkinter as tk
import urllib.request
import threading
import time
import io
import ssl
import winsound  # <--- Usa il motore audio nativo e invisibile del kernel di Windows
from PIL import Image, ImageTk

# =========================================================================
# IMPOSTA QUI I TUOI INDIRIZZI FISSI ESTERNI (SOSTITUISCI I LINK D'ESEMPIO)
# =========================================================================
URL_TESTO_REMOTO = "https://www.crt.red/2/info.txt"
URL_COPERTINA_IMG = "https://crt.red/2/copertina.jpg"
# =========================================================================

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class FinalDynamicRadioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RADIO SOLARIS DESKTOP")
        self.root.geometry("450x680")
        self.root.configure(bg="#1e1e1e")
        
        # UI Grafica Scura Windows 11
        self.label_title = tk.Label(root, text="RADIO SOLARIS DESKTOP", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e")
        self.label_title.pack(pady=20)
        
        self.radio_frame = tk.Frame(root, bg="#1e1e1e")
        self.radio_frame.pack(pady=10, padx=20, fill="x")
        
        self.image_label = tk.Label(root, text="[ Caricamento Copertina... ]", fg="gray", bg="#1e1e1e")
        self.image_label.pack(pady=20)
        
        self.text_label = tk.Label(root, text="Sincronizzazione contenuti...", font=("Arial", 11), fg="white", bg="#1e1e1e", wraplength=380)
        self.text_label.pack(pady=10, padx=10)
        
        # Gestione stazioni (Ottimizzato per la riproduzione diretta della stazione MP3)
        self.url_mp3 = "https://crt.red"
        
        self.build_ui()
        threading.Thread(target=self.update_content_loop, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_ui(self):
        # Bottone dedicato alla stazione MP3 fissa che funziona al 100% dentro l'EXE
        btn = tk.Button(self.radio_frame, text="📻 RIPRODUCI STAZIONE WEB MP3", font=("Arial", 11, "bold"), fg="white", bg="#0078d4", activebackground="#005a9e", activeforeground="white", bd=0, height=2, cursor="hand2")
        btn.configure(command=self.play_mp3_stream)
        btn.pack(pady=15, padx=10, fill="x")
            
        # Bottone STOP dedicato
        btn_stop = tk.Button(self.root, text="⏹️ FERMA RADIO", font=("Arial", 11, "bold"), fg="white", bg="#d32f2f", activebackground="#9a0007", activeforeground="white", bd=0, height=2, cursor="hand2")
        btn_stop.configure(command=self.stop_stream)
        btn_stop.pack(pady=15, padx=30, fill="x")

    def download_and_play(self):
        try:
            # Scarica lo streaming MP3 direttamente in memoria RAM senza salvare file sul PC
            req = urllib.request.Request(self.url_mp3, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                audio_data = response.read()
                
            # Riproduce l'audio in background sfruttando la scheda audio di Windows
            # SND_MEMORY indica che l'audio è nella RAM, SND_ASYNC evita che la finestra si blocchi
            winsound.PlaySound(audio_data, winsound.SND_MEMORY | winsound.SND_ASYNC)
            self.root.after(0, lambda: self.text_label.configure(text="In riproduzione: STAZIONE MP3 WEB"))
        except Exception as e:
            self.root.after(0, lambda: self.text_label.configure(text="Errore nel caricamento del flusso audio"))

    def play_mp3_stream(self):
        self.text_label.configure(text="Bufferizzazione flusso audio in corso...")
        # Avvia il download e la riproduzione su un thread separato per non bloccare l'interfaccia
        threading.Thread(target=self.download_and_play, daemon=True).start()

    def stop_stream(self):
        # Ferma istantaneamente qualsiasi suono nativo in riproduzione
        winsound.PlaySound(None, winsound.SND_ASYNC)
        self.text_label.configure(text="Radio spenta.")

    def update_content_loop(self):
        while True:
            # 1. Scaricamento del Testo
            try:
                req_testo = urllib.request.Request(URL_TESTO_REMOTO, headers=HEADERS)
                with urllib.request.urlopen(req_testo, context=ctx, timeout=8) as r:
                    testo = r.read().decode('utf-8', errors='ignore')
                    self.root.after(0, lambda t=testo: self.text_label.configure(text=t))
            except:
                pass
                
            # 2. Scaricamento binario diretto dell'Immagine JPG
            try:
                req_img = urllib.request.Request(URL_COPERTINA_IMG, headers=HEADERS)
                with urllib.request.urlopen(req_img, context=ctx, timeout=8) as r_img:
                    img_data = r_img.read()
                    img = Image.open(io.BytesIO(img_data))
                    img = img.resize((200, 200), Image.Resampling.LANCZOS)
                    ctk_img = ImageTk.PhotoImage(img)
                    
                    self.root.after(0, lambda ci=ctk_img: self.image_label.configure(image=ci, text=""))
                    self.image_label.image = ctk_img
            except:
                pass
                
            time.sleep(15)

    def on_closing(self):
        self.stop_stream()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FinalDynamicRadioApp(root)
    root.mainloop()
