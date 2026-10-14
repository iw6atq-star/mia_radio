import tkinter as tk
import customtkinter as ctk
import urllib.request
import threading
import time
import os
import io
from PIL import Image

CONFIG_URL = "https://discovery2radio.it"

class BlindedRadioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("WebRadio Player")
        self.geometry("450x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Interfaccia Grafica Iniziale
        self.label_title = ctk.CTkLabel(self, text="Caricamento canali...", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.pack(pady=20)
        
        self.radio_frame = ctk.CTkFrame(self)
        self.radio_frame.pack(pady=10, padx=20, fill="x")
        
        self.image_label = ctk.CTkLabel(self, text="[ In attesa della copertina ]")
        self.image_label.pack(pady=20)
        
        self.text_label = ctk.CTkLabel(self, text="Connessione al server...", wraplength=380, font=ctk.CTkFont(size=14))
        self.text_label.pack(pady=10, padx=10)
        
        self.config_data = {}
        
        # Avvia il caricamento della configurazione da remoto
        threading.Thread(target=self.load_remote_config, daemon=True).start()

    def load_remote_config(self):
        try:
            with urllib.request.urlopen(CONFIG_URL, timeout=10) as response:
                lines = response.read().decode('utf-8').splitlines()
                for line in lines:
                    if "=" in line:
                        k, v = line.split("=", 1)
                        self.config_data[k.strip()] = v.strip()
            self.after(0, self.build_ui_dinamica)
        except Exception as e:
            self.after(0, lambda: self.text_label.configure(text=f"Errore di connessione: {e}"))

    def build_ui_dinamica(self):
        self.label_title.configure(text=self.config_data.get("TITOLO_APP", "Radio Player"))
        
        # Crea i 4 bottoni con i nomi presi dal tuo sito
        for i in range(1, 5):
            nome = self.config_data.get(f"RADIO{i}_NOME", f"Radio {i}")
            url = self.config_data.get(f"RADIO{i}_URL", "")
            if url:
                btn = ctk.CTkButton(self.radio_frame, text=f"📻 {nome}", command=lambda u=url, n=nome: self.play_stream(u, n))
                btn.pack(pady=6, padx=10, fill="x")
                
        # Avvia il loop di aggiornamento per Testo e Immagine (ogni 20 secondi)
        threading.Thread(target=self.update_content_loop, daemon=True).start()

    def play_stream(self, url, nome):
        self.text_label.configure(text=f"In riproduzione: {nome}")
        # Usa il player di Windows integrato a riga di comando per lo stream (invisibile ed efficace)
        try:
            os.system(f"start /min wmplayer \"{url}\"")
        except:
            pass

    def update_content_loop(self):
        while True:
            try:
                # Aggiorna Testo
                url_testo = self.config_data.get("LINK_TESTO")
                if url_testo:
                    with urllib.request.urlopen(url_testo, timeout=5) as r:
                        testo = r.read().decode('utf-8', errors='ignore')
                        self.after(0, lambda t=testo: self.text_label.configure(text=t))
                
                # Aggiorna Immagine
                url_img = self.config_data.get("LINK_IMMAGINE")
                if url_img:
                    with urllib.request.urlopen(url_img, timeout=5) as r:
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
