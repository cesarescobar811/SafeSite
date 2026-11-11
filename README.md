# SafeSite

**Sistema de monitoreo de Equipo de Protección Personal (EPP) en tiempo real para el sector construcción.**

Universidad Gerardo Barrios · Facultad de Ciencias y Tecnología · Ingeniería en Sistemas y Redes Informáticas

## Integrantes

| Nombre completo | Carnet |
|---|---|
| César Alejandro Escobar Recinos | [Carnet] |
| [Nombre del integrante 2] | [Carnet] |
| [Nombre del integrante 3] | [Carnet] |

## Descripción

SafeSite es una aplicación de escritorio que usa una **cámara web** y **visión por computadora** para
detectar personas en tiempo real y comprobar si llevan **casco y chaleco**. Si detecta una infracción:

- marca a la persona con un recuadro **rojo** y el texto `ALERTA: FALTA EPP`;
- activa una **alarma sonora continua** que se detiene cuando el equipo se regulariza;
- guarda una **captura JPG** y registra el evento en una base de datos **SQLite** (`infracciones.db`)
  con id, fecha y hora, tipo de falta y ruta de la captura.

Cuando se cumple la norma, el recuadro es **verde** (`EPP COMPLETO`). Está pensado para equipos
**sin tarjeta gráfica dedicada** (YOLOv8n, imágenes de 320 px y salto de fotogramas) y procesa todo de
forma local. La documentación completa (objetivos, delimitación, justificación de tecnologías y
requerimientos) está en [`docs/SafeSite_Documento_Proyecto.pdf`](docs/SafeSite_Documento_Proyecto.pdf).

## Prototipo inicial (funcionalidad central)

La interfaz (PyQt6) tiene tres secciones:

- **Monitoreo en vivo:** video con detecciones, banner de estado, indicadores (cámara, personas, con y
  sin EPP, FPS, alarma), actividad reciente, botón de iniciar/detener y silenciar alarma.
- **Historial:** tabla de infracciones leída de SQLite con miniaturas, búsqueda, filtro por tipo,
  vista previa de la captura y exportación a CSV.
- **Ajustes:** cámara, resolución, modelo, tamaño de imagen, confianza, salto de fotogramas, alarma,
  volumen, carpeta de capturas y tema claro/oscuro (se guardan entre sesiones).

> **Nota sobre la detección.** El modelo estándar `yolov8n.pt` detecta *personas*, pero no cascos ni
> chalecos. Por eso el prototipo verifica el EPP por el **color** de la zona de la cabeza y del torso
> (colores de alta visibilidad). Funciona bien en una demostración con buena iluminación, pero puede
> fallar con otros colores o poca luz. Si se coloca un modelo entrenado en EPP en `models/` y se elige en
> *Ajustes → Modelo*, el sistema lo detecta y lo usa automáticamente.

## Instalación

Requiere **Python 3.10 o superior**.

```bash
# 1. Clonar el repositorio
git clone <URL-DEL-REPOSITORIO>
cd SafeSite

# 2. Crear y activar el entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt
```

La primera vez que se inicia el monitoreo, Ultralytics descarga `yolov8n.pt` automáticamente.
Se usa `pygame-ce` (compatible con `import pygame`) porque `pygame` puede fallar al compilarse en
versiones recientes de Python en Windows.

## Ejecución

```bash
python app.py
```

En la sección **Monitoreo en vivo**, pulsa **Iniciar monitoreo**. Para probar una infracción, muéstrate
a la cámara sin casco ni chaleco de colores vivos (amarillo, naranja, verde fluorescente); al ponerte
un casco amarillo y un chaleco de alta visibilidad, el recuadro pasa a verde y la alarma se detiene.

## Pruebas automáticas

No requieren cámara ni descargar el modelo:

```bash
python -m unittest discover -s tests -v
```

## Estructura del repositorio

```
SafeSite/
├── app.py                      # punto de entrada
├── requirements.txt
├── docs/                       # documento PDF y script para regenerarlo
├── models/                     # (opcional) modelos entrenados en EPP
├── capturas/                   # fotos de las infracciones (se crea sola)
├── tests/                      # pruebas automáticas
└── safesite/
    ├── config.py               # constantes y ajustes por defecto
    ├── nucleo/                 # detector, alarma, dibujo e hilo de video
    ├── datos/                  # acceso a SQLite
    └── ui/                     # ventana principal, vistas, componentes y estilos
```

## Flujo de trabajo colaborativo (Git)

- La rama `main` solo recibe código revisado. Cada integrante trabaja en su propia rama
  (`feature/<tarea>`) y la integra mediante *pull request* con revisión de al menos un compañero.
- Mensajes de *commit* claros y en presente: `Agrega filtro por tipo en el historial`.
- Antes de hacer *push*, ejecutar las pruebas automáticas.
- Actualizar el PDF si cambian los requerimientos: editar `docs/integrantes.json` o
  `docs/generar_documento.py` y ejecutar `python docs/generar_documento.py` (requiere `reportlab`).

## Licencia y uso

Proyecto académico. Uso educativo.
