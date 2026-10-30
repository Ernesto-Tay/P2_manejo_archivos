"""
FUNCIONES:
- Verificar integridad de los datos
- Respaldar datos con un ZIP
- Obtener información del sistema

para verificar la integridad, debe de utilizarse el hash SHA-256 y compararlo con el hash previo de los datos (se debe guardar en datos.sha256)
si se actualiza la información, se actualiza el hash
si no coincide la verificación de integridad, se da un aviso al usuario
el nombre de la carpeta conteniendo cada backup se crea con "backup_[fecha de creación]"
El backup debe contener:
- archivo BIN de los contactos guardados
- archivo JSON que conecta cada ID de los contactos con la posición en la que fueron insertados
- archivo JSON con los contactos (si existe)
- archivo PDF con el reporte de los contactos (si existe)

Se debe retornar tuplas con los siguientes valores:
- Estatus de función (éxito o fracaso)
- Descripción del resultado
- Datos obtenidos con la función (con el fin de hacerles Display con una interfaz posteriormente)


para la información del sistema (del archivo BIN con los contactos), deben verse los metadatos del archivo (fecha creación, permisos, tamaño...)


"""
from hashlib import sha256
from pathlib import Path
import zipfile, stat
import os
from datetime import datetime
class Herramientas:
    def __init__(self):
        self.backups_carpeta = Path("respaldos")
        self.hash_backup = "backup_hash.txt"
        self.archivo_bin = Path("contactos.dat")
        self.archivo_ids = Path("indice.json")
        self.archivo_contactos = Path("registros.json")  # opcional
        self.archivo_reporte = Path("Reporte_contactos.pdf")  # opcional
        self.archivo_hash = Path("datos.sha256")

    @staticmethod
    def _calcular_hash(ruta):
        """Calcula el SHA-256 de un archivo leyéndolo por bloques."""
        h = sha256()
        with open(ruta, "rb") as f:
            for bloque in iter(lambda: f.read(65536), b""):
                h.update(bloque)
        return h.hexdigest()

    @staticmethod
    def _fmt_fecha(timestamp):
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def _ruta_hash_backups(self):
        return self.backups_carpeta / self.hash_backup

    def _leer_hashes_backups(self):
        ruta = self._ruta_hash_backups()
        hashes = {}
        if ruta.exists():
            for linea in ruta.read_text(encoding="utf-8").splitlines():
                if ":" in linea:
                    nombre, h = linea.rsplit(":", 1)
                    hashes[nombre.strip()] = h.strip()
        return hashes


    def actualizar_hash(self):
        """Recalcula y guarda el hash del BIN. Llamar cada vez que se actualicen los datos."""
        try:
            if not self.archivo_bin.exists():
                return (False, f"No existe el archivo {self.archivo_bin}", None)
            h = self._calcular_hash(self.archivo_bin)
            self.archivo_hash.write_text(h, encoding="utf-8")
            return (True, "Hash actualizado correctamente", {"hash": h})
        except OSError as e:
            return (False, f"Error al actualizar el hash: {e}", None)


    def verificar_integridad(self):
        """Compara el hash actual del BIN con el guardado en datos.sha256."""
        try:
            if not self.archivo_bin.exists():
                return (False, f"No existe el archivo {self.archivo_bin}", None)

            actual = self._calcular_hash(self.archivo_bin)

            if not self.archivo_hash.exists():
                # Primera vez: no hay hash previo, se crea
                self.archivo_hash.write_text(actual, encoding="utf-8")
                return (True, "No había hash previo; se creó uno nuevo",
                        {"hash_actual": actual, "hash_previo": None, "coincide": True})

            previo = self.archivo_hash.read_text(encoding="utf-8").strip()
            coincide = (actual == previo)
            datos = {"hash_actual": actual, "hash_previo": previo, "coincide": coincide}

            if coincide:
                return (True, "Integridad verificada: los datos no han sido modificados", datos)
            return (False, "AVISO: el hash no coincide, los datos pudieron ser alterados o corrompidos", datos)
        except OSError as e:
            return (False, f"Error al verificar la integridad: {e}", None)


    def hacer_backup(self, forzar=False):
        """
        Crea respaldos/backup_[fecha].zip que contiene la carpeta backup_[fecha]/ con:
        BIN, JSON de IDs/posiciones, y (si existen) JSON de contactos y PDF de reporte.
        Si la integridad falla, no respalda salvo que forzar=True.
        """
        try:
            ok, desc, datos_int = self.verificar_integridad()
            if not ok and not forzar:
                return (False, f"Backup cancelado. {desc}", datos_int)

            if not self.archivo_ids.exists():
                return (False, f"Falta el archivo obligatorio {self.archivo_ids}", None)

            fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nombre_carpeta = f"backup_{fecha}"
            self.backups_carpeta.mkdir(exist_ok=True)
            ruta_zip = self.backups_carpeta / f"{nombre_carpeta}.zip"

            obligatorios = [self.archivo_bin, self.archivo_ids]
            opcionales = [self.archivo_contactos, self.archivo_reporte]
            incluidos = [a for a in obligatorios + opcionales if a.exists()]
            omitidos = [a.name for a in opcionales if not a.exists()]

            with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as z:
                for archivo in incluidos:
                    z.write(archivo, arcname=f"{nombre_carpeta}/{archivo.name}")

            # Guardar el hash del ZIP para poder evaluarlo después
            hash_zip = self._calcular_hash(ruta_zip)
            with open(self._ruta_hash_backups(), "a", encoding="utf-8") as f:
                f.write(f"{ruta_zip.name}:{hash_zip}\n")

            datos = {
                "ruta": str(ruta_zip),
                "carpeta": nombre_carpeta,
                "archivos_incluidos": [a.name for a in incluidos],
                "archivos_omitidos": omitidos,
                "hash_zip": hash_zip,
                "tamano_bytes": ruta_zip.stat().st_size,
                "integridad_origen": ok,
            }
            msg = "Backup creado correctamente"
            if not ok:
                msg += " (ADVERTENCIA: se forzó con datos que no pasaron la verificación)"
            return (True, msg, datos)
        except (OSError, zipfile.BadZipFile) as e:
            return (False, f"Error al crear el backup: {e}", None)


    def evaluar_backup(self, ruta_zip):
        """Verifica que el ZIP no esté corrupto, tenga los archivos obligatorios y su hash coincida."""
        try:
            ruta_zip = Path(ruta_zip)
            if not ruta_zip.exists():
                return (False, f"No existe el backup {ruta_zip}", None)

            with zipfile.ZipFile(ruta_zip, "r") as z:
                corrupto = z.testzip()
                nombres = [Path(n).name for n in z.namelist()]

            if corrupto:
                return (False, f"Archivo corrupto dentro del ZIP: {corrupto}", None)

            faltantes = [a.name for a in (self.archivo_bin, self.archivo_ids) if a.name not in nombres]
            if faltantes:
                return (False, f"Al backup le faltan archivos obligatorios: {faltantes}", {"faltantes": faltantes})

            hash_actual = self._calcular_hash(ruta_zip)
            hash_guardado = self._leer_hashes_backups().get(ruta_zip.name)
            datos = {"hash_actual": hash_actual, "hash_guardado": hash_guardado, "archivos": nombres}

            if hash_guardado is None:
                return (True, "Backup válido, pero no hay hash registrado para compararlo", datos)
            if hash_actual != hash_guardado:
                return (False, "AVISO: el hash del backup no coincide, pudo haber sido modificado", datos)
            return (True, "Backup válido e íntegro", datos)
        except (OSError, zipfile.BadZipFile) as e:
            return (False, f"Error al evaluar el backup: {e}", None)


    def extraer_info_del_backup(self, ruta_zip=None):
        """
        Si se da ruta_zip, retorna el detalle de ese backup (archivos, tamaños, fechas).
        Si no, lista todos los backups existentes en la carpeta de respaldos.
        """
        try:
            if ruta_zip is None:
                if not self.backups_carpeta.exists():
                    return (False, "Aún no existen backups", None)
                zips = sorted(self.backups_carpeta.glob("backup_*.zip"))
                lista = [{"nombre": z.name,
                          "tamano_bytes": z.stat().st_size,
                          "fecha_modificacion": self._fmt_fecha(z.stat().st_mtime)} for z in zips]
                return (True, f"Se encontraron {len(lista)} backups", {"backups": lista})

            ruta_zip = Path(ruta_zip)
            if not ruta_zip.exists():
                return (False, f"No existe el backup {ruta_zip}", None)

            with zipfile.ZipFile(ruta_zip, "r") as z:
                archivos = []
                for info in z.infolist():
                    if info.is_dir():
                        continue
                    archivos.append({
                        "nombre": Path(info.filename).name,
                        "tamano_bytes": info.file_size,
                        "tamano_comprimido": info.compress_size,
                        "fecha_modificacion": datetime(*info.date_time).strftime("%Y-%m-%d %H:%M:%S"),
                    })

            datos = {
                "backup": ruta_zip.name,
                "fecha_creacion": self._fmt_fecha(ruta_zip.stat().st_mtime),
                "tamano_bytes": ruta_zip.stat().st_size,
                "archivos": archivos,
            }
            return (True, "Información del backup obtenida", datos)
        except (OSError, zipfile.BadZipFile) as e:
            return (False, f"Error al leer el backup: {e}", None)

    def obtener_info_del_sistema(self):
        """Metadatos del archivo BIN de contactos: fechas, permisos, tamaño, etc."""
        try:
            if not self.archivo_bin.exists():
                return (False, f"No existe el archivo {self.archivo_bin}", None)

            st = self.archivo_bin.stat()

            # Fecha de creación: en Windows es st_ctime; en macOS st_birthtime;
            # en Linux generalmente no está disponible (st_ctime es cambio de metadatos)
            if hasattr(st, "st_birthtime"):
                creacion = st.st_birthtime
            elif os.name == "nt":
                creacion = st.st_ctime
            else:
                creacion = None

            datos = {
                "nombre": self.archivo_bin.name,
                "ruta_absoluta": str(self.archivo_bin.resolve()),
                "tamano_bytes": st.st_size,
                "tamano_kb": round(st.st_size / 1024, 2),
                "fecha_creacion": self._fmt_fecha(creacion) if creacion else "No disponible en este sistema",
                "fecha_modificacion": self._fmt_fecha(st.st_mtime),
                "fecha_ultimo_acceso": self._fmt_fecha(st.st_atime),
                "permisos": stat.filemode(st.st_mode),
                "permisos_octal": oct(stat.S_IMODE(st.st_mode)),
                "lectura": os.access(self.archivo_bin, os.R_OK),
                "escritura": os.access(self.archivo_bin, os.W_OK),
                "ejecucion": os.access(self.archivo_bin, os.X_OK),
            }
            if hasattr(st, "st_uid"):  # solo en sistemas tipo Unix
                datos["uid_propietario"] = st.st_uid
                datos["gid_grupo"] = st.st_gid

            return (True, "Información del sistema obtenida", datos)
        except OSError as e:
            return (False, f"Error al obtener la información del sistema: {e}", None)