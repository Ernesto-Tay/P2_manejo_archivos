"""
FUNCIONES:
- Exportar contactos a JSON
- Generar un PDF con los contactos almacenados

El PDF debe generarse en base al JSON, y también debe almacenar la fecha de creación
"""
import json

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from pathlib import Path
import os
from datetime import datetime

class pdf_maker:
    def __init__(self):
        self.datos = None
        self.altura = 560
        self.ancho_id = 40
        self.ancho_nombre = 105
        self.ancho_telefono = 290
        self.ancho_correo = 365
        self.ancho_ciudad = 550
        self.formato_titulo = ["Helvetica-Bold", 20, 30]
        self.formato_fecha = ["Helvetica", 10, 25]
        self.formato_encabezado = ["Helvetica-BoldOblique", 15, 20]
        self.formato_normal = ["Helvetica", 12, 12]

    def tener_datos(self) -> bool:
        """ Retorna True si ya se generó el registro como un JSON,
            False si aún no ha sido creado."""
        path = Path("info")
        try:
            with open(path / "registros.json", "r", encoding="utf-8") as f:
                self.datos = json.load(f)
                return True
        except FileNotFoundError:
            return False


    def formatear_pdf(self):
        """ Crea el PDF de empleados. Es necesario crear el JSON de empleados y pasarlo como diccionario a \"self.datos\" para el funcionamiento. De lo contrario, esta función no hará nada."""
        if not self.tener_datos(): return False, "No se ha creado el JSON requerido", None
        os.makedirs("info", exist_ok=True)
        path = os.path.join("info", "reporte_contactos.pdf")
        pdf = canvas.Canvas(path, pagesize = landscape(letter), initialFontSize = 12)
        y = self.altura

        # imprime el título del reporte
        pdf.setFont(self.formato_titulo[0], self.formato_titulo[1])
        pdf.drawString(self.ancho_id, y, "REPORTE DE EMPLEADOS")
        y-= self.formato_titulo[2]

        # imprime las fechas
        pdf.setFont(self.formato_fecha[0], self.formato_fecha[1])
        pdf.drawString(self.ancho_id, y, f"Generado el {datetime.now():%d/%m/%Y a las %H:%M}")
        y -= self.formato_fecha[2]

        # imprime los encabezados
        pdf.setFont(self.formato_encabezado[0], self.formato_encabezado[1])
        pdf.drawString(self.ancho_id, y, "ID")
        pdf.drawString(self.ancho_nombre, y, "NOMBRE")
        pdf.drawString(self.ancho_telefono, y, "TELÉFONO")
        pdf.drawString(self.ancho_correo, y, "CORREO ELECTRÓNICO")
        pdf.drawString(self.ancho_ciudad, y, "CIUDAD")
        y -= self.formato_encabezado[2]
        pdf.setFont(self.formato_normal[0], self.formato_normal[1])

        # imprime los datos, entrada por entrada (de acuerdo con el orden del JSON, basado en el orden de entrada)
        for id, datos in self.datos.items():
            pdf.drawString(self.ancho_id, y, str(id))
            pdf.drawString(self.ancho_nombre, y, datos["nombre"])
            pdf.drawString(self.ancho_telefono, y, str(datos["telefono"]))
            pdf.drawString(self.ancho_correo, y, datos["correo"])
            pdf.drawString(self.ancho_ciudad, y, datos["ciudad"])
            y -= self.formato_normal[2]

            if y < 50:
                pdf.showPage()
                y=self.altura
                pdf.setFont(self.formato_encabezado[0], self.formato_encabezado[1])
                pdf.drawString(self.ancho_id, y, "ID")
                pdf.drawString(self.ancho_nombre, y, "NOMBRE")
                pdf.drawString(self.ancho_telefono, y, "TELÉFONO")
                pdf.drawString(self.ancho_correo, y, "CORREO ELECTRÓNICO")
                pdf.drawString(self.ancho_ciudad, y, "CIUDAD")
                y -= self.formato_encabezado[2]
                pdf.setFont(self.formato_normal[0], self.formato_normal[1])
        try:
            pdf.save()
        except OSError as e:
            return False, f"No se pudo guardar el PDF (¿está abierto en otro programa?): {e}", None
        return True, f"Reporte creado correctamente en {path}", None