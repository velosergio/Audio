import pyaudio
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from scipy.signal import butter, lfilter
import colorsys
import time
import random

class AudioVisualizer:
    def __init__(self, master):
        self.master = master
        self.master.title("Visualizador de Audio")
        self.is_running = False

        # Configuración de PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.device_index = None

        # Dimensiones de la ventana
        self.width = 800
        self.height = 600

        # Interfaz gráfica
        self.create_widgets()

        # Lista para rastrear los trazos, sus tiempos de creación y movimientos
        self.shapes = []

        # Rango de frecuencias de interés (voz humana)
        self.low_freq = 300
        self.high_freq = 3400

        # Definir colores (6 colores en un arreglo)
        self.colores = [
            (255, 99, 71),    # Tomato
            (30, 144, 255),   # DodgerBlue
            (34, 139, 34),    # ForestGreen
            (255, 215, 0),    # Gold
            (138, 43, 226),   # BlueViolet
            (220, 20, 60)     # Crimson
        ]

        # Tiempo para cambiar la orientación
        self.last_orientation_change = time.time()
        self.current_orientation = "horizontal"

    def create_widgets(self):
        # Frame principal
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas para visualización (80% de la altura)
        self.canvas = tk.Canvas(self.main_frame, bg='white')
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Frame para controles
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.select_button = ttk.Button(self.control_frame, text="Seleccionar Micrófono", command=self.select_device)
        self.select_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.start_button = ttk.Button(self.control_frame, text="Iniciar", command=self.start_stream)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_button = ttk.Button(self.control_frame, text="Detener", command=self.stop_stream)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Barra de nivel de audio
        self.level_canvas = tk.Canvas(self.control_frame, width=200, height=20, bg='white')
        self.level_canvas.pack(side=tk.RIGHT, padx=5, pady=5)

    def select_device(self):
        devices = []
        for i in range(self.p.get_device_count()):
            devices.append(self.p.get_device_info_by_index(i)['name'])

        self.device_window = tk.Toplevel(self.master)
        self.device_window.title("Seleccionar Dispositivo")

        self.device_listbox = tk.Listbox(self.device_window)
        for device in devices:
            self.device_listbox.insert(tk.END, device)
        self.device_listbox.pack()

        select_btn = ttk.Button(self.device_window, text="Seleccionar", command=self.set_device)
        select_btn.pack()

    def set_device(self):
        selection = self.device_listbox.curselection()
        if selection:
            self.device_index = selection[0]
            self.device_window.destroy()
        else:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un dispositivo.")

    def start_stream(self):
        if self.device_index is None:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un micrófono primero.")
            return

        self.is_running = True
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=44100,
                                  input=True,
                                  input_device_index=self.device_index,
                                  frames_per_buffer=1024)

        self.update_visualization()

    def stop_stream(self):
        if self.stream is not None:
            self.is_running = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    # Función para aplicar filtro pasa banda
    def bandpass_filter(self, data, lowcut, highcut, fs, order=5):
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        y = lfilter(b, a, data)
        return y

    def update_visualization(self):
        if not self.is_running:
            return

        current_time = time.time()
        if current_time - self.last_orientation_change > 5:
            # Cambiar la orientación y tipo de trazo cada 5 segundos
            self.current_orientation = random.choice(["horizontal", "vertical", "diagonal", "curvo"])
            self.last_orientation_change = current_time

        data = self.stream.read(1024, exception_on_overflow=False)
        data_int = np.frombuffer(data, dtype=np.int16)

        # Aplicar filtro pasa banda para capturar solo la voz
        filtered_data = self.bandpass_filter(data_int, self.low_freq, self.high_freq, 44100, order=6)

        # FFT para obtener frecuencias
        fft_data = np.abs(np.fft.fft(filtered_data))[:512]
        freqs = np.fft.fftfreq(len(fft_data), 1/44100)[:512]

        # Obtener frecuencia dominante dentro del rango de interés
        idx = np.argmax(fft_data)
        dominant_freq = abs(freqs[idx])

        # Asegurar que la frecuencia dominante esté dentro del rango
        dominant_freq = min(max(dominant_freq, self.low_freq), self.high_freq)

        # Elegir un color aleatorio del arreglo
        color = random.choice(self.colores)
        color_hex = self.rgb_to_hex(color)

        # Calcular nivel de amplitud para determinar tamaño y movimiento
        level = np.abs(filtered_data).mean()
        size = max(10, int(level / 20))  # Ajustar tamaño según amplitud, mínimo 10

        # Dibujar trazos según la orientación actual
        x0 = np.random.randint(0, self.canvas.winfo_width())
        y0 = np.random.randint(0, self.canvas.winfo_height())

        if self.current_orientation == "horizontal":
            self.canvas.create_line(x0, y0, x0 + size, y0, fill=color_hex, width=random.randint(8, 15))
        elif self.current_orientation == "vertical":
            self.canvas.create_line(x0, y0, x0, y0 + size, fill=color_hex, width=random.randint(8, 15))
        elif self.current_orientation == "diagonal":
            self.canvas.create_line(x0, y0, x0 + size, y0 + size, fill=color_hex, width=random.randint(8, 15))
        elif self.current_orientation == "curvo":
            control_x = x0 + random.randint(-size, size)
            control_y = y0 + random.randint(-size, size)
            self.canvas.create_line(x0, y0, control_x, control_y, x0 + size, y0 + size, smooth=True, fill=color_hex, width=random.randint(8, 15))

        # Barra de nivel de audio
        self.level_canvas.delete("all")
        self.level_canvas.create_rectangle(0, 0, level / 50, 20, fill="green")

        self.master.after(50, self.update_visualization)

    def rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

    def on_closing(self):
        self.stop_stream()
        self.p.terminate()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioVisualizer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()