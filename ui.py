import sys
import os
import shutil
from exportar import pdf_maker
from contactos import ContactosMng
from herramientas import Herramientas

"""
Modo claro: sección de strings donde se contengan los colores usados para este modo, y que en el guardado se mantenga, así igual con el modo oscuro
Selección de colores: una serie de códigos de color que se implementarán en función del seleccionado por el usuario, y se actualizarán como tal
TODOS los datos de configuración se guardarán el selfs clave de donde el sistema tomará la información y actualizará la UI acorde a las selecciones
Al momento de guardar la información, el sistema primero duplicará la carpeta previa de configuración y luego intentará guardar la info en la
carpeta original, pero si algo falla se volverá a los datos por defecto por medio de la carpeta duplicada.
Para el idioma, se almacenará en una serie de strings la información elegida, y se usará booleano para determinar si es español (True) o inglés (False)
Se usarán botones y no entradas de texto para simplificar la selección de datos.
Para el nombre de usuario se podrá escribir texto, que no sea ni NULO ni de un largo superior a 40 caracteres.
El guardado se hará en JSON con el fin de conservar los tipos de valor almacenados.

"""
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QGroupBox, QPushButton,
                             QLabel, QLineEdit, QHBoxLayout, QFileDialog, QMessageBox, QTextEdit, QTabWidget,
                             QFormLayout, )
from PyQt6.QtGui import QGuiApplication, QAction
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path


class ColoresConfig:
    def __init__(self):
        self.temas = {
            "claro": {
                "fondo": "#f4f6fa",
                "fondo_tarjeta": "#ffffff",
                "borde": "#d9dee6",
                "acento": "#1E1700",
                "acento_hover": "#c0532f",
            },
            "oscuro": {
                "fondo": "#1e2128",
                "fondo_tarjeta": "#2a2e37",
                "borde": "#3a3f4b",
                "acento": "#910f0f",
                "acento_hover": "#993131",
            },
        }
        self.color_menu = {"claro": "#E05D00", "oscuro": "#ff0000"}
        self.color_letra = {"claro": "#000000", "oscuro": "#e6e8ec"}
        self.tamano_letra = 12

    def set_color_menu(self, mode, color):
        self.color_menu[mode] = color

    def set_color_letra(self, mode, color):
        self.color_letra[mode] = color

    def tamanos(self):
        base = self.tamano_letra
        return {
            "titulo": base + 6,
            "subtitulo": base + 3,
            "texto": base,
            "boton": base - 1,
        }

    def legibilidad(self, hex_fondo):
        hex_fondo = hex_fondo.lstrip("#")
        r, g, b = int(hex_fondo[0:2], 16), int(hex_fondo[2:4], 16), int(hex_fondo[4:6], 16)
        luminancia = (0.299 * r + 0.587 * g + 0.114 * b) / 255

        return "#000000" if luminancia > 0.5 else "#ffffff"

    def generar_qss(self, mode):
        colores = self.temas[mode]
        menu = self.color_menu[mode]
        texto = self.color_letra[mode]
        t_letra = self.tamanos()
        return f"""
         QWidget {{background-color: {colores['fondo']};}}
        QMainWindow {{ background-color: {colores['fondo']}; }}

        QGroupBox {{
            background-color: {colores['fondo_tarjeta']};
            border: 1px solid {colores['borde']};
            border-radius: 10px;
            color: {texto};
            font-size: {t_letra['subtitulo']}pt;
        }}

        QPushButton {{
            background-color: {colores['acento']};
            color: {self.legibilidad(colores['acento'])};
            border-radius: 8px;
            padding: 8px 16px;
            font-size: {t_letra['boton']}pt;
        }}

        QPushButton:hover {{ background-color: {colores['acento_hover']}; }}

        QLabel {{ color: {texto};
                font-size: {t_letra['texto']}pt;
        }}
        QLabel#TituloPagina {{
        color: {texto};
        font-size: {t_letra['titulo']}pt;
        font-weight: 700;
        }}

        QMenuBar {{ background-color: {menu}; 
                    font-size: {t_letra['texto']}pt;
                    color: {texto};
                }}

        QLineEdit{{color: {texto};}}

        QComboBox {{
            background-color: {colores['fondo_tarjeta']};
            color: {texto};
            border: 1px solid {colores['borde']};
            }}

        QComboBox QAbstractItemView {{
            color: {texto};
            background-color: {colores['fondo_tarjeta']};
            selection-background-color: {colores['acento']};
            selection-color: white;
        }}

        QSpinBox {{
            background-color: {colores['fondo_tarjeta']};
            color: {texto};
            border: 1px solid {colores['borde']};
            }}
                QCheckBox {{
            color: {texto};
            font-size: {t_letra['texto']}pt;
        }}
        QTextEdit {{
            background-color: {colores['fondo_tarjeta']};
            color: {texto};
            border: 1px solid {colores['borde']};
            border-radius: 6px;
            font-size: {t_letra['texto']}pt;
        }}
        QSlider::groove:horizontal {{
            background: {colores['borde']};
            height: 6px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {colores['acento']};
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }}

        """


def formatear_datos(datos):
    """Convierte el dict 'datos' devuelto por el gestor en texto legible."""
    if not datos:
        return ""
    if isinstance(datos, dict):
        return "\n".join(f"{clave}: {valor}" for clave, valor in datos.items())
    return str(datos)


def mostrar_resultado(salida, ok, mensaje, datos):
    """Escribe en el cuadro de salida el resultado de una operación."""
    icono = "✔" if ok else "✖"
    texto = f"{icono} {mensaje}"
    extra = formatear_datos(datos)
    if extra:
        texto += "\n\n" + extra
    salida.setPlainText(texto)


def crear_salida():
    salida = QTextEdit()
    salida.setReadOnly(True)
    salida.setPlaceholderText("El resultado aparecerá aquí...")
    return salida


def crear_titulo(texto):
    lbl = QLabel(texto)
    lbl.setObjectName("TituloPagina")
    return lbl


class GestorContactos:
    """
    Conecta la interfaz con las clases de datos (ContactosMng, pdf_maker y
    Herramientas). Todas las funciones devuelven (ok, mensaje, datos).
    """
    CARPETA = Path("info")
    JSON_REGISTROS = CARPETA / "registros.json"  # lo escribe ContactosMng.generar_json()
    PDF_REPORTE = CARPETA / "reporte_contactos.pdf"  # lo escribe pdf_maker.formatear_pdf()
    TEL_MAX = 2 ** 32 - 1  # el teléfono se guarda como entero sin signo de 4 bytes
    MSG_TELEFONO = ("El teléfono solo puede llevar dígitos, espacios y guiones, "
                    f"y no puede superar {TEL_MAX}.")

    def __init__(self):
        self.contactos = ContactosMng()
        self.exportador = pdf_maker()
        self.herramientas = Herramientas()

        self.error_carga = None
        try:
            self.contactos.cargar_posiciones()
        except (ValueError, OSError) as e:  # índice dañado o ilegible
            self.error_carga = str(e)
        if self.contactos.info is None and self.error_carga is None:
            self.contactos.info = {}  # primera ejecución: todavía no hay índice

    # ================================================================
    # UTILIDADES INTERNAS
    # ================================================================
    def _bloqueado(self):
        """Si el índice no se pudo cargar, no se puede operar con los contactos."""
        if self.error_carga:
            return (False, f"No se pudo cargar el índice de contactos: {self.error_carga}", None)
        return None

    def _sellar_hash(self):
        """Actualiza el hash SHA-256 tras cambiar los datos. Devuelve '' si todo salió bien,
        o un aviso para añadir al mensaje si el hash no se pudo actualizar."""
        ok, msg, _ = self.herramientas.actualizar_hash()
        return "" if ok else f" (aviso: {msg})"

    def _telefono_a_int(self, texto):
        """'5555-1234' -> 55551234. Devuelve None si no es un teléfono válido."""
        limpio = texto.replace(" ", "").replace("-", "")
        if not (limpio.isascii() and limpio.isdigit()):
            return None
        valor = int(limpio)
        return valor if valor <= self.TEL_MAX else None

    @staticmethod
    def _id_a_int(texto):
        try:
            return int(texto)
        except ValueError:
            return None

    @staticmethod
    def _contacto_a_dict(e_id, nombre, telefono, correo, ciudad):
        return {"id": e_id, "nombre": nombre, "telefono": telefono,
                "correo": correo, "ciudad": ciudad}

    def _copiar_a(self, origen, destino, verbo):
        """Copia un archivo generado en info/ a la ruta que eligió el usuario."""
        destino = Path(destino)
        try:
            if destino.resolve() != origen.resolve():
                shutil.copyfile(origen, destino)
        except OSError as e:
            return (False, f"No se pudo guardar en {destino}: {e}", None)
        return (True, f"{verbo} {destino}",
                {"ruta": str(destino), "total_contactos": len(self.contactos.info)})

    # ================================================================
    # CONTACTOS
    # ================================================================
    def agregar_contacto(self, nombre, telefono, correo, ciudad):
        """El ID no lo escribe el usuario: se asigna el siguiente número libre."""
        bloqueo = self._bloqueado()
        if bloqueo:
            return bloqueo
        tel = self._telefono_a_int(telefono)
        if tel is None:
            return (False, self.MSG_TELEFONO, None)

        nuevo_id = max(self.contactos.info, default=0) + 1
        ok, msg, _ = self.contactos.anadir_entrada(nuevo_id, nombre, tel, correo, ciudad)
        if not ok:
            return (False, msg, None)

        aviso = self._sellar_hash()
        return (True, f"Contacto agregado con el ID {nuevo_id}{aviso}",
                self._contacto_a_dict(nuevo_id, nombre, tel, correo, ciudad))

    def buscar_por_id(self, id_contacto):
        bloqueo = self._bloqueado()
        if bloqueo:
            return bloqueo
        id_int = self._id_a_int(id_contacto)
        if id_int is None:
            return (False, "El ID debe ser un número entero", None)

        ok, msg, registro = self.contactos.obtener_entrada(id_int)
        if not ok:
            return (False, msg, None)
        return (True, msg, self._contacto_a_dict(*registro))

    def modificar_contacto(self, id_contacto, nuevos_datos):
        """ContactosMng reescribe el registro completo, así que primero se leen los
        datos actuales y se mezclan con los campos que el usuario quiso cambiar."""
        bloqueo = self._bloqueado()
        if bloqueo:
            return bloqueo
        id_int = self._id_a_int(id_contacto)
        if id_int is None:
            return (False, "El ID debe ser un número entero", None)

        ok, msg, registro = self.contactos.obtener_entrada(id_int)
        if not ok:
            return (False, msg, None)
        _, nombre, telefono, correo, ciudad = registro

        nombre = nuevos_datos.get("nombre", nombre)
        correo = nuevos_datos.get("correo", correo)
        ciudad = nuevos_datos.get("ciudad", ciudad)
        if "telefono" in nuevos_datos:
            telefono = self._telefono_a_int(nuevos_datos["telefono"])
            if telefono is None:
                return (False, self.MSG_TELEFONO, None)

        ok, msg, _ = self.contactos.modificar_entrada(id_int, nombre, telefono, correo, ciudad)
        if not ok:
            return (False, msg, None)

        aviso = self._sellar_hash()
        return (True, f"Contacto modificado{aviso}",
                self._contacto_a_dict(id_int, nombre, telefono, correo, ciudad))

    # ================================================================
    # EXPORTAR
    # ================================================================
    def exportar_json(self, ruta_destino):
        bloqueo = self._bloqueado()
        if bloqueo:
            return bloqueo
        ok, msg, _ = self.contactos.generar_json()
        if not ok:
            return (False, msg, None)
        return self._copiar_a(self.JSON_REGISTROS, ruta_destino, "Exportado a")

    def generar_reporte_pdf(self, ruta_destino):
        bloqueo = self._bloqueado()
        if bloqueo:
            return bloqueo
        # El PDF se arma a partir de registros.json, así que se regenera antes
        # para que el reporte nunca salga con datos viejos.
        ok, msg, _ = self.contactos.generar_json()
        if not ok:
            return (False, msg, None)
        ok, msg, _ = self.exportador.formatear_pdf()
        if not ok:
            return (False, msg, None)
        return self._copiar_a(self.PDF_REPORTE, ruta_destino, "Reporte generado en")

    # ================================================================
    # HERRAMIENTAS
    # ================================================================
    def verificar_integridad(self):
        return self.herramientas.verificar_integridad()

    def crear_respaldo_zip(self):
        """El ZIP se guarda en respaldos/backup_[fecha].zip (lo decide Herramientas)."""
        return self.herramientas.hacer_backup()

    def obtener_info_del_sistema(self):
        return self.herramientas.obtener_info_del_sistema()


# =====================================================================
#  PÁGINA: CONTACTOS (funcional)
# =====================================================================
class ContactosPage(QWidget):
    TAB_AGREGAR, TAB_BUSCAR, TAB_MODIFICAR = 0, 1, 2

    def __init__(self, gestor, parent=None):
        super().__init__(parent)
        self.gestor = gestor

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(crear_titulo("Contactos"))

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_agregar(), "Agregar")
        self.tabs.addTab(self._tab_buscar(), "Buscar por ID")
        self.tabs.addTab(self._tab_modificar(), "Modificar")
        layout.addWidget(self.tabs)

        self.salida = crear_salida()
        layout.addWidget(self.salida)

    # ---------------- Agregar ----------------
    def _tab_agregar(self):
        w = QWidget()
        form = QFormLayout(w)
        self.in_nombre = QLineEdit()
        self.in_telefono = QLineEdit()
        self.in_correo = QLineEdit()
        self.in_ciudad = QLineEdit()
        boton = QPushButton("Agregar contacto")
        boton.clicked.connect(self.accion_agregar)
        form.addRow("Nombre:", self.in_nombre)
        form.addRow("Teléfono:", self.in_telefono)
        form.addRow("Correo:", self.in_correo)
        form.addRow("Ciudad:", self.in_ciudad)
        form.addRow(boton)
        return w

    def accion_agregar(self):
        nombre = self.in_nombre.text().strip()
        telefono = self.in_telefono.text().strip()
        correo = self.in_correo.text().strip()
        ciudad = self.in_ciudad.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Datos incompletos", "El nombre es obligatorio.")
            return

        # >>> LLAMADA [1/8]: agregar_contacto(nombre, telefono, correo, ciudad)
        ok, msg, datos = self.gestor.agregar_contacto(nombre, telefono, correo, ciudad)

        mostrar_resultado(self.salida, ok, msg, datos)
        if ok:
            for campo in (self.in_nombre, self.in_telefono, self.in_correo, self.in_ciudad):
                campo.clear()

    # ---------------- Buscar por ID ----------------
    def _tab_buscar(self):
        w = QWidget()
        form = QFormLayout(w)
        self.in_buscar_id = QLineEdit()
        self.in_buscar_id.setPlaceholderText("ID del contacto...")
        self.in_buscar_id.returnPressed.connect(self.accion_buscar)
        boton = QPushButton("Buscar")
        boton.clicked.connect(self.accion_buscar)
        form.addRow("ID:", self.in_buscar_id)
        form.addRow(boton)
        return w

    def accion_buscar(self):
        id_contacto = self.in_buscar_id.text().strip()
        if not id_contacto:
            QMessageBox.warning(self, "Datos incompletos", "Escribe un ID para buscar.")
            return

        # >>> LLAMADA [2/8]: buscar_por_id(id_contacto)
        ok, msg, datos = self.gestor.buscar_por_id(id_contacto)

        mostrar_resultado(self.salida, ok, msg, datos)

    # ---------------- Modificar ----------------
    def _tab_modificar(self):
        w = QWidget()
        form = QFormLayout(w)
        self.in_mod_id = QLineEdit()
        self.in_mod_nombre = QLineEdit()
        self.in_mod_telefono = QLineEdit()
        self.in_mod_correo = QLineEdit()
        self.in_mod_ciudad = QLineEdit()
        for campo in (self.in_mod_nombre, self.in_mod_telefono, self.in_mod_correo, self.in_mod_ciudad):
            campo.setPlaceholderText("(vacío = no cambiar)")
        boton = QPushButton("Modificar contacto")
        boton.clicked.connect(self.accion_modificar)
        form.addRow("ID:", self.in_mod_id)
        form.addRow("Nuevo nombre:", self.in_mod_nombre)
        form.addRow("Nuevo teléfono:", self.in_mod_telefono)
        form.addRow("Nuevo correo:", self.in_mod_correo)
        form.addRow("Nueva ciudad:", self.in_mod_ciudad)
        form.addRow(boton)
        return w

    def accion_modificar(self):
        id_contacto = self.in_mod_id.text().strip()
        if not id_contacto:
            QMessageBox.warning(self, "Datos incompletos", "Escribe el ID del contacto a modificar.")
            return

        # Solo se envían los campos que el usuario llenó
        candidatos = {
            "nombre": self.in_mod_nombre.text().strip(),
            "telefono": self.in_mod_telefono.text().strip(),
            "correo": self.in_mod_correo.text().strip(),
            "ciudad": self.in_mod_ciudad.text().strip(),
        }
        nuevos_datos = {k: v for k, v in candidatos.items() if v}
        if not nuevos_datos:
            QMessageBox.warning(self, "Sin cambios", "Llena al menos un campo para modificar.")
            return

        # >>> LLAMADA [3/8]: modificar_contacto(id_contacto, nuevos_datos)
        ok, msg, datos = self.gestor.modificar_contacto(id_contacto, nuevos_datos)

        mostrar_resultado(self.salida, ok, msg, datos)
        if ok:
            for campo in (self.in_mod_id, self.in_mod_nombre, self.in_mod_telefono, self.in_mod_correo,
                          self.in_mod_ciudad):
                campo.clear()


# =====================================================================
#  PÁGINA: EXPORTAR (funcional)
# =====================================================================
class ExportarPage(QWidget):
    def __init__(self, gestor, parent=None):
        super().__init__(parent)
        self.gestor = gestor

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(crear_titulo("Exportar"))

        grupo = QGroupBox("Opciones de exportación")
        fila = QHBoxLayout(grupo)
        self.boton_json = QPushButton("Exportar a JSON")
        self.boton_pdf = QPushButton("Generar reporte PDF")
        self.boton_json.clicked.connect(self.accion_json)
        self.boton_pdf.clicked.connect(self.accion_pdf)
        fila.addWidget(self.boton_json)
        fila.addWidget(self.boton_pdf)
        layout.addWidget(grupo)

        self.salida = crear_salida()
        layout.addWidget(self.salida)

    def accion_json(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar a JSON", "contactos.json", "JSON (*.json)")
        if not ruta:
            return

        # >>> LLAMADA [4/8]: exportar_json(ruta)
        ok, msg, datos = self.gestor.exportar_json(ruta)

        mostrar_resultado(self.salida, ok, msg, datos)

    def accion_pdf(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Generar reporte PDF", "reporte_contactos.pdf", "PDF (*.pdf)")
        if not ruta:
            return

        # >>> LLAMADA [5/8]: generar_reporte_pdf(ruta)
        ok, msg, datos = self.gestor.generar_reporte_pdf(ruta)

        mostrar_resultado(self.salida, ok, msg, datos)


# =====================================================================
#  PÁGINA: HERRAMIENTAS (funcional)
# =====================================================================
class HerramientasPage(QWidget):
    def __init__(self, gestor, parent=None):
        super().__init__(parent)
        self.gestor = gestor

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(crear_titulo("Herramientas"))

        grupo = QGroupBox("Mantenimiento del archivo de contactos")
        fila = QHBoxLayout(grupo)
        self.boton_integridad = QPushButton("Verificar integridad")
        self.boton_zip = QPushButton("Crear respaldo ZIP")
        self.boton_info = QPushButton("Información del archivo")
        self.boton_integridad.clicked.connect(self.accion_integridad)
        self.boton_zip.clicked.connect(self.accion_zip)
        self.boton_info.clicked.connect(self.accion_info)
        fila.addWidget(self.boton_integridad)
        fila.addWidget(self.boton_zip)
        fila.addWidget(self.boton_info)
        layout.addWidget(grupo)

        self.salida = crear_salida()
        layout.addWidget(self.salida)

    def accion_integridad(self):
        # >>> LLAMADA [6/8]: verificar_integridad()
        ok, msg, datos = self.gestor.verificar_integridad()

        mostrar_resultado(self.salida, ok, msg, datos)

    def accion_zip(self):
        # >>> LLAMADA [7/8]: crear_respaldo_zip()
        ok, msg, datos = self.gestor.crear_respaldo_zip()

        mostrar_resultado(self.salida, ok, msg, datos)

    def accion_info(self):
        # >>> LLAMADA [8/8]: obtener_info_del_sistema()
        ok, msg, datos = self.gestor.obtener_info_del_sistema()

        mostrar_resultado(self.salida, ok, msg, datos)


# =====================================================================
#  PÁGINA: AYUDA (SIMULADA - no necesita lógica)
# =====================================================================
class AyudaPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(crear_titulo("Ayuda"))

        texto = QTextEdit()
        texto.setReadOnly(True)
        texto.setPlainText(
            "GUÍA DE USO (simulada)\n\n"
            "• Contactos: agrega nuevos contactos, búscalos por ID o modifica sus datos.\n"
            "• Exportar: guarda tus contactos en un archivo JSON o genera un reporte en PDF.\n"
            "• Herramientas: verifica la integridad del archivo, crea un respaldo ZIP "
            "o consulta la información del archivo.\n"
            "• Vista > Modo oscuro: cambia entre el tema claro y el oscuro.\n\n"
            "Esta sección es solo demostrativa."
        )
        layout.addWidget(texto)


# =====================================================================
#  VENTANA PRINCIPAL
# =====================================================================
class Sistema(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Contactos")

        # Centrado aproximado (igual que tu versión anterior)
        p = QGuiApplication.primaryScreen().geometry()
        self.move(2 * p.width() // 11, p.height() // 6)
        self.setFixedSize(720, 520)

        # Backend (aquí se conectan todas las funciones)
        self.gestor = GestorContactos()

        # Tema
        self.tema_manager = ColoresConfig()
        self.modo = "claro"

        # Páginas
        self.contenedor = QStackedWidget()
        self.setCentralWidget(self.contenedor)

        self.pag_contactos = ContactosPage(self.gestor)
        self.pag_exportar = ExportarPage(self.gestor)
        self.pag_herramientas = HerramientasPage(self.gestor)
        self.pag_ayuda = AyudaPage()
        for pagina in (self.pag_contactos, self.pag_exportar, self.pag_herramientas, self.pag_ayuda):
            self.contenedor.addWidget(pagina)

        self._crear_menu()
        self.aplicar_tema()

    # ---------------- Menú ----------------
    def _accion(self, menu, texto, callback):
        accion = QAction(texto, self)
        accion.triggered.connect(callback)
        menu.addAction(accion)
        return accion

    def _crear_menu(self):
        barra = self.menuBar()

        # Contactos (funcional)
        m_contactos = barra.addMenu("Contactos")
        self._accion(m_contactos, "Agregar contacto",
                     lambda: self.ir_a(self.pag_contactos, ContactosPage.TAB_AGREGAR))
        self._accion(m_contactos, "Buscar por ID",
                     lambda: self.ir_a(self.pag_contactos, ContactosPage.TAB_BUSCAR))
        self._accion(m_contactos, "Modificar contacto",
                     lambda: self.ir_a(self.pag_contactos, ContactosPage.TAB_MODIFICAR))

        # Exportar (funcional)
        m_exportar = barra.addMenu("Exportar")
        self._accion(m_exportar, "Exportar a JSON", lambda: self.ir_a(self.pag_exportar))
        self._accion(m_exportar, "Generar reporte PDF", lambda: self.ir_a(self.pag_exportar))

        # Herramientas (funcional)
        m_herr = barra.addMenu("Herramientas")
        self._accion(m_herr, "Verificar integridad", lambda: self.ir_a(self.pag_herramientas))
        self._accion(m_herr, "Crear respaldo ZIP", lambda: self.ir_a(self.pag_herramientas))
        self._accion(m_herr, "Información del archivo", lambda: self.ir_a(self.pag_herramientas))

        # Ayuda (simulado)
        m_ayuda = barra.addMenu("Ayuda")
        self._accion(m_ayuda, "Guía de uso", lambda: self.ir_a(self.pag_ayuda))
        self._accion(m_ayuda, "Acerca de", self.mostrar_acerca_de)

        # Vista: cambio claro/oscuro
        m_vista = barra.addMenu("Vista")
        self.accion_tema = QAction("Modo oscuro", self)
        self.accion_tema.setCheckable(True)
        self.accion_tema.toggled.connect(self.alternar_tema)
        m_vista.addAction(self.accion_tema)

    def ir_a(self, pagina, tab=None):
        self.contenedor.setCurrentWidget(pagina)
        if tab is not None:
            pagina.tabs.setCurrentIndex(tab)

    def mostrar_acerca_de(self):
        QMessageBox.about(self, "Acerca de", "Gestor de Contactos\nVersión demostrativa (simulado).")

    # ---------------- Tema ----------------
    def alternar_tema(self, activado):
        self.modo = "oscuro" if activado else "claro"
        self.aplicar_tema()

    def aplicar_tema(self):
        QApplication.instance().setStyleSheet(self.tema_manager.generar_qss(self.modo))


app = QApplication(sys.argv)
system = Sistema()
system.show()
sys.exit(app.exec())