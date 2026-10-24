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
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QHBoxLayout, QFileDialog, QMessageBox, QScrollArea, QFrame, QGroupBox, QComboBox, QSpinBox, QColorDialog, QCheckBox, QSlider, QTextEdit)
from PyQt6.QtGui import QGuiApplication, QAction, QPixmap, QPainter, QPainterPath, QColor
from PyQt6.QtCore import Qt, pyqtSignal
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


class Idiomas:
    def __init__(self):
        self.diccionario ={"es": {
                    "titulo_settings":    "Configuración",
                    "grupo_perfil":       "Perfil",
                    "label_nombre":       "Nombre de usuario",
                    "boton_cambiar_nom":  "Cambiar Nombre",
                    "placeholder_nombre": "Ingrese nuevo nombre...",
                    "menu_archivo":       "Archivo",
                    "menu_edicion":       "Edición",
                    "menu_ver":           "Ver",
                    "menu_config":        "Configuración",
                    "msg_exito_titulo":   "Éxito",
                    "msg_exito_texto":    "Nombre actualizado",
                    "msg_error_titulo":   "Error",
                    "msg_error_texto":    "El nombre no puede estar vacío ni superar los 40 caracteres",
                    "label_foto":         "Cambiar foto de perfil",
                    "boton_foto":         "Seleccionar una foto...",
                    "apariencia_title":    "Apariencia",
                    "tema_title":          "Tema",
                    "acces_title":         "Accesibilidad",
                    "text_color_title":    "Color del texto",
                    "menu_color_title":    "Color del menú",
                    "texto_title":         "Tamaño del texto",
                    "idioma_title":        "Idioma",
                    "texto_button":        "Cambiar",
                    "archivo_titulo":       "Archivo",
                    "edicion_titulo":      "Edición",
                    "archivo_grupo":      "Documentos recientes",
                    "archivo_doc1":       "documento_1.txt",
                    "archivo_doc2":       "reporte_final.docx",
                    "archivo_doc3":       "notas.md",
                    "archivo_nuevo":      "Nuevo archivo",
                    "archivo_abrir":      "Abrir archivo",
                    "edicion_titulo":     "Edición",
                    "edicion_grupo":      "Herramientas",
                    "edicion_deshacer":   "Deshacer",
                    "edicion_rehacer":    "Rehacer",
                    "edicion_copiar":     "Copiar",
                    "edicion_pegar":      "Pegar",
                    "edicion_cortar":     "Cortar",
                    "edicion_placeholder": "Escribe aquí para probar la apariencia...",
                    "ver_titulo":         "Ver",
                    "ver_grupo":          "Opciones de vista",
                    "ver_sidebar":        "Mostrar barra lateral",
                    "ver_pantalla":       "Modo pantalla completa",
                    "ver_zoom":           "Zoom",


                },
                "en": {
                    "titulo_settings":    "Settings",
                    "grupo_perfil":       "Profile",
                    "label_nombre":       "Username",
                    "boton_cambiar_nom":  "Change Name",
                    "placeholder_nombre": "Enter new name...",
                    "menu_archivo":       "File",
                    "menu_edicion":       "Edit",
                    "menu_ver":           "View",
                    "menu_config":        "Settings",
                    "msg_exito_titulo":   "Success",
                    "msg_exito_texto":    "Name updated",
                    "msg_error_titulo":   "Error",
                    "msg_error_texto":    "Name cannot be empty or exceed 40 characters",
                    "label_foto":         "Change profile picture",
                    "boton_foto":         "Browse pictures...",
                    "apariencia_title":    "Appearance",
                    "tema_title":          "Theme",
                    "acces_title":         "Accessibility",
                    "text_color_title":    "Text color",
                    "menu_color_title":    "Menu color",
                    "texto_title":         "Text size",
                    "idioma_title":        "Language",
                    "texto_button":        "Change",
                    "archivo_titulo":       "File",
                    "edicion_titulo":      "Edit",
                    "archivo_titulo":     "File",
                    "archivo_grupo":      "Recent documents",
                    "archivo_doc1":       "document_1.txt",
                    "archivo_doc2":       "final_report.docx",
                    "archivo_doc3":       "notes.md",
                    "archivo_nuevo":      "New file",
                    "archivo_abrir":      "Open file",
                    "edicion_titulo":     "Edit",
                    "edicion_grupo":      "Tools",
                    "edicion_deshacer":   "Undo",
                    "edicion_rehacer":    "Redo",
                    "edicion_copiar":     "Copy",
                    "edicion_pegar":      "Paste",
                    "edicion_cortar":     "Cut",
                    "edicion_placeholder": "Type here to preview the styling...",
                    "ver_titulo":         "View",
                    "ver_grupo":          "View options",
                    "ver_sidebar":        "Show sidebar",
                    "ver_pantalla":       "Fullscreen mode",
                    "ver_zoom":           "Zoom",

                },
            }

    def devolver_diccionario(self, idioma):
        return self.diccionario[idioma]


class Sistema(QMainWindow):
    def __init__(self):
        super().__init__()

        self.info_manager = info_mng()

        # datos del cosito de PyQt
        self.setWindowTitle("Config Simulator")
        p = QGuiApplication.primaryScreen().geometry()
        x = 2*(p.width())//11
        y = (p.height())//6

        # poner el cosito de forma centrada
        self.move(x, y)
        self.setFixedSize(600, 400)

        # inicialización del contenedor
        self.contenedor = QStackedWidget()
        self.setCentralWidget(self.contenedor)

        #conexión con funciones encargadas de cada dato, para recuperarlos al momento de cerrar y al momento de cargar
        self.settings_page = settings_p()

        scroll = QScrollArea()
        scroll.setWidget(self.settings_page)
        scroll.setWidgetResizable(True)   

        # títulos para los WIP
        self.archivo_widget = ArchivoPage()
        self.edicion_widget = EdicionPage()
        self.ver_widget = VerPage()


        # Asignación de distintas pestañas en función de la opción del menú elegida
        self.contenedor.addWidget(self.archivo_widget)
        self.contenedor.addWidget(self.edicion_widget)
        self.contenedor.addWidget(self.ver_widget)
        self.contenedor.addWidget(scroll)

        #Barrita superior
        self.menu = self.menuBar()

        # --- BOTONES Y ACCIONES ---
        self.m_archivo = QAction("", self)
        self.m_archivo.triggered.connect(lambda: self.contenedor.setCurrentIndex(0))
        self.menu.addAction(self.m_archivo)

        self.m_edits = QAction("", self)
        self.m_edits.triggered.connect(lambda: self.contenedor.setCurrentIndex(1))
        self.menu.addAction(self.m_edits)

        self.m_ver = QAction("", self)
        self.m_ver.triggered.connect(lambda: self.contenedor.setCurrentIndex(2))
        self.menu.addAction(self.m_ver)

        self.m_settings = QAction("", self)
        self.m_settings.triggered.connect(lambda: self.contenedor.setCurrentIndex(3))
        self.menu.addAction(self.m_settings)

        # --- DATOS EDITABLES POR EL USUARIO ---
        # tema de la app
        self.tema_select = "claro"
        self.tema_manager = ColoresConfig()
        self.color_upd(self.tema_select)

        # nombre usuario
        self.username = None

        # idioma
        self.idioma = "es"
        self.idioma_manager = Idiomas()
        self.idioma_upd(self.idioma)
        self.settings_page.idioma_cambiado.connect(self.idioma_upd)
        self.settings_page.texto_cambiado.connect(self.f_tamano_upd)
        self.settings_page.tema_cambiado.connect(self.color_upd)
        self.settings_page.color_texto_cambiado.connect(self.f_color_upd)
        self.settings_page.color_menu_cambiado.connect(self.m_color_upd)

    def color_upd(self, new_color):
        self.tema_select = new_color
        qss = self.tema_manager.generar_qss(new_color)
        QApplication.instance().setStyleSheet(qss)

    def idioma_upd(self, new_idioma): 
        self.idioma = new_idioma
        idioma_data = self.idioma_manager.devolver_diccionario(self.idioma)
        self.settings_page.t = self.idioma_manager.devolver_diccionario(self.idioma)
        self.m_archivo.setText(idioma_data["menu_archivo"])
        self.m_edits.setText(idioma_data["menu_edicion"])
        self.m_ver.setText(idioma_data["menu_ver"])
        self.m_settings.setText(idioma_data["menu_config"])
        self.settings_page.retraducir()
        self.archivo_widget.retraducir(idioma_data)
        self.edicion_widget.retraducir(idioma_data)
        self.ver_widget.retraducir(idioma_data)


    def f_tamano_upd(self, new_tamano):
        self.tema_manager.tamano_letra = new_tamano
        self.color_upd(self.tema_select)

    def f_color_upd(self, hex):
        self.tema_manager.set_color_letra(self.tema_select, hex)
        self.color_upd(self.tema_select)

    def m_color_upd(self, hex):
        self.tema_manager.set_color_menu(self.tema_select, hex)
        self.color_upd(self.tema_select)

    
    # funciones patito para los layouts adicionales (solo para que esta madre no se ande crasheando)
    def _pagina_placeholder(self, texto):
        w = QWidget()
        l = QVBoxLayout()
        l.setContentsMargins(20, 20, 20, 20)
        lbl = QLabel(texto)
        lbl.setObjectName("TituloPagina")
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        l.addWidget(lbl)
        l.addStretch()
        w.setLayout(l)
        return w

    def carga_sys(self):
        status, msg, info = self.info_manager.cargar_info()
        if status == "Éxito":
            self.idioma_upd(info.get("idioma", "es"))
            self.color_upd(info.get("tema", "claro"))
            self.f_tamano_upd(info.get("tamano_texto", 12))
            self.f_color_upd(info.get("color_texto", "#000000"))
            self.m_color_upd(info.get("color_menu", "#E05D00"))
        else:
            QMessageBox.warning(self, status, msg)

    def guardar_sys(self):
        info = {
            "username": self.settings_page.nombre_user.text(),
            "ruta_foto": self.settings_page.foto_archivo.ruta,
            "idioma": self.idioma,
            "tema": self.tema_select,
            "tamano_texto": self.tema_manager.tamano_letra,
            "color_texto": self.tema_manager.color_letra[self.tema_select],
            "color_menu": self.tema_manager.color_menu[self.tema_select]
        }
        status, msg = self.info_manager.guardar_info(info)
        if status == "Éxito":
            QMessageBox.information(self, status, msg)
        else:
            QMessageBox.critical(self, status, msg)
 
    def archivo_page(self):
        return self._pagina_placeholder(self.archivo_title.text())
 
    def edicion_page(self):
        return self._pagina_placeholder(self.edicion_title.text())
 
    def ver_page(self):
        return self._pagina_placeholder(self.ver_title.text())

class ArchivoPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        self.setLayout(layout)
 
        self.titulo = QLabel()
        self.titulo.setObjectName("TituloPagina")
        layout.addWidget(self.titulo)
 
        self.grupo = QGroupBox()
        grupo_layout = QVBoxLayout()
        self.grupo.setLayout(grupo_layout)
 
        self.doc1 = QLabel()
        self.doc2 = QLabel()
        self.doc3 = QLabel()
        grupo_layout.addWidget(self.doc1)
        grupo_layout.addWidget(self.doc2)
        grupo_layout.addWidget(self.doc3)
 
        botones = QHBoxLayout()
        self.boton_nuevo = QPushButton()
        self.boton_abrir = QPushButton()
        botones.addWidget(self.boton_nuevo)
        botones.addWidget(self.boton_abrir)
        grupo_layout.addLayout(botones)
 
        layout.addWidget(self.grupo)
        layout.addStretch()
 
    def retraducir(self, t):
        self.titulo.setText(t["archivo_titulo"])
        self.grupo.setTitle(t["archivo_grupo"])
        self.doc1.setText("doc - " + t["archivo_doc1"])
        self.doc2.setText("doc - " + t["archivo_doc2"])
        self.doc3.setText("doc - " + t["archivo_doc3"])
        self.boton_nuevo.setText(t["archivo_nuevo"])
        self.boton_abrir.setText(t["archivo_abrir"])
 
 
class EdicionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        self.setLayout(layout)
 
        self.titulo = QLabel()
        self.titulo.setObjectName("TituloPagina")
        layout.addWidget(self.titulo)
 
        self.grupo = QGroupBox()
        grupo_layout = QVBoxLayout()
        self.grupo.setLayout(grupo_layout)
 
        botones = QHBoxLayout()
        self.boton_deshacer = QPushButton()
        self.boton_rehacer = QPushButton()
        self.boton_copiar = QPushButton()
        self.boton_pegar = QPushButton()
        self.boton_cortar = QPushButton()
        for b in (self.boton_deshacer, self.boton_rehacer, self.boton_copiar, self.boton_pegar, self.boton_cortar):
            botones.addWidget(b)
        grupo_layout.addLayout(botones)
 
        self.texto_editable = QTextEdit()
        grupo_layout.addWidget(self.texto_editable)
 
        layout.addWidget(self.grupo)
 
    def retraducir(self, t):
        self.titulo.setText(t["edicion_titulo"])
        self.grupo.setTitle(t["edicion_grupo"])
        self.boton_deshacer.setText(t["edicion_deshacer"])
        self.boton_rehacer.setText(t["edicion_rehacer"])
        self.boton_copiar.setText(t["edicion_copiar"])
        self.boton_pegar.setText(t["edicion_pegar"])
        self.boton_cortar.setText(t["edicion_cortar"])
        self.texto_editable.setPlaceholderText(t["edicion_placeholder"])
 
 
class VerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        self.setLayout(layout)
 
        self.titulo = QLabel()
        self.titulo.setObjectName("TituloPagina")
        layout.addWidget(self.titulo)
 
        self.grupo = QGroupBox()
        grupo_layout = QVBoxLayout()
        self.grupo.setLayout(grupo_layout)
 
        self.check_sidebar = QCheckBox()
        self.check_pantalla = QCheckBox()
        grupo_layout.addWidget(self.check_sidebar)
        grupo_layout.addWidget(self.check_pantalla)
 
        zoom_layout = QHBoxLayout()
        self.zoom_label = QLabel()
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 150)
        self.zoom_slider.setValue(100)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(self.zoom_slider)
        grupo_layout.addLayout(zoom_layout)
 
        layout.addWidget(self.grupo)
        layout.addStretch()
 
    def retraducir(self, t):
        self.titulo.setText(t["ver_titulo"])
        self.grupo.setTitle(t["ver_grupo"])
        self.check_sidebar.setText(t["ver_sidebar"])
        self.check_pantalla.setText(t["ver_pantalla"])
        self.zoom_label.setText(t["ver_zoom"])
 

class settings_p(QWidget):
    idioma_cambiado = pyqtSignal(str)
    texto_cambiado = pyqtSignal(int)
    tema_cambiado = pyqtSignal(str)
    color_texto_cambiado = pyqtSignal(str)
    color_menu_cambiado = pyqtSignal(str)
    def __init__(self, parent = None, idioma = "es"):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        self.titulo = QLabel()
        self.titulo.setObjectName("TituloPagina")
        layout.addWidget(self.titulo)

        self.label_titulo = None

        # SECCIÓN DEL PERFIL
        perfil = QHBoxLayout()
        self.grupo_perfil = QGroupBox()
        self.grupo_perfil.setLayout(perfil)
        layout.addWidget(self.grupo_perfil)

        # IZQUIERDA - foto de perfil y selector de esta
        self.foto_layout = QVBoxLayout()
        self.foto_shaper = ImagenPerfil()
        self.foto_shaper.setObjectName("FotoPerfil")
        self.foto_archivo = SubidorArchivos()
        self.foto_layout.addWidget(self.foto_shaper, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.foto_layout.addWidget(self.foto_archivo)
        perfil.addLayout(self.foto_layout)

        self.foto_archivo.arch.connect(self.foto_shaper.carga_imagen)

        # DERECHA - zona para cambiar el nombre de perfil acual
        # DERECHA - zona para cambiar el nombre de perfil acual
        self.p_userData = QVBoxLayout()
        self.nombreHeader = QLabel("")
        self.p_userData.addWidget(self.nombreHeader)
        self.nombre_user = QLabel()
        self.nombre_user.setObjectName("NombreUsuarioLabel")
        self.nombre_upd = QPushButton("")
        self.p_userData.addWidget(self.nombre_user)
        self.p_userData.addWidget(self.nombre_upd)
        self.nombre_upd.clicked.connect(self.cambianombre)
        perfil.addLayout(self.p_userData)

        self.nom_upd_input = QLineEdit(self.nombre_user.text())
        self.nom_upd_input.setFixedWidth(self.width()//2 - 35)
        self.p_userData.addWidget(self.nom_upd_input)
        self.nom_upd_input.returnPressed.connect(lambda: self.nom_upd(self.nom_upd_input.text(), self.nom_upd_input))
        self.nom_upd_input.hide()

        layout.addWidget(self.linea_division())


        # SECCIÓN GENERAL
        general = QHBoxLayout()
        self.grupo_general = QGroupBox()
        self.grupo_general.setLayout(general)
        layout.addWidget(self.grupo_general)

        # IZQUIERDA - accesibilidad
        self.acces_layout = QVBoxLayout()
        self.Access_title = QLabel()
        self.idioma_title = QLabel()
        self.idioma_select = QComboBox()
        self.idioma_select.addItems(["español/es-ES", "English/en-US"])
        self.idioma_select.currentIndexChanged.connect(self.cambia_idioma)

        self.texto_title = QLabel()
        self.texto_select = QSpinBox()
        self.texto_select.setRange(8, 32)
        self.texto_select.setValue(12)
        self.texto_select.setSuffix(" pt")
        self.texto_select.valueChanged.connect(self.cambia_tamano)

        self.acces_layout.addWidget(self.Access_title)
        self.acces_layout.addWidget(self.idioma_title)
        self.acces_layout.addWidget(self.idioma_select)
        self.acces_layout.addWidget(self.texto_title)
        self.acces_layout.addWidget(self.texto_select)

        # DERECHA - apariencia
        self.apariencia_layout = QVBoxLayout()
        self.apariencia_title = QLabel()
        self.tema_title = QLabel()
        self.tema_select = QComboBox()
        self.tema_select.addItems(["Modo Claro", "Modo Oscuro"])
        self.tema_select.currentIndexChanged.connect(lambda index: self.color_upd("claro" if index == 0 else "oscuro"))

        self.text_color_title = QLabel()
        self.text_color_select = QFrame()
        self.text_color_select.setFixedSize(24, 24)
        self.text_color_select.setFrameShape(QFrame.Shape.Box)
        self.text_color_boton = QPushButton()
        self.text_color_boton.clicked.connect(self.cambia_color_texto)
        fila_color_texto = QHBoxLayout()
        fila_color_texto.addWidget(self.text_color_select)
        fila_color_texto.addWidget(self.text_color_boton)

        self.menu_color_title = QLabel()
        self.menu_color_select = QFrame()
        self.menu_color_select.setFixedSize(24, 24)
        self.menu_color_select.setFrameShape(QFrame.Shape.Box)
        self.menu_color_boton = QPushButton()
        self.menu_color_boton.clicked.connect(self.cambia_color_menu)
        fila_color_menu = QHBoxLayout()
        fila_color_menu.addWidget(self.menu_color_select)
        fila_color_menu.addWidget(self.menu_color_boton)

        self.apariencia_layout.addWidget(self.apariencia_title)
        self.apariencia_layout.addWidget(self.tema_title)
        self.apariencia_layout.addWidget(self.tema_select)
        self.apariencia_layout.addWidget(self.text_color_title)
        self.apariencia_layout.addLayout(fila_color_texto)
        self.apariencia_layout.addWidget(self.menu_color_title)
        self.apariencia_layout.addLayout(fila_color_menu)

        general.addLayout(self.acces_layout)
        general.addLayout(self.apariencia_layout)
        self.t = None

    def cambianombre(self):
        self.nom_upd_input.show()
        self.nombre_upd.hide()

    def cambia_idioma(self, index):
        resultado = "es" if index == 0 else "en"
        self.idioma_cambiado.emit(resultado)

    def cambia_tamano(self, pt):
        self.texto_cambiado.emit(pt)

    def color_upd(self, new_color):
        self.tema_cambiado.emit(new_color)

    def cambia_color_texto(self):
        color = QColorDialog.getColor(initial=self.text_color_select.palette().window().color(), parent=self, title="Seleccionar color de texto")
        if color.isValid():
            self.text_color_select.setStyleSheet(f"background-color: {color.name()};")
            self.color_texto_cambiado.emit(color.name())

    def cambia_color_menu(self):
        color = QColorDialog.getColor(initial=self.menu_color_select.palette().window().color(), parent=self, title="Seleccionar color de menú")
        if color.isValid():
            self.menu_color_select.setStyleSheet(f"background-color: {color.name()};")
            self.color_menu_cambiado.emit(color.name())

    def nom_upd(self, newName, input_place):
        if 1 <= len(newName.strip()) <= 40:
            self.nombre_user.setText(newName.strip())
            input_place.hide()
            self.nombre_upd.show()
            QMessageBox.information(self, self.t["msg_exito_titulo"], self.t["msg_exito_texto"])
        else:
            QMessageBox.warning(self, self.t["msg_error_titulo"], self.t["msg_error_texto"])


    def retraducir(self):
        self.titulo.setText(self.t["titulo_settings"])
        self.grupo_perfil.setTitle(self.t["grupo_perfil"])
        self.nombreHeader.setText(self.t["label_nombre"])
        self.nombre_upd.setText(self.t["boton_cambiar_nom"])
        self.nom_upd_input.setPlaceholderText(self.t["placeholder_nombre"])
        self.foto_archivo.t_perfil.setText(self.t["label_foto"])
        self.foto_archivo.boton.setText(self.t["boton_foto"])
        self.grupo_general.setTitle(self.t["apariencia_title"])
        self.tema_title.setText(self.t["tema_title"])
        self.Access_title.setText(self.t["acces_title"])
        self.text_color_title.setText(self.t["text_color_title"])
        self.menu_color_title.setText(self.t["menu_color_title"])
        self.texto_title.setText(self.t["texto_title"])
        self.idioma_title.setText(self.t["idioma_title"])
        self.text_color_boton.setText(self.t["texto_button"])
        self.menu_color_boton.setText(self.t["texto_button"])


    def linea_division(self):
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)      
        linea.setFrameShadow(QFrame.Shadow.Sunken)   
        return linea

class SubidorArchivos(QWidget):
    arch = pyqtSignal(str)
    def __init__(self, parent = None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Texto debajo
        self.t_perfil = QLabel("")
        layout.addWidget(self.t_perfil)

        self.boton = QPushButton("")
        self.boton.clicked.connect(self.foto_select)
        layout.addWidget(self.boton) 
        self.ruta = None


    def foto_select(self, entrada = None):
        if entrada and entrada is not None:
            ruta = entrada
        else:
            ruta, _ = QFileDialog.getOpenFileName(self, "seleccionar archivo", "", "Imágenes (*.png *.jpg *.jpeg);;")
        if ruta:
            if ruta and ruta.lower().endswith(('.png', '.jpg', '.jpeg')):
                
                self.ruta = ruta
                self.arch.emit(ruta)
            elif ruta:
                print("Foto no existE")

class ImagenPerfil(QLabel):
    def __init__(self, diametro=100, parent=None):
        super().__init__(parent)
        self.diametro = diametro
        self.setFixedSize(diametro, diametro)
        self.pixmap_o = None

    def carga_imagen(self, ruta_imagen):
        self.pixmap_o = QPixmap(ruta_imagen)
        self.setPixmap(self.recortar_circulo(self.pixmap_o))

    def recortar_circulo(self, pixmap):
        # Escala la imagen para llenar el círculo
        pixmap = pixmap.scaled(
            self.diametro, self.diametro,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        # Crea un pixmap nuevo con fondo transparente
        circular = QPixmap(self.diametro, self.diametro)
        circular.fill(Qt.GlobalColor.transparent)

        painter = QPainter(circular)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Define la forma circular como "molde" de recorte
        path = QPainterPath()
        path.addEllipse(0, 0, self.diametro, self.diametro)
        painter.setClipPath(path)

        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return circular

app = QApplication(sys.argv)
system = Sistema()
system.carga_sys()
system.show()
res = app.exec()
system.guardar_sys()
sys.exit(res)