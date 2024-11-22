# Visualizador de Audio en Tiempo Real

Este proyecto es un visualizador de audio interactivo que genera representaciones visuales dinámicas basadas en la entrada de audio del micrófono. Las visualizaciones incluyen formas geométricas que responden al ritmo, frecuencia y amplitud del sonido.

## Características Principales

- 🎤 Captura de audio en tiempo real
- 🎨 Visualización dinámica con formas geométricas
- 🌈 Mapeo de frecuencias a colores
- 📊 Indicador de nivel de audio
- 🔄 Animaciones fluidas y movimientos físicos
- 🎛️ Selección de dispositivo de entrada

## Requisitos Previos

```bash
pip install pyaudio numpy scipy tkinter
```

## Instalación

1. Clona este repositorio:
```bash
git clone [URL del repositorio]
cd visualizador-audio
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Ejecuta el programa:
```bash
python Audio_Forms.py
```

2. Selecciona tu dispositivo de entrada (micrófono) usando el botón "Seleccionar Micrófono"
3. Presiona "Iniciar" para comenzar la visualización
4. Habla o reproduce música para ver las visualizaciones
5. Usa "Detener" para pausar la visualización

## Cómo Funciona

- **Procesamiento de Audio**: 
  - Utiliza PyAudio para capturar audio en tiempo real
  - Aplica un filtro pasa banda (300Hz - 3400Hz) para aislar frecuencias de voz
  - Analiza frecuencias usando transformada de Fourier (FFT)

- **Visualización**:
  - Las frecuencias bajas generan colores cálidos (rojos)
  - Las frecuencias altas generan colores fríos (azules)
  - La amplitud del sonido determina el tamaño de las formas
  - Las formas tienen movimientos físicos y rebotan en los bordes
  - Cada forma tiene una vida útil de 1 segundo

## Controles

- **Seleccionar Micrófono**: Abre un menú para elegir el dispositivo de entrada
- **Iniciar**: Comienza la captura y visualización de audio
- **Detener**: Pausa la visualización
- **Barra de Nivel**: Muestra la intensidad actual del audio

## Especificaciones Técnicas

- **Frecuencia de Muestreo**: 44100 Hz
- **Tamaño del Buffer**: 1024 muestras
- **Rango de Frecuencias**: 300Hz - 3400Hz
- **Formas Disponibles**: Óvalos, Rectángulos, Polígonos

## Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Haz fork del repositorio
2. Crea una nueva rama (`git checkout -b feature/mejora`)
3. Realiza tus cambios
4. Commit tus cambios (`git commit -am 'Añade nueva característica'`)
5. Push a la rama (`git push origin feature/mejora`)
6. Crea un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Agradecimientos

- PyAudio por la captura de audio
- NumPy y SciPy por el procesamiento de señales
- Tkinter por la interfaz gráfica