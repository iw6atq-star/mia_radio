import tkinter as tk
import urllib.request
import threading
import time
import io
import webbrowser
import ssl
from PIL import Image, ImageTk

# =========================================================================
# I TUOI DUE INDIRIZZI FISSI SU GITHUB (IMBLOCCABILI DA CLOUDFLARE)
# =========================================================================
URL_TESTO_REMOTO = "https://raw.githubusercontent.com/iw6atq-star/mia_radio/refs/heads/main/info.txt"

# Incolla tra le virgolette il link RAW del tuo file copertina.txt
URL_COPERTINA_TXT = "https://raw.githubusercontent.com/iw6atq-star/mia_radio/refs/heads/main/copertina.txt"
# =========================================================================

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class FinalDynamicRadioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Discovery 2 Radio Player")
        self.root.geometry("450x650")
        self.root.configure(bg="#1e1e1e")
        
        # UI Grafica Scura Windows 11
        self.label_title = tk.Label(root, text="Discovery 2 Radio Player", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e")
        self.label_title.pack(pady=20)
        
        self.radio_frame = tk.Frame(root, bg="#1e1e1e")
        self.radio_frame.pack(pady=10, padx=20, fill="x")
        
        self.image_label = tk.Label(root, text="[ Caricamento Copertina... ]", fg="gray", bg="#1e1e1e")
        self.image_label.pack(pady=20)
        
        self.text_label = tk.Label(root, text="Sincronizzazione contenuti...", font=("Arial", 11), fg="white", bg="#1e1e1e", wraplength=380)
        self.text_label.pack(pady=10, padx=10)
        
        # Flussi streaming reali delle tue radio
        r1 = "https://cast5.asurahosting.com/proxy/giancar1/stream"
        r2 = "http://stream.laut.fm/wolf-one"
        r3 = "https://cast6.asurahosting.com/proxy/radiosolaris/stream"
        r4 = "https://fra-pioneer01.dedicateware.com:3155/stream"
        
        self.streams = {
            "DISCOVERY 2 RADIO": r1,
            "WOLF 1 RADIO": r2,
            "RADIO SOLARIS": r3,
            "LAIKA 2 RADIO": r4
        }
        
        self.last_image_url = ""
        self.build_ui()
        threading.Thread(target=self.update_content_loop, daemon=True).start()

    def build_ui(self):
        for nome, url in self.streams.items():
            btn = tk.Button(self.radio_frame, text=f"📻 {nome}", font=("Arial", 11, "bold"), fg="white", bg="#0078d4", activebackground="#005a9e", activeforeground="white", bd=0, height=2, cursor="hand2")
            btn.configure(command=lambda u=url, n=nome: self.play_stream(u, n))
            btn.pack(pady=6, padx=10, fill="x")

    def play_stream(self, url, nome):
        self.text_label.configure(text=f"In riproduzione: {nome}")
        try:
            webbrowser.open(url)
        except:
            pass

    def update_content_loop(self):
        while True:
            # 1. Aggiornamento automatico del Testo da GitHub (info.txt)
            try:
                req_testo = urllib.request.Request(URL_TESTO_REMOTO, headers=HEADERS)
                with urllib.request.urlopen(req_testo, context=ctx, timeout=8) as r:
                    testo = r.read().decode('utf-8', errors='ignore')
                    self.root.after(0, lambda t=testo: self.text_label.configure(text=t))
            except:
                pass
                
            # 2. Aggiornamento automatico dell'Immagine leggendo il link dentro copertina.txt
            try:
                req_link_img = urllib.request.Request(URL_COPERTINA_TXT, headers=HEADERS)
                with urllib.request.urlopen(req_link_img, context=ctx, timeout=8) as r_link:
                    real_img_url = r_link.read().decode('utf-8', errors='ignore').strip()
                    
                    if real_img_url and real_img_url != self.last_image_url:
                        self.last_image_url = real_img_url
                        req_img = urllib.request.Request(real_img_url, headers=HEADERS)
                        with urllib.request.urlopen(req_img, context=ctx, timeout=8) as r_img:
                            img_data = r_img.read()
                            img = Image.open(io.BytesIO(img_data))
                            img = img.resize((200, 200), Image.Resampling.LANCZOS)
                            ctk_img = ImageTk.PhotoImage(img)
                            self.root.after(0, lambda ci=ctk_img: self.image_label.configure(image=ci, text=""))
                            self.image_label.image = ctk_img
            except:
                pass
                
            time.sleep(15) # Ricontrolla tutto ogni 15 secondi automaticamente

if __name__ == "__main__":
    root = tk.Tk()
    app = FinalDynamicRadioApp(root)
    root.mainloop()
