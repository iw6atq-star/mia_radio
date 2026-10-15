import tkinter as tk
import urllib.request
import threading
import time
import io
import ssl
import subprocess  # Avvia flussi e file web usando il motore nativo di Windows
from PIL import Image, ImageTk

# =========================================================================
# IMPOSTA QUI I TUOI INDIRIZZI FISSI ESTERNI (SOSTITUISCI I LINK D'ESEMPIO)
# =========================================================================
URL_TESTO_REMOTO = "https://www.crt.red/2/info.txt"
URL_COPERTINA_IMG = "https://www.crt.red/2/copertina.jpg"
# =========================================================================

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class FinalDynamicRadioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RADIO SOLARIS DESKTOP")
        self.root.geometry("450x680") # Aumentata leggermente l'altezza per far spazio al quinto bottone
        self.root.configure(bg="#1e1e1e")
        
        # Gestore per tracciare il processo audio attivo
        self.audio_process = None
        
        # UI Grafica Scura Windows 11
        self.label_title = tk.Label(root, text="RADIO SOLARIS DESKTOP", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e")
        self.label_title.pack(pady=20)
        
        self.radio_frame = tk.Frame(root, bg="#1e1e1e")
        self.radio_frame.pack(pady=10, padx=20, fill="x")
        
        self.image_label = tk.Label(root, text="[ Caricamento Copertina... ]", fg="gray", bg="#1e1e1e")
        self.image_label.pack(pady=20)
        
        self.text_label = tk.Label(root, text="Sincronizzazione contenuti...", font=("Arial", 11), fg="white", bg="#1e1e1e", wraplength=380)
        self.text_label.pack(pady=10, padx=10)
        
        # Sostituisci questi indirizzi d'esempio con i tuoi link reali completi
        r1 = "https://cast5.asurahosting.com/proxy/giancar1/stream"
        r2 = "http://stream.laut.fm/wolf-one"
        r3 = "https://cast6.asurahosting.com/proxy/radiosolaris/stream"
        r4 = "https://fra-pioneer01.dedicateware.com:3155/stream"
        r5 = "https://www.crt.red/2/A.mp3"  # <--- Il tuo file MP3 fisso sul web
        
        self.streams = {
            "DISCOVERY 2 RADIO": r1,
            "WOLF 1 RADIO": r2,
            "RADIO SOLARIS": r3,
            "LAIKA 2 RADIO": r4,
            "STAZIONE MP3 WEB": r5  # Nuova stazione aggiunta
        }
        
        self.build_ui()
        threading.Thread(target=self.update_content_loop, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_ui(self):
        for nome, url in self.streams.items():
            btn = tk.Button(self.radio_frame, text=f"📻 {nome}", font=("Arial", 11, "bold"), fg="white", bg="#0078d4", activebackground="#005a9e", activeforeground="white", bd=0, height=2, cursor="hand2")
            btn.configure(command=lambda u=url, n=nome: self.play_stream(u, n))
            btn.pack(pady=5, padx=10, fill="x")
            
        # Bottone STOP dedicato
        btn_stop = tk.Button(self.root, text="⏹️ FERMA RADIO", font=("Arial", 11, "bold"), fg="white", bg="#d32f2f", activebackground="#9a0007", activeforeground="white", bd=0, height=2, cursor="hand2")
        btn_stop.configure(command=self.stop_stream)
        btn_stop.pack(pady=15, padx=30, fill="x")

    def play_stream(self, url, nome):
        self.text_label.configure(text=f"Apertura: {nome}...")
        self.stop_stream()
        
        # Avvia lo streaming o il file MP3 tramite Windows Media Player in modalità background invisibile
        try:
            cmd = f'wmplayer.exe "{url}" /play /close'
            self.audio_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.text_label.configure(text=f"In riproduzione: {nome}")
        except:
            self.text_label.configure(text="Errore: Contenuto non disponibile")

    def stop_stream(self):
        # Chiude in modo forzato qualsiasi istanza di Windows Media Player aperta in background
        try:
            subprocess.run("taskkill /f /im wmplayer.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
        self.audio_process = None
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
