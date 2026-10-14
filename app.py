import tkinter as tk
import customtkinter as ctk
import urllib.request
import threading
import time
import os
import io
import webbrowser
import ssl
from PIL import Image

# Ricostruzione dei link a pezzi per evitare i tagli della chat
URL_BASE_SITO = "https://discovery2radio.it"
CONFIG_URL = URL_BASE_SITO + "/radio_config.txt"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

# Forza il bypass dei controlli di sicurezza SSL rigidi dell'hosting
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class BlindedRadioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Discovery 2 Radio Player")
        self.geometry("450x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Interfaccia Grafica Iniziale
        self.label_title = ctk.CTkLabel(self, text="Discovery 2 Radio Player", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.pack(pady=20)
        
        self.radio_frame = ctk.CTkFrame(self)
        self.radio_frame.pack(pady=10, padx=20, fill="x")
        
        self.image_label = ctk.CTkLabel(self, text="[ Caricamento Copertina... ]")
        self.image_label.pack(pady=20)
        
        self.text_label = ctk.CTkLabel(self, text="Sincronizzazione canali...", wraplength=380, font=ctk.CTkFont(size=14))
        self.text_label.pack(pady=10, padx=10)
        
        # Flussi definitivi delle tue radio ricostruiti al millimetro per evitare alterazioni
        self.config_data = {
            "TITOLO_APP": "Discovery 2 Radio Player",
            "RADIO1_NOME": "DISCOVERY 2 RADIO", 
            "RADIO1_URL": "https://cast5.asurahosting.com/proxy/giancar1/stream ",
            "RADIO2_NOME": "WOLF 1 RADIO", 
            "RADIO2_URL": "http://stream.laut.fm/wolf-one",
            "RADIO3_NOME": "RADIO SOLARIS", 
            "RADIO3_URL": "https://cast6.asurahosting.com/proxy/radiosolaris/stream",
            "RADIO4_NOME": "LAIKA 2 RADIO", 
            "RADIO4_URL": "https://fra-pioneer01.dedicateware.com:3155/stream
",
            "LINK_TESTO": URL_BASE_SITO + "/info.txt",
            "LINK_IMMAGINE": URL_BASE_SITO + "/copertina.jpg"
        }
        
        # Genera i bottoni immediatamente con i dati interni protetti
        self.build_ui_dinamica()
        
        # Tenta l'aggiornamento remoto in background (Testo e Copertina)
        threading.Thread(target=self.load_remote_config, daemon=True).start()

    def load_remote_config(self):
        try:
            req = urllib.request.Request(CONFIG_URL, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
                lines = response.read().decode('utf-8', errors='ignore').splitlines()
                for line in lines:
                    if "=" in line:
                        k, v = line.split("=", 1)
                        self.config_data[k.strip()] = v.strip()
            self.after(0, lambda: self.label_title.configure(text=self.config_data.get("TITOLO_APP")))
        except:
            pass # Se il sito dà 403 o scade, l'app usa comunque i dati interni di emergenza senza bloccarsi
        
        threading.Thread(target=self.update_content_loop, daemon=True).start()

    def build_ui_dinamica(self):
        for i in range(1, 5):
            nome = self.config_data.get(f"RADIO{i}_NOME")
            url = self.config_data.get(f"RADIO{i}_URL")
            btn = ctk.CTkButton(self.radio_frame, text=f"📻 {nome}", command=lambda u=url, n=nome: self.play_stream(u, n))
            btn.pack(pady=6, padx=10, fill="x")

    def play_stream(self, url, nome):
        self.text_label.configure(text=f"In riproduzione: {nome}")
        try:
            webbrowser.open(url)
        except:
            pass

    def update_content_loop(self):
        while True:
            try:
                # Recupero del testo scorrevole
                url_testo = self.config_data.get("LINK_TESTO")
                if url_testo:
                    req_testo = urllib.request.Request(url_testo, headers=HEADERS)
                    with urllib.request.urlopen(req_testo, context=ctx, timeout=5) as r:
                        testo = r.read().decode('utf-8', errors='ignore')
                        self.after(0, lambda t=testo: self.text_label.configure(text=t))
                
                # Recupero e rendering dell'immagine
                url_img = self.config_data.get("LINK_IMMAGINE")
                if url_img:
                    req_img = urllib.request.Request(url_img, headers=HEADERS)
                    with urllib.request.urlopen(req_img, context=ctx, timeout=5) as r:
                        img_data = r.read()
                        img = Image.open(io.BytesIO(img_data))
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 200))
                        self.after(0, lambda ci=ctk_img: self.image_label.configure(image=ci, text=""))
            except:
                pass
            time.sleep(20)

if __name__ == "__main__":
    app = BlindedRadioApp()
    app.mainloop()
