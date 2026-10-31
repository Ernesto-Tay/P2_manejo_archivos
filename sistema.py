from herramientas import Herramientas
from exportar import pdf_maker
from contactos import ContactosMng

class Admin_pdfs:
    def __init__(self):
        self.manejo_pdf = pdf_maker()


class AdminContactos:
    def __init__(self):
        self.manejo_contactos = ContactosMng()