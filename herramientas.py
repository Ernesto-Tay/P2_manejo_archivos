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
import json, shutil, tempfile, zlib
from datetime import datetime
class Herramientas:
    def __init__(self):
        # ContactosMng y pdf_maker guardan todo dentro de la carpeta "info"
        carpeta_datos = Path("info")
        self.backups_carpeta = Path("respaldos")
        self.hash_backup = "backup_hash.txt"
        self.archivo_bin = carpeta_datos / "contactos.dat"
        self.archivo_ids = carpeta_datos / "indice.json"
        self.archivo_contactos = carpeta_datos / "registros.json"  # opcional
        self.archivo_reporte = carpeta_datos / "reporte_contactos.pdf"  # opcional
        self.archivo_hash = carpeta_datos / "datos.sha256"

    @staticmethod
    def _calcular_hash(ruta):
        """Calcula el SHA-256 de un archivo leyéndolo por bloques."""
        h = sha256()
        with open(ruta, "rb") as f:
            for bloque in iter(lambda: f.read(65536), b""):
                h.update(bloque)
        return h.hexdigest()

    @staticmethod
    def _calcular_crc32(ruta):
        """Calcula el CRC-32 de un archivo (el mismo que guarda el ZIP) leyéndolo por bloques."""
        crc = 0
        with open(ruta, "rb") as f:
            for bloque in iter(lambda: f.read(65536), b""):
                crc = zlib.crc32(bloque, crc)
        return crc

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

    def restaurar_backup(self, ruta_zip, tamano_registro=None):
        """
        Recupera los archivos de datos desde un backup ZIP creado con hacer_backup().
        1. Evalúa el ZIP (que no esté corrupto, que tenga lo obligatorio y que su hash coincida).
        2. Extrae solo los archivos conocidos a una carpeta temporal y revisa que el índice
           y el BIN sean coherentes entre sí (si se da tamano_registro).
        3. Respalda el estado actual (respaldos/backup_[fecha].zip) por si hay que volver atrás.
        4. Reemplaza los archivos; si algo falla a la mitad, deja todo como estaba.
        5. Actualiza datos.sha256 con el hash del BIN restaurado.
        Los archivos opcionales (JSON de contactos, PDF) que el backup no traiga se dejan intactos.
        """
        conocidos = {a.name: a for a in (self.archivo_bin, self.archivo_ids,
                                         self.archivo_contactos, self.archivo_reporte)}
        try:
            ruta_zip = Path(ruta_zip)
            ok, desc, datos_eval = self.evaluar_backup(ruta_zip)
            if not ok:
                return (False, f"Restauración cancelada. {desc}", datos_eval)

            with tempfile.TemporaryDirectory(prefix="restaurar_") as carpeta:
                carpeta = Path(carpeta)
                extraidos = {}
                with zipfile.ZipFile(ruta_zip, "r") as z:
                    for info in z.infolist():
                        # Solo se usa el nombre final y solo de los archivos conocidos:
                        # así una ruta como "../../x" dentro del ZIP nunca se escribe en disco.
                        nombre = Path(info.filename).name
                        if info.is_dir() or nombre not in conocidos or nombre in extraidos:
                            continue
                        with z.open(info) as origen, open(carpeta / nombre, "wb") as destino:
                            shutil.copyfileobj(origen, destino)
                        extraidos[nombre] = carpeta / nombre

                # --- el índice y el BIN del backup deben ser coherentes ---
                try:
                    indice = json.loads(extraidos[self.archivo_ids.name].read_text(encoding="utf-8"))
                    posiciones = {int(k): int(v) for k, v in indice.items()}
                except (ValueError, TypeError, AttributeError):
                    return (False, "Restauración cancelada: el índice del backup está dañado", None)
                if tamano_registro:
                    n = len(posiciones)
                    tam_bin = extraidos[self.archivo_bin.name].stat().st_size
                    if tam_bin != n * tamano_registro or sorted(posiciones.values()) != list(range(n)):
                        return (False, "Restauración cancelada: el índice del backup no coincide con "
                                       "el archivo de contactos", {"contactos_en_indice": n, "bytes_bin": tam_bin})

                # --- respaldo del estado actual, por si hay que volver atrás ---
                previo = None
                if self.archivo_bin.exists():
                    ok_prev, desc_prev, datos_prev = self.hacer_backup(forzar=True)
                    if not ok_prev:
                        return (False, f"Restauración cancelada: no se pudo respaldar el estado actual. {desc_prev}", None)
                    previo = datos_prev["ruta"]

                # --- reemplazo de archivos, con reversa si algo falla ---
                self.archivo_bin.parent.mkdir(exist_ok=True)
                originales, reemplazados = {}, []
                try:
                    for nombre, origen in extraidos.items():
                        destino = conocidos[nombre]
                        if destino.exists():
                            originales[destino] = carpeta / f"original_{nombre}"
                            shutil.copyfile(destino, originales[destino])
                        nuevo = destino.with_name(destino.name + ".nuevo")
                        shutil.copyfile(origen, nuevo)
                        os.replace(nuevo, destino)
                        reemplazados.append(destino)
                except OSError as e:
                    for destino in reemplazados:
                        if destino in originales:
                            shutil.copyfile(originales[destino], destino)
                        else:
                            destino.unlink(missing_ok=True)
                    for destino in conocidos.values():
                        destino.with_name(destino.name + ".nuevo").unlink(missing_ok=True)
                    return (False, f"Error al restaurar; los datos quedaron como estaban: {e}", None)

            ok_hash, desc_hash, _ = self.actualizar_hash()
            restaurados = sorted(extraidos)
            conservados = sorted(n for n in conocidos if n not in extraidos and conocidos[n].exists())
            datos = {
                "backup": ruta_zip.name,
                "contactos_restaurados": len(posiciones),
                "archivos_restaurados": restaurados,
                "archivos_conservados_sin_cambios": conservados,
                "respaldo_del_estado_anterior": previo,
                "hash_del_backup_verificado": datos_eval.get("hash_guardado") is not None,
            }
            msg = f"Backup restaurado: {len(posiciones)} contactos recuperados"
            if previo:
                msg += f". El estado anterior quedó guardado en {previo}"
            if datos_eval.get("hash_guardado") is None:
                msg += " (aviso: no había hash registrado para este backup, no se pudo comprobar su origen)"
            if not ok_hash:
                msg += f" (aviso: {desc_hash})"
            return (True, msg, datos)
        except (OSError, zipfile.BadZipFile) as e:
            return (False, f"Error al restaurar el backup: {e}", None)

    def comparar_con_backup(self, ruta_zip):
        """
        Compara cada archivo de un backup ZIP con su original actual (tamaño y CRC-32).
        Es de solo lectura: no modifica nada. Una diferencia es lo esperado si los datos
        cambiaron después de crear el backup.
        """
        originales = {a.name: a for a in (self.archivo_bin, self.archivo_ids,
                                          self.archivo_contactos, self.archivo_reporte)}
        try:
            filas = []
            with zipfile.ZipFile(ruta_zip, "r") as z:
                for info in z.infolist():
                    nombre = Path(info.filename).name
                    if info.is_dir() or nombre not in originales:
                        continue
                    orig = originales[nombre]
                    fila = {"archivo": nombre, "tamano_backup": info.file_size,
                            "tamano_comprimido": info.compress_size}
                    if not orig.exists():
                        fila.update(tamano_actual=None, estado="el original ya no existe")
                    else:
                        fila["tamano_actual"] = orig.stat().st_size
                        igual = (fila["tamano_actual"] == info.file_size
                                 and self._calcular_crc32(orig) == info.CRC)
                        fila["estado"] = "igual" if igual else "DIFERENTE"
                    filas.append(fila)

            if not filas:
                return (False, "El ZIP no contiene archivos reconocidos de este sistema", None)
            todo_igual = all(f["estado"] == "igual" for f in filas)
            if todo_igual:
                return (True, "Los archivos actuales coinciden con el backup", {"archivos": filas})
            return (False, "Hay diferencias entre los archivos actuales y el backup "
                           "(es lo esperado si los datos cambiaron después de crearlo)", {"archivos": filas})
        except (OSError, zipfile.BadZipFile) as e:
            return (False, f"Error al comparar con el backup: {e}", None)

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