import tkinter as tk
import urllib.request
import threading
import time
import io
import ssl
import miniaudio  # Libreria integrata nell'eseguibile, non richiede VLC sul PC dell'utente
from PIL import Image, ImageTk

# =========================================================================
# INDIRIZZI FISSI SU GITHUB
# =========================================================================
URL_TESTO_REMOTO = "https://crt.red/2/info.txt"
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
        self.root.geometry("450x650")
        self.root.configure(bg="#1e1e1e")
        
        # Inizializzazione del motore audio e dello stream corrente
        self.audio_device = None
        self.current_stream_thread = None
        self._stop_signal = threading.Event()
        
        # UI Grafica Scura Windows 11
        self.label_title = tk.Label(root, text="RADIO SOLARIS DESKTOP", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e")
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
        r4 = "https://fra-pioneer01.dedicateware.com:3155/stream
        
        self.streams = {
            "DISCOVERY 2 RADIO": r1,
            "WOLF 1 RADIO": r2,
            "RADIO SOLARIS": r3,
            "LAIKA 2 RADIO": r4
        }
        
        self.build_ui()
        threading.Thread(target=self.update_content_loop, daemon=True).start()
        
        # Gestisce la chiusura pulita dell'audio se l'utente chiude la finestra
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_ui(self):
        for nome, url in self.streams.items():
            btn = tk.Button(self.radio_frame, text=f"📻 {nome}", font=("Arial", 11, "bold"), fg="white", bg="#0078d4", activebackground="#005a9e", activeforeground="white", bd=0, height=2, cursor="hand2")
            btn.configure(command=lambda u=url, n=nome: self.play_stream(u, n))
            btn.pack(pady=6, padx=10, fill="x")

    def play_stream(self, url, nome):
        self.text_label.configure(text=f"Connessione a: {nome}...")
        
        # Ferma il flusso precedente se attivo
        self.stop_audio()
        
        # Avvia la riproduzione in un thread separato per non bloccare la grafica della finestra
        self._stop_signal.clear()
        self.current_stream_thread = threading.Thread(target=self._stream_audio_worker, args=(url, nome), daemon=True)
        self.current_stream_thread.start()

    def _stream_audio_worker(self, url, nome):
        try:
            # Apre lo streaming HTTP come un file di dati continuo
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                self.root.after(0, lambda: self.text_label.configure(text=f"In riproduzione: {nome}"))
                
                # Decodifica il flusso MP3 in tempo reale
                dec = miniaudio.StreamDevice()
                # miniaudio leggerà i blocchi di dati man mano che arrivano dal server web
                with miniaudio.decode_client(response) as stream:
                    self.audio_device = miniaudio.PlaybackDevice(output_format=stream.format, sample_rate=stream.sample_rate, channels=stream.nchannels)
                    self.audio_device.start(stream)
                    
                    # Mantiene il thread vivo finché l'utente non cambia stazione o chiude l'app
                    while not self._stop_signal.is_set() and self.audio_device.is_active():
                        time.sleep(0.2)
        except Exception as e:
            self.root.after(0, lambda: self.text_label.configure(text=f"Errore connessione o flusso non supportato"))

    def stop_audio(self):
        self._stop_signal.set()
        if self.audio_device:
            try:
                self.audio_device.stop()
                self.audio_device.close()
            except:
                pass
            self.audio_device = None

    def update_content_loop(self):
        while True:
            # 1. Aggiornamento automatico del Testo da GitHub
            try:
                req_testo = urllib.request.Request(URL_TESTO_REMOTO, headers=HEADERS)
                with urllib.request.urlopen(req_testo, context=ctx, timeout=8) as r:
                    testo = r.read().decode('utf-8', errors='ignore')
                    self.root.after(0, lambda t=testo: self.text_label.configure(text=t))
            except:
                pass
                
            # 2. Aggiornamento automatico dell'Immagine di copertina (Scarica direttamente il JPG)
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
        self.stop_audio()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FinalDynamicRadioApp(root)
    root.mainloop()
