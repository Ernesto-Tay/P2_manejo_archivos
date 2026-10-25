"""
FUNCIONES:
- Exportar contactos a JSON
- Generar un PDF con los contactos almacenados

El PDF debe generarse en base al JSON, y también debe almacenar la fecha de creación
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class pdf_maker:
    def __init__(self):
        self.datos = None
        self.altura = 750
        self.ancho_id = 100
        self.ancho_nombre = 150
        self.ancho_telefono = 250
        self.archo_correo = 300
        self.ancho_ciudad = 400
        self.formato_titulo = ["Helvetica-Bold", 20, 30]
        self.formato_encabezado = ["Helvetica-BoldOblique", 15, 20]
        self.formato_normal = ["Helvetica", 12, 12]

    def tener_datos(self) -> bool:
        """ Retorna True si ya se adjuntó la información del registro del JSON,
            False si aún no ha sido añadida."""
        return self.datos is not None


    def formatear_pdf(self):
        """ Crea el PDF de empleados. Es necesario crear el JSON de empleados y pasarlo como diccionario a \"self.datos\" para el funcionamiento. De lo contrario, esta función no hará nada."""
        if not self.tener_datos(): return
        pdf = canvas.Canvas("Reporte_contactos.pdf", pagesize = letter, initialFontName = "Helvetica", initialFontSize = 12)
        y = self.altura

        # imprime el título del reporte
        pdf.setFont(self.formato_titulo[0], self.formato_titulo[1])
        pdf.drawString(self.ancho_id, y, "REPORTE DE EMPLEADOS")
        y-= self.formato_titulo[2]

        # imprime los encabezados
        pdf.setFont(self.formato_encabezado[0], self.formato_encabezado[1])
        pdf.drawString(self.ancho_id, y, "ID")
        pdf.drawString(self.ancho_nombre, y, "NOMBRE")
        pdf.drawString(self.ancho_telefono, y, "TELÉFONO")
        pdf.drawString(self.ancho_correo, y, "CORREO ELECTRÓNICO")
        pdf.drawString(self.ancho_ciudad, y, "CIUDAD")
        Y -= self.formato_encabezado[2]
        pdf.setFont(self.formato_normal[0], self.formato_normal[1])

        # imprime los datos, entrada por entrada (de acuerdo con el orden del JSON, basado en el orden de entrada)
        for id, datos in self.datos:
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
                Y -= self.formato_encabezado[2]
                pdf.setFont(self.formato_normal[0], self.formato_normal[1])




    
