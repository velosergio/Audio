import pyaudio
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from scipy.signal import butter, lfilter
import colorsys
import time
import math

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

        # Lista para rastrear las formas, sus tiempos de creación y movimientos
        self.shapes = []

        # Rango de frecuencias de interés (voz humana)
        self.low_freq = 300
        self.high_freq = 3400

        # Ajustar estos valores para mejor rendimiento
        self.max_shapes = 15  # Limitar número máximo de formas
        self.particle_density = 20  # Reducir densidad de partículas
        self.update_interval = 50  # Ajustar intervalo de actualización (ms)
        
        # Buffer para formas
        self.shape_buffer = []

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

    def create_particle_effect(self, x, y, size, color, noise_density=0.3):
        """Versión optimizada del efecto de partículas"""
        points = []
        # Reducir número de partículas
        num_particles = int(size * 5)  # Reducido de 10 a 5
        
        for _ in range(min(num_particles, self.particle_density)):
            angle = np.random.uniform(0, 2 * np.pi)
            distance = np.random.normal(size/2, size/4)
            px = x + distance * np.cos(angle)
            py = y + distance * np.sin(angle)
            if np.random.random() < noise_density:
                points.append((px, py))
        
        # Crear partículas en grupo en lugar de individualmente
        particles = []
        for px, py in points:
            particles.extend([px-1, py-1, px+1, py+1])
        
        if particles:
            return self.canvas.create_polygon(particles, fill=color, outline='', stipple='gray50')
        return None

    def create_glowing_circle(self, x, y, size, color):
        """Versión optimizada del efecto de resplandor"""
        # Reducir número de capas de resplandor
        shapes = []
        for i in range(3):  # Reducido de 5 a 3 capas
            expanded_size = size * (1 + i * 0.3)
            alpha = 0.3 - (i * 0.1)
            glow_color = self.adjust_color_alpha(color, alpha)
            
            shape = self.canvas.create_oval(
                x - expanded_size, y - expanded_size,
                x + expanded_size, y + expanded_size,
                fill=glow_color, outline='',
                stipple='gray25'
            )
            shapes.append(shape)
        return shapes

    def adjust_color_alpha(self, color, alpha):
        """Ajusta la transparencia de un color"""
        # Convertir color hex a RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Ajustar valores según alpha
        r = int(r * alpha + 255 * (1-alpha))
        g = int(g * alpha + 255 * (1-alpha))
        b = int(b * alpha + 255 * (1-alpha))
        
        return f'#{r:02x}{g:02x}{b:02x}'

    def update_visualization(self):
        if not self.is_running:
            return

        # Limitar procesamiento de audio
        try:
            data = self.stream.read(1024, exception_on_overflow=False)
            data_int = np.frombuffer(data, dtype=np.int16)
            filtered_data = self.bandpass_filter(data_int, self.low_freq, self.high_freq, 44100, order=6)
        except:
            return

        # Reducir cálculos FFT
        fft_data = np.abs(np.fft.fft(filtered_data))[:256]  # Reducido de 512 a 256
        freqs = np.fft.fftfreq(len(fft_data), 1/44100)[:256]
        
        # Limitar número de formas activas
        if len(self.shapes) >= self.max_shapes:
            oldest_shape = self.shapes.pop(0)
            self.canvas.delete(oldest_shape['id'])

        # Análisis de audio similar al anterior
        idx = np.argmax(fft_data)
        dominant_freq = abs(freqs[idx])
        dominant_freq = min(max(dominant_freq, self.low_freq), self.high_freq)
        
        # Crear colores más complejos
        freq_normalized = (dominant_freq - self.low_freq) / (self.high_freq - self.low_freq)
        primary_hue = freq_normalized * 360
        secondary_hue = (primary_hue + 180) % 360  # Color complementario
        
        primary_color = self.hsv_to_hex(primary_hue/360, 0.8, 0.9)
        secondary_color = self.hsv_to_hex(secondary_hue/360, 0.7, 0.8)
        
        # Calcular tamaños y parámetros basados en el audio
        level = np.abs(filtered_data).mean()
        base_size = max(20, int(level / 10))
        num_points = np.random.randint(5, 12)  # Número variable de puntos
        
        # Posición central aleatoria
        x_center = np.random.randint(0, self.canvas.winfo_width())
        y_center = np.random.randint(0, self.canvas.winfo_height())
        
        # Seleccionar tipo de forma aleatoria
        shape_type = np.random.choice([
            'glow_circle',
            'particle_cloud',
            'striped_circle',
            'noise_sphere'
        ], p=[0.3, 0.3, 0.2, 0.2])
        
        # Generar movimiento más complejo (mover esto ANTES de crear las formas)
        angle = np.random.uniform(0, 2*np.pi)
        speed = np.random.uniform(2, 5)
        dx = speed * np.cos(angle)
        dy = speed * np.sin(angle)

        # Variable para almacenar el ID de la forma principal
        shape = None

        if shape_type == 'glow_circle':
            # Crear el círculo principal y guardar su ID
            shape = self.canvas.create_oval(
                x_center - base_size, y_center - base_size,
                x_center + base_size, y_center + base_size,
                fill=primary_color, outline=''
            )
            self.create_glowing_circle(x_center, y_center, base_size, primary_color)
            self.create_particle_effect(x_center, y_center, base_size/2, secondary_color)
            
        elif shape_type == 'particle_cloud':
            # Crear un grupo de partículas y guardar el ID de la primera
            shape = self.canvas.create_oval(
                x_center - base_size/2, y_center - base_size/2,
                x_center + base_size/2, y_center + base_size/2,
                fill=primary_color, outline=''
            )
            for _ in range(5):
                offset_x = x_center + np.random.normal(0, base_size/3)
                offset_y = y_center + np.random.normal(0, base_size/3)
                self.create_particle_effect(offset_x, offset_y, base_size/3, primary_color)
                
        elif shape_type == 'striped_circle':
            # Crear el círculo principal con líneas
            shape = self.canvas.create_oval(
                x_center - base_size, y_center - base_size,
                x_center + base_size, y_center + base_size,
                outline=primary_color, width=2
            )
            for i in range(0, 360, 20):
                angle = math.radians(i)
                x1 = x_center + base_size * math.cos(angle)
                y1 = y_center + base_size * math.sin(angle)
                self.canvas.create_line(
                    x_center, y_center, x1, y1,
                    fill=primary_color,
                    width=2,
                    stipple='gray50'
                )
            self.create_glowing_circle(x_center, y_center, base_size/2, secondary_color)
            
        elif shape_type == 'noise_sphere':
            # Crear la esfera principal
            shape = self.canvas.create_oval(
                x_center - base_size/2, y_center - base_size/2,
                x_center + base_size/2, y_center + base_size/2,
                fill=primary_color, outline=''
            )
            for _ in range(50):
                angle = np.random.uniform(0, 2 * np.pi)
                radius = np.random.normal(base_size/2, base_size/6)
                x = x_center + radius * np.cos(angle)
                y = y_center + radius * np.sin(angle)
                size = np.random.uniform(2, 6)
                self.create_particle_effect(x, y, size, primary_color, noise_density=0.5)

        # Verificar que shape está definido antes de añadirlo
        if shape is not None:
            self.shapes.append({
                'id': shape,
                'time': time.time(),
                'dx': dx,
                'dy': dy,
                'rotation': np.random.uniform(-5, 5),
                'scale_factor': 1.0,
                'scale_direction': np.random.choice([-1, 1])
            })

        # Optimizar actualización de movimiento
        self.move_shapes_optimized()

        # Actualizar barra de nivel
        self.level_canvas.delete("all")
        self.level_canvas.create_rectangle(0, 0, level / 50, 20, fill=primary_color)

        self.master.after(self.update_interval, self.update_visualization)

    def move_shapes_optimized(self):
        current_time = time.time()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Procesar formas en lote
        shapes_to_remove = []
        
        for shape_info in self.shapes:
            shape_id = shape_info['id']
            
            # Mover forma
            self.canvas.move(shape_id, shape_info['dx'], shape_info['dy'])
            
            # Verificar bordes
            bbox = self.canvas.bbox(shape_id)
            if bbox:
                if bbox[0] <= 0 or bbox[2] >= canvas_width:
                    shape_info['dx'] *= -1
                if bbox[1] <= 0 or bbox[3] >= canvas_height:
                    shape_info['dy'] *= -1
            
            # Marcar para eliminación si es antigua
            if current_time - shape_info['time'] > 1.5:
                shapes_to_remove.append(shape_info)
        
        # Eliminar formas en lote
        for shape_info in shapes_to_remove:
            self.canvas.delete(shape_info['id'])
            self.shapes.remove(shape_info)

    def hsv_to_hex(self, h, s, v):
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))

    def on_closing(self):
        self.stop_stream()
        self.p.terminate()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioVisualizer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
