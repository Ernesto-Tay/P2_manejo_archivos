"""
FUNCIONES:
- Agregar contacto
- Buscar contactos por ID
- Modificar contacto

cada contacto tiene: ID, Nombre, Teléfono, Correo, Ciudad
Largo de los registros: 100 en total (4, 32, 4, 30, 30)
Se rellenan con espacios en blanco
se guardan en un .txt, y se busca con Tell(), seek() y así

EDICIÓN: solo se sobreescribe el registro modificado, no todo el archivo
Se accede a un 'indice.json' (bitácora de no. de entrada), aparte del JSON principal.
Nomenclatura indice.json -> id : no.registro
se utiliza esta nomenclatura para acceder rápidamente a un registro
"""
import struct
import os
from pathlib import Path
import json
class ContactosMng:
    def __init___(self):
        self.formato = "<I32sI30s30s"
        self.tamano_registro = struct.calcsize(self.formato)
        self.info = None


    def cargar_posiciones(self):
        """Este método se encarga de cargar las posiciones del indice.json para buscarlas en el archivo de texto."""
        carpeta_datos = Path("info")
        with open(carpeta_datos / "indice.json", "r", encoding="utf-8") as a:
            datos = json.load(a)
            self.info = datos

    
    def calcular_posicion(self, id):
        if self.info is None:
            return False

        posc = self.info.get(id, None)

        if posc is None: 
            return None

        return self.tamano_registro * (posc - 1) 


    def actualizar_info_json(self):
        carpeta_datos = Path("info")
        with open(carpeta_datos / "indice.json", "w", encoding = "utf-8") as a:
            json.dump(self.info, a, indent = 4, ensure_ascii=False)
            

    def anadir_entrada(self, id: int, nombre: str, tel: int, correo: str, ciudad: str):
        if self.info.get(id, False):
            return False # ya existe una entrada 
        n_nombre = nombre.ljust(32, " ").encode("utf-8")
        n_correo = correo.ljust(30, " ").encode("utf-8")
        n_ciudad = ciudad.ljust(30, " ").encode("utf-8")
        
        carpeta_datos = Path("info")
        with open(carpeta_datos / "contactos.dat", "ab") as a:
            a.read()
            n_entrada = a.tell() / self.tamano_registro
            self.info[id] = n_entrada
            a.write("<I", id)
            a.write("<32S", n_nombre)
            a.write("<I", tel)
            a.write("<30s", n_correo)
            a.write("<30s", n_ciudad)


    def modificar_entrada(self, id: int, nombre: str, tel: int, correo: str, ciudad: str):
        n_nombre = nombre.ljust(32, " ").encode("utf-8")
        n_correo = correo.ljust(30, " ").encode("utf-8")
        n_ciudad = ciudad.ljust(30, " ").encode("utf-8")

        posc = self.calcular_posicion(id)
        
        carpeta_datos = Path("info")
        with open(carpeta_datos / "contactos.dat", "r+b") as a:
            a.seek(posc)
            a.write("<I", id)
            a.write("<32S", n_nombre)
            a.write("<I", tel)
            a.write("<30s", n_correo)
            a.write("<30s", n_ciudad)


    def obtener_entrada(self, id):
        if not self.info.get(id, False):
            return None
        carpeta_datos = Path("info")
        with open(carpeta_datos / "contactos.dat", "rb") as a:
            posc = self.calcular_posicion(id)
            a.seek(posc)
            e_id = a.read(4).decode("utf-8")
            nombre = a.read(24).decode("utf-8").rstrip()
            telefono = a.read(11).decode("utf-8").rstrip()
            correo = a.read(30).decode("utf-8").rstrip()
            ciudad = a.read(30).decode("utf-8").rstrip()
            
        return e_id, nombre, telefono, correo, ciudad


    def generar_json(self):
        carpeta_datos = Path("info")
        with open(carpeta_datos / "contactos.dat", "rb") as a:
            resultado = {}
            posc = 0
            while True:
                a.seek(posc)

                e_id = a.read(4).decode("utf-8")
                if not e_id: break
                nombre = a.read(32).decode("utf-8").rstrip()
                telefono = a.read(4).decode("utf-8").rstrip()
                correo = a.read(30).decode("utf-8").rstrip()
                ciudad = a.read(30).decode("utf-8").rstrip()

                resultado[e_id] ={
                    "nombre": nombre,
                    "telefono": telefono,
                    "correo": correo,
                    "ciudad": ciudad
                }


        with open(carpeta_datos / "registros.json", "w", encoding = "utf-8") as j:
            json.dump(resultado, j, indent = 4, ensure_ascii=False)