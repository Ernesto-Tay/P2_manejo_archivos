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
    def __init__(self):
        self.formato = "<I32sI30s30s"
        self.tamano_registro = struct.calcsize(self.formato)
        self.info = None


    def cargar_posiciones(self):
        """Este método se encarga de cargar las posiciones del indice.json para buscarlas en el archivo de texto."""
        carpeta_datos = Path("info")
        try:
            with open(carpeta_datos / "indice.json", "r", encoding="utf-8") as a:
                datos = json.load(a)
                self.info = {int(k): v for k, v in datos.items()}
                return True, "Índice cargado correctamente", None
        except FileNotFoundError:
            self.info = {}
            return False, "No se encontró un índice, se iniciará el sistema con uno vacío.", None

    
    def calcular_posicion(self, id):
        """ Calcula la posición de una ID. Retorna \n1. False si no hay info cargada aún\n2. None si la posición no fue encontrada en los datos\n3. la cantidad de bytes que deben recorrerse antes de llegar al punto óptimo"""
        if self.info is None:
            return False

        posc = self.info.get(id, None)

        if posc is None: 
            return None

        return self.tamano_registro * posc


    def actualizar_info_json(self):
        carpeta_datos = Path("info") / "indice.json"
        tmp =  carpeta_datos.with_suffix(".tmp")
        with open(tmp, "w", encoding = "utf-8") as a:
            json.dump(self.info, a, indent = 4, ensure_ascii=False)
        tmp.replace(carpeta_datos)
            

    def anadir_entrada(self, id: int, nombre: str, tel: int, correo: str, ciudad: str):
        if id in self.info:
            return False, "Ya existe una entrada con esa ID", None
        if self.info is None:
            return False, "No se han encontrado datos en la sesión", None
        n_nombre = nombre.encode("utf-8").ljust(32, b" ")
        n_correo = correo.encode("utf-8").ljust(30, b" ")
        n_ciudad = ciudad.encode("utf-8").ljust(30, b" ")

        if len(n_nombre) > 32:
            return False, "El nombre excede los 32 bytes permitidos", None
        if len(n_correo) > 30:
            return False, "El correo excede los 30 bytes permitidos", None
        if len(n_ciudad) > 30:
            return False, "La ciudad excede los 30 bytes permitidos", None

        carpeta_datos = Path("info")
        carpeta_datos.mkdir(exist_ok=True)
        with open(carpeta_datos / "contactos.dat", "ab") as a:
            a.seek(0, os.SEEK_END)
            n_entrada = a.tell() // self.tamano_registro
            a.write(struct.pack(self.formato, id, n_nombre, tel, n_correo, n_ciudad))
            self.info[id] = n_entrada
            self.actualizar_info_json()
        return True, "Contacto añadido correctamente", None


    def modificar_entrada(self, id: int, nombre: str, tel: int, correo: str, ciudad: str):
        """Busca la entrada en los datos cargados y la edita en función de los nuevos datos. Devuelve: \n1. False, si no hay datos cargados\n2. None, si no se encontró\n3. True, si toddo salió bien"""
        n_nombre = nombre.ljust(32, " ").encode("utf-8")
        n_correo = correo.ljust(30, " ").encode("utf-8")
        n_ciudad = ciudad.ljust(30, " ").encode("utf-8")

        posc = self.calcular_posicion(id)
        if posc is False: return False, "No se han encontrado datos en la sesión", None
        if posc is None: return False, "El contacto no existe", None
        
        carpeta_datos = Path("info")
        carpeta_datos.mkdir(exist_ok=True)
        with open(carpeta_datos / "contactos.dat", "r+b") as a:
            a.seek(posc)
            a.write(struct.pack(self.formato, id, n_nombre, tel, n_correo, n_ciudad))

        return True, "Contacto editado correctamente", None


    def obtener_entrada(self, id):
        """Busca la entrada en los datos cargados. Devuelve:\n1. False, si no hay datos cargados\n2. None, si no se encuentra la entrada en el modelo de datos\n3. Los datos de la entrada buscada, si es encontrda"""
        if self.info is None: return False, "No se han encontrado datos en la sesión", None
        if not id in self.info:
            return False, "El contacto no fué encontrado", None
        carpeta_datos = Path("info")
        with open(carpeta_datos / "contactos.dat", "rb") as a:
            posc = self.calcular_posicion(id)
            a.seek(posc)
            block = a.read(self.tamano_registro)
            e_id, nombre, telefono, correo, ciudad = struct.unpack(self.formato, block)
            nombre = nombre.decode("utf-8").rstrip(" \x00")
            correo = correo.decode("utf-8").rstrip(" \x00")
            ciudad = ciudad.decode("utf-8").rstrip(" \x00")
            
        return True, "Contacto encontrado", (e_id, nombre, telefono, correo, ciudad)


    def generar_json(self):
        """Convierte los contactos a un json llamado registros.json. Devuelve:\n1. False - 2, no se pudo almacenar información. \n2. False - 1, si no se encontró la carpeta con los datos\n3. True - 0, si los datos fueron correctamente generados a JSON"""
        carpeta_datos = Path("info")
        try:
            with open(carpeta_datos / "contactos.dat", "rb") as a:
                resultado = {}
                while True:
                    linea = a.read(self.tamano_registro)
                    if not linea: break
                    e_id, nombre, telefono, correo, ciudad = struct.unpack(self.formato, linea)
                    nombre = nombre.decode("utf-8").rstrip(" \x00")
                    correo = correo.decode("utf-8").rstrip(" \x00")
                    ciudad = ciudad.decode("utf-8").rstrip(" \x00")

                    resultado[e_id] ={
                        "nombre": nombre,
                        "telefono": telefono,
                        "correo": correo,
                        "ciudad": ciudad
                    }

            if resultado == {}:
                return False, "No hay datos para guardar", None

            with open(carpeta_datos / "registros.json", "w", encoding = "utf-8") as j:
                json.dump(resultado, j, indent = 4, ensure_ascii=False)

            return True, "Datos guardados correctamente", None
        except FileNotFoundError:
            return False, "No se ha encontrado el modelo de datos", None