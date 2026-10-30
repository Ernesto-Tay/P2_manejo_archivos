import sys
import os
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
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout,QGroupBox, QPushButton, QLabel, QLineEdit, QHBoxLayout, QFileDialog, QMessageBox, QTextEdit, QTabWidget, QFormLayout,)
from PyQt6.QtGui import QGuiApplication, QAction
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
class ColoresConfig:
    def __init__(self):
        self.temas = {
                "claro": {
                    "fondo":         "#f4f6fa",
                    "fondo_tarjeta": "#ffffff",
                    "borde":         "#d9dee6",
                    "acento":        "#1E1700",
                    "acento_hover":  "#c0532f",
                },
                "oscuro": {
                    "fondo":         "#1e2128",
                    "fondo_tarjeta": "#2a2e37",
                    "borde":         "#3a3f4b",
                    "acento":        "#910f0f",
                    "acento_hover":  "#993131",
            },
        }
        self.color_menu = {"claro": "#E05D00", "oscuro":"#ff0000"}
        self.color_letra = {"claro": "#000000", "oscuro":"#e6e8ec"}
        self.tamano_letra = 12

    def set_color_menu(self, mode, color):
        self.color_menu[mode] = color

    def set_color_letra(self, mode, color):
        self.color_letra[mode] = color

    def tamanos(self):
        base = self.tamano_letra
        return {
            "titulo":    base + 6,   
            "subtitulo": base + 3,  
            "texto":     base,     
            "boton":     base - 1,
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
    Todas las funciones devuelven (ok, mensaje, datos).
    Por ahora son "stubs": devuelven False + aviso de pendiente, para que la
    interfaz funcione y puedas probarla antes de tener la lógica lista.
    """

    def __init__(self, archivo_bin="contactos.bin"):
        self.archivo_bin = Path(archivo_bin)

    def _pendiente(self, nombre):
        return (False, f"Función '{nombre}' pendiente de implementar", None)

    # ================================================================
    # CONTACTOS
    # ================================================================

    # ----------------------------------------------------------------
    # >>> IMPLEMENTAR [1/8]: agregar_contacto
    # Recibe:   nombre (str), telefono (str), correo (str)
    # Debe:     asignar un ID único, guardar el contacto en self.archivo_bin
    # Devuelve: (True, "Contacto agregado", {"id": ..., "nombre": ..., ...})
    #           (False, "motivo del error", None)
    # ----------------------------------------------------------------
    def agregar_contacto(self, nombre, telefono, correo):
        return self._pendiente("agregar_contacto")

    # ----------------------------------------------------------------
    # >>> IMPLEMENTAR [2/8]: buscar_por_id
    # Recibe:   id_contacto (str)
    # Debe:     localizar el contacto con ese ID en self.archivo_bin
    # Devuelve: (True, "Contacto encontrado", {"id":..., "nombre":..., "telefono":..., "correo":...})
    #           (False, "No existe un contacto con ese ID", None)
    # ----------------------------------------------------------------
    def buscar_por_id(self, id_contacto):
        return self._pendiente("buscar_por_id")

    # ----------------------------------------------------------------
    # >>> IMPLEMENTAR [3/8]: modificar_contacto
    # Recibe:   id_contacto (str), nuevos_datos (dict)
    #           nuevos_datos solo trae las claves que el usuario quiso cambiar,
    #           por ejemplo {"telefono": "5555-1234"} o {"nombre": "Ana", "correo": "a@x.com"}
    # Debe:     actualizar el registro y guardar el archivo
    # Devuelve: (True, "Contacto modificado", {datos ya actualizados})
    #           (False, "motivo del error", None)
    # ----------------------------------------------------------------
    def modificar_contacto(self, id_contacto, nuevos_datos):
        return self._pendiente("modificar_contacto")

    # ================================================================
    # EXPORTAR
    # ================================================================

    # ----------------------------------------------------------------
    # >>> IMPLEMENTAR [4/8]: exportar_json
    # Recibe:   ruta_destino (str) -> ruta elegida por el usuario (.json)
    # Debe:     leer todos los contactos y escribirlos como JSON en esa ruta
    #           (sugerencia: módulo json, indent=4, ensure_ascii=False)
    # Devuelve: (True, "Exportado a ...", {"ruta": ..., "total_contactos": N})
    # ----------------------------------------------------------------
    def exportar_json(self, ruta_destino):
        return self._pendiente("exportar_json")

    # ----------------------------------------------------------------
    # >>> IMPLEMENTAR [5/8]: generar_reporte_pdf
    # Recibe:   ruta_destino (str) -> ruta elegida por el usuario (.pdf)
    # Debe:     generar un PDF con la lista de contactos
    #           (sugerencia: librería reportlab o fpdf2; recuerda instalarla con pip)
    # Devuelve: (True, "Reporte generado en ...", {"ruta": ..., "total_contactos": N})
    # ----------------------------------------------------------------
    def generar_reporte_pdf(self, ruta_destino):
        return self._pendiente("generar_reporte_pdf")

    # ================================================================
    # HERRAMIENTAS
    # ================================================================

    # ----------------------------------------------------------------
    # >>> IMPLEMENTAR [6/8]: verificar_integridad
    # Recibe:   nada
    # Debe:     comprobar que el archivo BIN existe, no está corrupto
    #           y que cada registro se puede leer (por ejemplo con un checksum/hash)
    # Devuelve: (True, "Archivo íntegro", {"registros": N, "hash": "..."})
    #           (False, "Se detectó corrupción: ...", None)
    # ----------------------------------------------------------------
    def verificar_integridad(self):
        return self._pendiente("verificar_integridad")

    # ----------------------------------------------------------------
    # >>> IMPLEMENTAR [7/8]: crear_respaldo_zip
    # Recibe:   ruta_destino (str) -> ruta elegida por el usuario (.zip)
    # Debe:     comprimir self.archivo_bin dentro de un ZIP (módulo zipfile)
    # Devuelve: (True, "Respaldo creado", {"ruta": ..., "tamano_bytes": ...})
    # ----------------------------------------------------------------
    def crear_respaldo_zip(self, ruta_destino):
        return self._pendiente("crear_respaldo_zip")

    # ----------------------------------------------------------------
    # >>> IMPLEMENTAR [8/8]: obtener_info_del_sistema
    # Recibe:   nada
    # Debe:     pega aquí la función que ya tienes (usa stat). Necesita en los
    #           imports del archivo: "import os", "import stat" y tu méthod
    #           auxiliar self._fmt_fecha(timestamp).
    # Devuelve: (True, "Información del sistema obtenida", datos)
    #           (False, "Error al obtener la información del sistema: ...", None)
    # ----------------------------------------------------------------
    def obtener_info_del_sistema(self):
        return self._pendiente("obtener_info_del_sistema")


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
        boton = QPushButton("Agregar contacto")
        boton.clicked.connect(self.accion_agregar)
        form.addRow("Nombre:", self.in_nombre)
        form.addRow("Teléfono:", self.in_telefono)
        form.addRow("Correo:", self.in_correo)
        form.addRow(boton)
        return w

    def accion_agregar(self):
        nombre = self.in_nombre.text().strip()
        telefono = self.in_telefono.text().strip()
        correo = self.in_correo.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Datos incompletos", "El nombre es obligatorio.")
            return

        # >>> LLAMADA [1/8]: agregar_contacto(nombre, telefono, correo)
        ok, msg, datos = self.gestor.agregar_contacto(nombre, telefono, correo)

        mostrar_resultado(self.salida, ok, msg, datos)
        if ok:
            for campo in (self.in_nombre, self.in_telefono, self.in_correo):
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
        for campo in (self.in_mod_nombre, self.in_mod_telefono, self.in_mod_correo):
            campo.setPlaceholderText("(vacío = no cambiar)")
        boton = QPushButton("Modificar contacto")
        boton.clicked.connect(self.accion_modificar)
        form.addRow("ID:", self.in_mod_id)
        form.addRow("Nuevo nombre:", self.in_mod_nombre)
        form.addRow("Nuevo teléfono:", self.in_mod_telefono)
        form.addRow("Nuevo correo:", self.in_mod_correo)
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
        }
        nuevos_datos = {k: v for k, v in candidatos.items() if v}
        if not nuevos_datos:
            QMessageBox.warning(self, "Sin cambios", "Llena al menos un campo para modificar.")
            return

        # >>> LLAMADA [3/8]: modificar_contacto(id_contacto, nuevos_datos)
        ok, msg, datos = self.gestor.modificar_contacto(id_contacto, nuevos_datos)

        mostrar_resultado(self.salida, ok, msg, datos)
        if ok:
            for campo in (self.in_mod_id, self.in_mod_nombre, self.in_mod_telefono, self.in_mod_correo):
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
        ruta, _ = QFileDialog.getSaveFileName(self, "Crear respaldo ZIP", "respaldo_contactos.zip", "ZIP (*.zip)")
        if not ruta:
            return

        # >>> LLAMADA [7/8]: crear_respaldo_zip(ruta)
        ok, msg, datos = self.gestor.crear_respaldo_zip(ruta)

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
        self.gestor = GestorContactos("contactos.bin")

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
