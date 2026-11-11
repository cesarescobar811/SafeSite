"""generar_documento.py - Genera docs/SafeSite_Documento_Proyecto.pdf

Los datos de la portada (integrantes, carnets, asignatura, docente, fecha) se leen de
docs/integrantes.json. Para actualizar el PDF:

    pip install reportlab
    python docs/generar_documento.py
"""
import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Frame, PageBreak, PageTemplate, Paragraph,
    Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "integrantes.json")
SALIDA = os.path.join(AQUI, "SafeSite_Documento_Proyecto.pdf")

AZUL_OSCURO = colors.HexColor("#12233f")
AZUL = colors.HexColor("#2563eb")
AZUL_CLARO = colors.HexColor("#c7d2fe")
TEXTO = colors.HexColor("#1f2937")
GRIS = colors.HexColor("#6b7280")
FILA = colors.HexColor("#f1f5f9")
BORDE = colors.HexColor("#d1d5db")

ANCHO_PAGINA, ALTO_PAGINA = letter
MARGEN = 2.5 * cm
ANCHO_UTIL = ANCHO_PAGINA - 2 * MARGEN


# ----------------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------------
_base = ParagraphStyle("base", fontName="Helvetica", fontSize=10.5, leading=15.5,
                       textColor=TEXTO, alignment=TA_JUSTIFY, spaceAfter=7)
E = {
    "cuerpo": _base,
    "H1": ParagraphStyle("H1", parent=_base, fontName="Helvetica-Bold", fontSize=18,
                         leading=22, textColor=AZUL_OSCURO, alignment=TA_LEFT,
                         spaceBefore=4, spaceAfter=10, keepWithNext=1),
    "H2": ParagraphStyle("H2", parent=_base, fontName="Helvetica-Bold", fontSize=12.5,
                         leading=16, textColor=AZUL, alignment=TA_LEFT,
                         spaceBefore=10, spaceAfter=5, keepWithNext=1),
    "indice": ParagraphStyle("Indice", parent=_base, fontName="Helvetica-Bold", fontSize=18,
                             leading=22, textColor=AZUL_OSCURO, alignment=TA_LEFT,
                             spaceAfter=14),
    "vineta": ParagraphStyle("vineta", parent=_base, leftIndent=16, bulletIndent=4,
                             spaceAfter=3),
    "celda": ParagraphStyle("celda", parent=_base, fontSize=9, leading=12,
                            alignment=TA_LEFT, spaceAfter=0),
    "celda_enc": ParagraphStyle("celda_enc", parent=_base, fontName="Helvetica-Bold",
                                fontSize=9, leading=12, textColor=colors.white,
                                alignment=TA_LEFT, spaceAfter=0),
    "etiqueta": ParagraphStyle("etiqueta", parent=_base, fontName="Helvetica-Bold",
                               fontSize=9, leading=12, textColor=AZUL, alignment=TA_LEFT,
                               spaceAfter=4),
}


def p(texto, estilo="cuerpo"):
    return Paragraph(texto, E[estilo])


def vinetas(items):
    return [Paragraph(t, E["vineta"], bulletText="•") for t in items]


def numeradas(items):
    return [Paragraph(t, E["vineta"], bulletText=f"{i}.") for i, t in enumerate(items, 1)]


def tabla(encabezados, filas, anchos):
    datos = [[Paragraph(h, E["celda_enc"]) for h in encabezados]]
    datos += [[Paragraph(c, E["celda"]) for c in fila] for fila in filas]
    t = Table(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FILA]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


# ----------------------------------------------------------------------------
# Documento con índice automático
# ----------------------------------------------------------------------------
class Documento(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            nombre = flowable.style.name
            if nombre == "H1":
                self.notify("TOCEntry", (0, flowable.getPlainText(), self.page))
            elif nombre == "H2":
                self.notify("TOCEntry", (1, flowable.getPlainText(), self.page))


def dibujar_portada(datos):
    def _portada(c, doc):
        c.saveState()
        alto_banda = 9.5 * cm
        c.setFillColor(AZUL_OSCURO)
        c.rect(0, ALTO_PAGINA - alto_banda, ANCHO_PAGINA, alto_banda, stroke=0, fill=1)
        c.setFillColor(AZUL)
        c.rect(0, ALTO_PAGINA - alto_banda - 0.18 * cm, ANCHO_PAGINA, 0.18 * cm, stroke=0, fill=1)

        x = MARGEN
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x, ALTO_PAGINA - 2.3 * cm, datos["universidad"].upper())
        c.setFillColor(AZUL_CLARO)
        c.setFont("Helvetica", 10)
        c.drawString(x, ALTO_PAGINA - 3.0 * cm, datos["facultad"])
        c.drawString(x, ALTO_PAGINA - 3.6 * cm, datos["carrera"])

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 46)
        c.drawString(x, ALTO_PAGINA - 6.3 * cm, datos["proyecto"])
        c.setFillColor(AZUL_CLARO)
        c.setFont("Helvetica", 13)
        y = ALTO_PAGINA - 7.4 * cm
        for linea in simpleSplit(datos["subtitulo"], "Helvetica", 13, ANCHO_UTIL):
            c.drawString(x, y, linea)
            y -= 0.62 * cm
        c.restoreState()
    return _portada


def dibujar_pie(c, doc):
    c.saveState()
    c.setStrokeColor(BORDE)
    c.setLineWidth(0.5)
    c.line(MARGEN, 1.7 * cm, ANCHO_PAGINA - MARGEN, 1.7 * cm)
    c.setFont("Helvetica", 8.5)
    c.setFillColor(GRIS)
    c.drawString(MARGEN, 1.2 * cm, "SafeSite · Documento del proyecto")
    c.drawRightString(ANCHO_PAGINA - MARGEN, 1.2 * cm, f"Página {doc.page}")
    c.restoreState()


# ----------------------------------------------------------------------------
# Contenido
# ----------------------------------------------------------------------------
def portada_flowables(datos):
    historia = [Spacer(1, 8.6 * cm), p("INTEGRANTES", "etiqueta")]
    filas = [[i["nombre"], i["carnet"]] for i in datos["integrantes"]]
    historia.append(tabla(["Nombre completo", "Carnet"], filas,
                          [ANCHO_UTIL * 0.68, ANCHO_UTIL * 0.32]))
    historia.append(Spacer(1, 0.9 * cm))
    historia.append(tabla(
        ["Asignatura", "Docente", "Fecha"],
        [[datos["asignatura"], datos["docente"], datos["fecha"]]],
        [ANCHO_UTIL * 0.40, ANCHO_UTIL * 0.36, ANCHO_UTIL * 0.24]))
    historia.append(PageBreak())
    return historia


def indice_flowables():
    toc = TableOfContents()
    toc.dotsMinLevel = 0
    toc.levelStyles = [
        ParagraphStyle("toc1", fontName="Helvetica-Bold", fontSize=11.5, leading=21,
                       textColor=AZUL_OSCURO),
        ParagraphStyle("toc2", fontName="Helvetica", fontSize=10, leading=16,
                       leftIndent=18, textColor=TEXTO),
    ]
    return [p("Índice", "indice"), toc, PageBreak()]


def h1(texto):
    return [CondPageBreak(6 * cm), p(texto, "H1")]


def contenido():
    s = []

    # ---------------------------------------------------------------- 1
    s += h1("1. Introducción")
    s += [
        p("En la industria de la construcción, las personas que trabajan en obra están "
          "expuestas a riesgos como la caída de objetos, los golpes en la cabeza, el "
          "contacto con maquinaria y la baja visibilidad en zonas de tránsito. Dos de "
          "los elementos de protección más básicos para reducir estos riesgos son el "
          "<b>casco</b> y el <b>chaleco reflectivo</b>. Aun así, su uso depende "
          "casi por completo de la supervisión humana."),
        p("<b>El problema.</b> Un supervisor no puede observar todos los frentes de "
          "trabajo al mismo tiempo, por lo que el incumplimiento del uso de EPP suele "
          "pasar desapercibido hasta que ocurre un incidente o una inspección. Además, "
          "rara vez queda un registro objetivo de cuándo y con qué frecuencia se "
          "incumplió la norma, lo que dificulta analizar tendencias, exigir "
          "responsabilidades y mejorar de forma continua las medidas de seguridad. Las "
          "soluciones comerciales de videovigilancia con analítica suelen requerir "
          "equipos costosos, servidores con tarjeta gráfica o servicios en la nube, "
          "lo que las deja fuera del alcance de pequeñas y medianas constructoras."),
        p("<b>La solución propuesta.</b> SafeSite es una aplicación de escritorio que "
          "usa una cámara web y visión por computadora para detectar personas en tiempo "
          "real y comprobar si llevan casco y chaleco. Cuando detecta una infracción, "
          "avisa de inmediato con una alerta visual (recuadro rojo con el texto "
          "\"ALERTA: FALTA EPP\") y una alarma sonora continua, y conserva evidencia "
          "de cada caso: una fotografía, la fecha y hora, y el tipo de falta, guardados "
          "en una base de datos local. El sistema está pensado para ejecutarse en "
          "computadoras comunes sin tarjeta gráfica dedicada y procesa todo de forma "
          "local, sin enviar imágenes a internet."),
        p("Este documento describe los objetivos, la delimitación, la justificación de "
          "las tecnologías y los requerimientos del proyecto. Junto a él se entrega un "
          "prototipo inicial ejecutable que implementa la funcionalidad central: "
          "monitoreo en vivo con detección, alerta sonora y registro de infracciones."),
    ]

    # ---------------------------------------------------------------- 2
    s += h1("2. Objetivo general y objetivos específicos")
    s += [p("2.1 Objetivo general", "H2"),
          p("Desarrollar un sistema de escritorio de monitoreo en tiempo real que, "
            "mediante visión por computadora aplicada al video de una cámara web, "
            "detecte a las personas y verifique el uso de casco y chaleco, emita alertas "
            "inmediatas y conserve evidencia de cada infracción, funcionando en equipos "
            "sin tarjeta gráfica dedicada."),
          p("2.2 Objetivos específicos", "H2")]
    s += numeradas([
        "Capturar y procesar video en tiempo real desde una cámara web a 640 x 480 "
        "píxeles, aplicando optimizaciones para CPU (modelo liviano YOLOv8n, imágenes "
        "de entrada de 320 o 416 píxeles y salto de fotogramas).",
        "Detectar personas con YOLOv8n y verificar la presencia de casco y chaleco "
        "mediante reglas sobre la imagen, con la posibilidad de sustituirlas por un "
        "modelo entrenado específicamente en EPP.",
        "Notificar cada infracción con un recuadro rojo y el texto \"ALERTA: FALTA EPP\" "
        "y con una alarma sonora continua que se detenga cuando el equipo se "
        "regularice; marcar en verde \"EPP COMPLETO\" cuando se cumple la norma.",
        "Registrar cada infracción en una base de datos SQLite (identificador, fecha y "
        "hora, tipo de falta y ruta de la captura) y guardar una fotografía JPG como "
        "evidencia.",
        "Diseñar una interfaz gráfica con PyQt6 que incluya monitoreo en vivo con "
        "indicadores de estado, un historial consultable con vista previa y exportación "
        "a CSV, y una sección de ajustes configurables.",
        "Verificar el funcionamiento mediante pruebas automáticas y gestionar el "
        "desarrollo de forma colaborativa con Git y GitHub.",
    ])

    # ---------------------------------------------------------------- 3
    s += h1("3. Delimitación del proyecto")
    s += [p("3.1 Alcance", "H2"),
          p("El proyecto comprende el diseño y la construcción de una aplicación de "
            "escritorio que:")]
    s += vinetas([
        "Captura video de <b>una cámara web</b> conectada al computador.",
        "Detecta personas y verifica únicamente <b>casco y chaleco</b>.",
        "Emite alertas visuales y sonoras, y registra las infracciones con su captura "
        "en una base de datos local.",
        "Ofrece una interfaz con monitoreo en vivo, historial, exportación a CSV y "
        "ajustes persistentes (cámara, modelo, rendimiento, alarma, carpeta de "
        "capturas y tema).",
    ]) 
    s += [p("3.2 Fuera del alcance", "H2")]
    s += vinetas([
        "Otros elementos de protección (guantes, gafas, calzado, arneses, protección "
        "auditiva).",
        "Múltiples cámaras, cámaras IP o transmisión de video por red.",
        "Identificación o reconocimiento de personas: el sistema registra infracciones, "
        "no identidades.",
        "Envío de notificaciones remotas (correo, mensajería), servicios en la nube o "
        "aplicación móvil.",
        "El entrenamiento de un modelo propio a gran escala. El sistema permite "
        "integrar un modelo de EPP ya entrenado, pero su entrenamiento no forma parte "
        "de esta fase.",
    ])
    s += [p("3.3 Delimitación técnica, espacial y temporal", "H2")]
    s += vinetas([
        "<b>Técnica:</b> Python 3.10 o superior; ejecución solo en CPU; sistema "
        "operativo principal Windows 10/11.",
        "<b>Espacial:</b> las pruebas se realizan en un entorno controlado (aula o "
        "laboratorio) con la cámara web del equipo, simulando una zona de trabajo.",
        "<b>Temporal:</b> proyecto académico desarrollado durante el ciclo del curso; "
        "se entrega un prototipo inicial y su documentación.",
    ])
    s += [p("3.4 Limitaciones conocidas", "H2"),
          p("Con el modelo estándar (YOLOv8n entrenado en COCO) el sistema detecta "
            "personas, pero no reconoce cascos ni chalecos como objetos. Por ello, el "
            "prototipo comprueba el EPP mediante el <b>color</b> de la zona de la cabeza "
            "y del torso. Este método depende de la iluminación y del color del equipo, "
            "y puede producir falsos positivos o negativos; la precisión aumenta "
            "al usar un modelo entrenado en EPP, que el sistema detecta y utiliza "
            "automáticamente. El sistema es una ayuda para la supervisión y no la "
            "sustituye.")]

    # ---------------------------------------------------------------- 4
    s += h1("4. Justificación de las tecnologías a utilizar")
    s += [p("La elección de tecnologías responde a tres criterios: que funcionen sin "
            "tarjeta gráfica, que sean de código abierto y bien documentadas, y que "
            "permitan trabajar de forma colaborativa y mantener el código ordenado.")]
    filas = [
        ["<b>Python 3.10+</b>",
         "Lenguaje principal. Tiene el ecosistema más completo para visión por "
         "computadora y aprendizaje automático, es legible y facilita que todo el "
         "equipo colabore."],
        ["<b>YOLOv8n (Ultralytics)</b>",
         "Detector de objetos en tiempo real. La variante \"nano\" es la más pequeña y "
         "rápida de la familia, adecuada para CPU. Además permite sustituirla por un "
         "modelo entrenado en EPP sin cambiar el resto del sistema."],
        ["<b>OpenCV</b>",
         "Captura de video de la cámara web, preprocesamiento, análisis de color (HSV) "
         "y dibujo de recuadros y textos sobre el video."],
        ["<b>NumPy</b>",
         "Manejo eficiente de los fotogramas como matrices; es base de OpenCV y de "
         "Ultralytics."],
        ["<b>PyQt6</b>",
         "Interfaz gráfica de escritorio con aspecto profesional. Su sistema de hilos "
         "(QThread) y señales permite procesar video sin congelar la ventana, y sus "
         "hojas de estilo permiten un diseño moderno con tema claro y oscuro."],
        ["<b>pygame-ce</b>",
         "Reproducción de la alarma sonora continua mediante su módulo de audio. Se "
         "usa la edición de la comunidad (pygame-ce), que publica instaladores "
         "precompilados para versiones recientes de Python y evita errores de "
         "compilación en Windows."],
        ["<b>SQLite (sqlite3)</b>",
         "Base de datos incluida en la biblioteca estándar de Python. No necesita "
         "servidor ni configuración: todo se guarda en un único archivo "
         "(infracciones.db), ideal para una aplicación local."],
        ["<b>Git y GitHub</b>",
         "Control de versiones y trabajo colaborativo mediante ramas, "
         "<i>commits</i> y <i>pull requests</i>, con historial verificable de la "
         "contribución de cada integrante."],
        ["<b>unittest</b>",
         "Pruebas automáticas incluidas en Python, sin dependencias adicionales, para "
         "verificar la base de datos, las reglas de detección, la alarma y el flujo "
         "completo del monitoreo."],
    ]
    s += [tabla(["Tecnología", "Justificación"], filas, [ANCHO_UTIL * 0.27, ANCHO_UTIL * 0.73])]

    # ---------------------------------------------------------------- 5
    s += h1("5. Requerimientos del proyecto")
    s += [p("5.1 Requerimientos funcionales", "H2"),
          p("Describen lo que el sistema debe hacer. La prioridad indica la importancia "
            "para la funcionalidad central del prototipo.")]
    rf = [
        ["RF-01", "Capturar video en tiempo real desde la cámara web a 640 x 480 píxeles.", "Alta"],
        ["RF-02", "Detectar a las personas presentes en los fotogramas procesados mediante YOLOv8n.", "Alta"],
        ["RF-03", "Verificar para cada persona la presencia de casco y chaleco, mediante reglas de color o un modelo entrenado en EPP.", "Alta"],
        ["RF-04", "Marcar con un recuadro rojo y el texto \"ALERTA: FALTA EPP\" a la persona que incumpla.", "Alta"],
        ["RF-05", "Marcar con un recuadro verde y el texto \"EPP COMPLETO\" a la persona que cumpla.", "Alta"],
        ["RF-06", "Reproducir una alarma sonora continua mientras exista una infracción y detenerla cuando se regularice.", "Alta"],
        ["RF-07", "Registrar cada infracción en SQLite (infracciones.db) con id, fecha y hora, tipo de falta y ruta de la captura.", "Alta"],
        ["RF-08", "Guardar una captura JPG de cada infracción en la carpeta de capturas.", "Alta"],
        ["RF-09", "Confirmar la infracción tras detecciones consecutivas y limitar la frecuencia de registros para evitar falsos positivos y duplicados.", "Media"],
        ["RF-10", "Permitir iniciar y detener el monitoreo y silenciar la alarma desde la interfaz.", "Alta"],
        ["RF-11", "Mostrar indicadores en tiempo real: estado general, cámara, personas, con y sin EPP, FPS, alarma, total de infracciones y actividad reciente.", "Media"],
        ["RF-12", "Mostrar un historial de infracciones con fecha, tipo y foto, con búsqueda, filtro por tipo y vista previa de la captura.", "Alta"],
        ["RF-13", "Exportar el historial a un archivo CSV.", "Baja"],
        ["RF-14", "Permitir configurar y guardar ajustes: cámara, resolución, modelo, tamaño de imagen, confianza, salto de fotogramas, alarma, volumen, carpeta de capturas y tema.", "Media"],
        ["RF-15", "Informar al usuario los fallos de cámara sin cerrar la aplicación.", "Media"],
    ]
    s += [tabla(["ID", "Requerimiento", "Prioridad"], rf,
                [ANCHO_UTIL * 0.11, ANCHO_UTIL * 0.76, ANCHO_UTIL * 0.13])]

    s += [CondPageBreak(9 * cm), Spacer(1, 6), p("5.2 Requerimientos no funcionales", "H2"),
          p("Describen las cualidades que debe tener el sistema. Las cifras son "
            "objetivos de diseño que se verificarán durante las pruebas.")]
    rnf = [
        ["RNF-01", "<b>Rendimiento:</b> ejecutarse únicamente en CPU, con un objetivo de al menos 8 FPS en pantalla en un equipo de gama media, usando YOLOv8n, imgsz de 320 o 416 y salto de fotogramas."],
        ["RNF-02", "<b>Tiempo de respuesta:</b> la alerta visual y sonora debe aparecer en menos de 2 segundos desde que ocurre la infracción, en condiciones normales."],
        ["RNF-03", "<b>Usabilidad:</b> interfaz clara, con estados indicados por colores y textos, utilizable sin conocimientos técnicos y con tema claro y oscuro."],
        ["RNF-04", "<b>Portabilidad:</b> funcionar en Windows 10/11 con Python 3.10 o superior, instalando las dependencias con <i>pip install -r requirements.txt</i>."],
        ["RNF-05", "<b>Mantenibilidad:</b> arquitectura modular (núcleo, datos e interfaz separados), código comentado y pruebas automáticas."],
        ["RNF-06", "<b>Fiabilidad:</b> el procesamiento de video no debe congelar la interfaz; si falla la cámara o el audio, el sistema informa el problema y continúa operando."],
        ["RNF-07", "<b>Persistencia e integridad:</b> las infracciones se almacenan de forma local y duradera en SQLite; las rutas de las capturas se guardan de forma portable."],
        ["RNF-08", "<b>Privacidad:</b> todo el procesamiento es local; no se envían imágenes ni datos a servicios externos."],
        ["RNF-09", "<b>Colaboración:</b> el código se gestiona en un repositorio de GitHub con ramas y <i>pull requests</i>, con trazabilidad de los aportes de cada integrante."],
    ]
    s += [tabla(["ID", "Requerimiento"], rnf, [ANCHO_UTIL * 0.11, ANCHO_UTIL * 0.89])]
    return s


# ----------------------------------------------------------------------------
def generar():
    with open(DATOS, encoding="utf-8") as f:
        datos = json.load(f)

    doc = Documento(
        SALIDA, pagesize=letter, leftMargin=MARGEN, rightMargin=MARGEN,
        topMargin=2.2 * cm, bottomMargin=2.4 * cm,
        title=f"{datos['proyecto']} - Documento del proyecto",
        author=", ".join(i["nombre"] for i in datos["integrantes"]),
        subject=datos["subtitulo"],
    )
    marco = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="marco")
    doc.addPageTemplates([
        PageTemplate(id="portada", frames=[marco], onPage=dibujar_portada(datos),
                     autoNextPageTemplate="interior"),
        PageTemplate(id="interior", frames=[marco], onPage=dibujar_pie),
    ])

    historia = portada_flowables(datos) + indice_flowables() + contenido()
    doc.multiBuild(historia)
    print(f"PDF generado: {SALIDA}")


if __name__ == "__main__":
    generar()
