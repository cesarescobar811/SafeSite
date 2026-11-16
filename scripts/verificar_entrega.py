"""verificar_entrega.py - Revisa que el repositorio cumpla lo que pide la entrega.

Uso (desde la raíz del proyecto):
    python scripts/verificar_entrega.py              # revisa archivos, README, PDF y dependencias
    python scripts/verificar_entrega.py --pruebas    # además ejecuta las pruebas automáticas

Comprueba:
  * que existan README.md, requirements.txt, el PDF y el prototipo;
  * que no queden marcadores como [Carnet] o [apellidos] en integrantes.json ni en el README;
  * que README, integrantes.json y PDF coincidan en nombres y carnets;
  * que el PDF tenga todas las secciones pedidas (requiere `pip install pypdf`);
  * que requirements.txt incluya las librerías del proyecto;
  * que Git no esté siguiendo archivos que no deben subirse (venv, bases de datos, modelos).

Termina con código 0 si todo está bien y 1 si hay alguna falla (los avisos no cuentan como falla).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

ARCHIVOS_REQUERIDOS = [
    "README.md", "requirements.txt", "app.py", ".gitignore",
    "docs/integrantes.json", "docs/SafeSite_Documento_Proyecto.pdf",
]
SECCIONES_PDF = [
    "Índice", "Introducción", "Objetivo general", "Objetivos específicos", "Delimitación",
    "Justificación", "Requerimientos funcionales", "Requerimientos no funcionales",
]
# Cada elemento es un conjunto de nombres aceptados (el primero que aparezca sirve).
PAQUETES_REQUERIDOS = [
    {"opencv-python", "opencv-python-headless"}, {"ultralytics"},
    {"pygame-ce", "pygame"}, {"numpy"}, {"pyqt6"},
]
MARCADOR = re.compile(r"\[[^\]]*\]")  # cualquier texto entre corchetes: [Carnet], [apellidos]...


class Informe:
    def __init__(self):
        self.correctas = self.fallas = self.avisos = 0

    def ok(self, texto):
        self.correctas += 1
        print(f"[OK]    {texto}")

    def falla(self, texto):
        self.fallas += 1
        print(f"[FALLA] {texto}")

    def aviso(self, texto):
        self.avisos += 1
        print(f"[AVISO] {texto}")

    def verificar(self, condicion, texto_ok, texto_falla):
        (self.ok if condicion else self.falla)(texto_ok if condicion else texto_falla)


def normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).casefold()


# ---------------------------------------------------------------------------
def revisar_archivos(inf: Informe) -> None:
    for relativa in ARCHIVOS_REQUERIDOS:
        inf.verificar((RAIZ / relativa).is_file(), f"Existe {relativa}", f"Falta {relativa}")
    pruebas = list((RAIZ / "tests").glob("test_*.py"))
    inf.verificar(bool(pruebas), f"Hay {len(pruebas)} archivo(s) de pruebas en tests/",
                  "No hay archivos de pruebas en tests/")


def revisar_integrantes(inf: Informe):
    ruta = RAIZ / "docs" / "integrantes.json"
    if not ruta.is_file():
        return None
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        inf.falla(f"integrantes.json no es un JSON válido: {exc}")
        return None

    integrantes = datos.get("integrantes", [])
    inf.verificar(len(integrantes) >= 1, f"integrantes.json lista {len(integrantes)} integrante(s)",
                  "integrantes.json no tiene integrantes")

    pendientes = [f"{clave}: {datos[clave]}" for clave in ("asignatura", "docente")
                  if MARCADOR.search(datos.get(clave, ""))]
    for i, integrante in enumerate(integrantes, 1):
        for clave in ("nombre", "carnet"):
            if not integrante.get(clave, "").strip() or MARCADOR.search(integrante[clave]):
                pendientes.append(f"integrante {i}, {clave}: {integrante.get(clave, '(vacío)')}")
    if pendientes:
        inf.falla("Faltan datos por completar en docs/integrantes.json:")
        for texto in pendientes:
            print(f"          - {texto}")
    else:
        inf.ok("integrantes.json no tiene marcadores pendientes")

    carnets = [i.get("carnet", "").strip() for i in integrantes
               if i.get("carnet", "").strip() and not MARCADOR.search(i["carnet"])]
    inf.verificar(len(carnets) == len(set(carnets)), "Los carnets no se repiten",
                  "Hay carnets repetidos en integrantes.json")
    return datos


def revisar_readme(inf: Informe, datos) -> None:
    ruta = RAIZ / "README.md"
    if not ruta.is_file():
        return
    texto = ruta.read_text(encoding="utf-8")
    plano = normalizar(texto)
    primera = texto.lstrip().splitlines()[0] if texto.strip() else ""
    inf.verificar(primera.startswith("# ") and "safesite" in primera.casefold(),
                  "El README empieza con el nombre del proyecto",
                  "El README debe empezar con un título que incluya el nombre del proyecto")
    inf.verificar("## integrantes" in plano, "El README tiene la sección Integrantes",
                  "Al README le falta la sección «Integrantes»")
    inf.verificar("## descripción" in plano, "El README tiene la sección Descripción",
                  "Al README le falta la sección «Descripción»")

    marcadores = sorted(set(MARCADOR.findall(texto)))
    # Los enlaces de Markdown y las notas con corchetes legítimas no cuentan como pendientes.
    pendientes = [m for m in marcadores if re.fullmatch(
        r"\[(carnet|apellidos|nombre[^\]]*|.*carnet.*)\]", m, flags=re.IGNORECASE)]
    inf.verificar(not pendientes, "El README no tiene marcadores pendientes",
                  f"El README aún tiene marcadores por completar: {', '.join(pendientes)}")

    if datos:
        for integrante in datos.get("integrantes", []):
            nombre, carnet = integrante.get("nombre", ""), integrante.get("carnet", "")
            if MARCADOR.search(nombre) or MARCADOR.search(carnet):
                continue  # aún incompleto: ya se avisó en la revisión de integrantes.json
            en_readme = normalizar(nombre) in plano and normalizar(carnet) in plano
            inf.verificar(en_readme, f"README e integrantes.json coinciden para {nombre}",
                          f"«{nombre}» o su carnet no aparecen igual en el README")


def revisar_requirements(inf: Informe) -> None:
    ruta = RAIZ / "requirements.txt"
    if not ruta.is_file():
        return
    nombres = set()
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#", 1)[0].strip()
        if linea:
            nombres.add(re.split(r"[<>=!~\[ ;]", linea, maxsplit=1)[0].strip().casefold())
    for aceptados in PAQUETES_REQUERIDOS:
        presentes = aceptados & nombres
        etiqueta = " o ".join(sorted(aceptados))
        inf.verificar(bool(presentes), f"requirements.txt incluye {etiqueta}",
                      f"requirements.txt no incluye {etiqueta}")
    if "pygame" in nombres and "pygame-ce" not in nombres:
        inf.aviso("requirements.txt usa «pygame»; en versiones recientes de Python conviene «pygame-ce»")


def revisar_pdf(inf: Informe, datos) -> None:
    ruta = RAIZ / "docs" / "SafeSite_Documento_Proyecto.pdf"
    if not ruta.is_file():
        return
    contenido = ruta.read_bytes()
    inf.verificar(contenido.startswith(b"%PDF") and len(contenido) > 5000,
                  "El PDF es un archivo válido", "El PDF está vacío o dañado")
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError:
        inf.aviso("No se revisó el contenido del PDF: instala pypdf (pip install pypdf)")
        return

    paginas = PdfReader(str(ruta)).pages
    inf.verificar(len(paginas) >= 5, f"El PDF tiene {len(paginas)} páginas",
                  f"El PDF tiene solo {len(paginas)} páginas; parece incompleto")
    texto = normalizar(" ".join((p.extract_text() or "") for p in paginas))

    faltantes = [s for s in SECCIONES_PDF if normalizar(s) not in texto]
    inf.verificar(not faltantes, "El PDF contiene todas las secciones pedidas",
                  f"Al PDF le faltan secciones: {', '.join(faltantes)}")
    if datos:
        ausentes = [i["nombre"] for i in datos.get("integrantes", [])
                    if normalizar(i["nombre"]) not in texto or normalizar(i["carnet"]) not in texto]
        inf.verificar(not ausentes, "La portada del PDF muestra a todos los integrantes con su carnet",
                      "El PDF está desactualizado: faltan o difieren estos integrantes: "
                      + ", ".join(ausentes) + ". Ejecuta: python docs/generar_documento.py")


def revisar_git(inf: Informe) -> None:
    gitignore = RAIZ / ".gitignore"
    if gitignore.is_file():
        reglas = gitignore.read_text(encoding="utf-8")
        for patron in ("venv", "infracciones.db", "*.pt"):
            inf.verificar(patron in reglas, f".gitignore ignora {patron}",
                          f".gitignore no ignora {patron}")
    if not (RAIZ / ".git").exists():
        inf.aviso("La carpeta no es un repositorio Git: se omite la revisión de archivos versionados")
        return
    try:
        salida = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True,
                                timeout=30, check=True).stdout.splitlines()
    except (FileNotFoundError, subprocess.SubprocessError):
        inf.aviso("No se pudo ejecutar git: se omite la revisión de archivos versionados")
        return
    indebidos = [a for a in salida if a.startswith(("venv/", ".venv/")) or "__pycache__" in a
                 or a.endswith((".db", ".pt")) or (a.startswith("capturas/") and a.endswith(".jpg"))]
    inf.verificar(not indebidos, "Git no sigue archivos que no deben subirse",
                  "Git está siguiendo archivos que no deben subirse: " + ", ".join(indebidos[:5])
                  + ("..." if len(indebidos) > 5 else ""))


def ejecutar_pruebas(inf: Informe) -> None:
    entorno = dict(os.environ, QT_QPA_PLATFORM="offscreen", SDL_AUDIODRIVER="dummy")
    resultado = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                               cwd=RAIZ, env=entorno, capture_output=True, text=True)
    resumen = re.search(r"Ran (\d+) tests?", resultado.stderr)
    cantidad = resumen.group(1) if resumen else "?"
    if resultado.returncode == 0:
        inf.ok(f"Las {cantidad} pruebas automáticas pasan")
    else:
        inf.falla(f"Fallan pruebas automáticas ({cantidad} ejecutadas). Detalle:")
        print("\n".join("          " + linea for linea in resultado.stderr.splitlines()[-15:]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Revisa que el repositorio esté listo para entregar.")
    parser.add_argument("--pruebas", action="store_true", help="ejecutar también las pruebas automáticas")
    argumentos = parser.parse_args()

    inf = Informe()
    print(f"Revisando: {RAIZ}\n")
    revisar_archivos(inf)
    datos = revisar_integrantes(inf)
    revisar_readme(inf, datos)
    revisar_requirements(inf)
    revisar_pdf(inf, datos)
    revisar_git(inf)
    if argumentos.pruebas:
        ejecutar_pruebas(inf)
    else:
        inf.aviso("No se ejecutaron las pruebas automáticas (usa --pruebas para incluirlas)")

    print(f"\nResultado: {inf.correctas} correctas, {inf.fallas} fallas, {inf.avisos} avisos")
    if inf.fallas:
        print("Corrige las fallas antes de entregar.")
    else:
        print("Todo en orden para entregar.")
    return 1 if inf.fallas else 0


if __name__ == "__main__":
    sys.exit(main())
