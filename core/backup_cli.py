import os
import zipfile
from datetime import datetime, timedelta
import paramiko
import yaml


class BackupCLI:
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = None
        self.ssh_client = None
        self.mysql_data_path = "/var/lib/mysql"
        self.mysql_service_name = "mysql"
        self.running = True

    def display_menu(self):
        print("\n" + "="*50)
        print("    GESTIÓN DE BACKUPS")
        print("="*50)
        print("1. Ejecutar backup completo")
        print("2. Validar configuración YAML")
        print("3. Probar conexión SSH")
        print("4. Solo backup de MySQL")
        print("5. Solo backup de directorios")
        print("6. Limpiar backups antiguos")
        print("7. Ver información de configuración")
        print("0. Volver al menú principal")
        print("-"*50)

    def load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                self.config = yaml.safe_load(file)
                return True
        except FileNotFoundError:
            print(f"[ERROR] No se encontró {self.config_path}")
            return False
        except yaml.YAMLError as e:
            print(f"[ERROR] Error en {self.config_path}: {e}")
            return False

    def validate_config_option(self):
        print("\nVALIDAR CONFIGURACIÓN YAML")
        print("-" * 40)

        if not self.load_config():
            return

        try:
            required_sections = ['vps', 'backup']
            missing_sections = []

            for section in required_sections:
                if section not in self.config:
                    missing_sections.append(section)

            if missing_sections:
                print(f"[ERROR] Secciones faltantes: {', '.join(missing_sections)}")
                return

            print("[OK] Estructura YAML válida")

            vps_config = self.config['vps']
            required_vps_keys = ['ip', 'user', 'key_path']

            for key in required_vps_keys:
                if key not in vps_config:
                    print(f"[ERROR] Falta clave VPS: {key}")
                    return
                elif not vps_config[key]:
                    print(f"[ERROR] Valor vacío para VPS: {key}")
                    return

            print("[OK] Configuración VPS válida")

            if not os.path.exists(vps_config['key_path']):
                print(f"[ERROR] Archivo de clave SSH no encontrado: {vps_config['key_path']}")
                return

            print("[OK] Archivo de clave SSH encontrado")

            backup_config = self.config['backup']
            if 'local_save_path' not in backup_config:
                print("[ERROR] Falta 'local_save_path' en configuración backup")
                return

            if 'remote_folders' not in backup_config:
                print("[ERROR] Falta 'remote_folders' en configuración backup")
                return

            print("[OK] Configuración de backup válida")

            mysql_config = self.config.get('mysql', {})
            if mysql_config.get('enabled', False):
                print("[OK] MySQL backup está habilitado")
            else:
                print("[INFO] MySQL backup está deshabilitado")

            print("\n[✓] Configuración completamente válida")

        except Exception as e:
            print(f"[ERROR] Error validando configuración: {e}")

    def show_config_info_option(self):
        print("\nINFORMACIÓN DE CONFIGURACIÓN")
        print("-" * 40)

        if not self.load_config():
            return

        try:
            vps_config = self.config['vps']
            print(f"📡 Servidor VPS:")
            print(f"   IP: {vps_config.get('ip', 'No configurado')}")
            print(f"   Usuario: {vps_config.get('user', 'No configurado')}")
            print(f"   Clave SSH: {vps_config.get('key_path', 'No configurado')}")

            backup_config = self.config['backup']
            print(f"\n💾 Configuración de Backup:")
            print(f"   Carpeta local: {backup_config.get('local_save_path', 'No configurado')}")

            remote_folders = backup_config.get('remote_folders', [])
            print(f"   Directorios remotos ({len(remote_folders)}):")
            for folder in remote_folders:
                print(f"     • {folder}")

            mysql_config = self.config.get('mysql', {})
            print(f"\n🗄️ MySQL Backup:")
            enabled = mysql_config.get('enabled', False)
            print(f"   Estado: {'✅ Habilitado' if enabled else '❌ Deshabilitado'}")
            if enabled:
                print(f"   Nombre backup: {mysql_config.get('backup_name', 'Auto-generado')}")
                restart = mysql_config.get('restart_after_backup', True)
                print(f"   Reiniciar después: {'✅ Sí' if restart else '❌ No'}")

            settings = self.config.get('settings', {})
            if settings:
                print(f"\n⚙️ Configuraciones:")
                keep_remote = settings.get('keep_remote_copies', False)
                print(f"   Mantener copias remotas: {'✅ Sí' if keep_remote else '❌ No'}")

        except Exception as e:
            print(f"[ERROR] Error mostrando configuración: {e}")

    def establish_connection(self):
        if self.ssh_client is None:
            if not self.load_config():
                return False
            return self.connect_ssh()
        else:
            print("✓ Utilizando conexión SSH existente")
            return True

    def connect_ssh(self):
        try:
            vps_config = self.config['vps']
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.ssh_client.connect(
                hostname=vps_config['ip'],
                username=vps_config['user'],
                key_filename=vps_config['key_path'],
                passphrase=vps_config.get('passphrase')
            )
            print(f"[OK] Conectado a {vps_config['ip']}")
            return True
        except Exception as e:
            print(f"[ERROR] Error conectando SSH: {e}")
            return False

    def test_connection_option(self):
        print("\nPROBAR CONEXIÓN SSH")
        print("-" * 40)

        if self.ssh_client:
            self.close_connection()

        if not self.load_config():
            return

        print("Probando conexión SSH...")
        if self.establish_connection():
            print("✅ Conexión SSH exitosa")

            print("Probando ejecución de comandos...")
            result = self.execute_command("whoami")
            if result:
                print(f"✅ Usuario conectado: {result.strip()}")

                backup_config = self.config['backup']
                remote_folders = backup_config.get('remote_folders', [])

                print(f"\nVerificando acceso a directorios remotos:")
                for folder in remote_folders:
                    check_result = self.execute_command(f"ls -la {folder} 2>/dev/null | head -1")
                    if check_result:
                        print(f"✅ Accesible: {folder}")
                    else:
                        print(f"❌ No accesible: {folder}")

            else:
                print("❌ Error ejecutando comandos")
        else:
            print("❌ Error de conexión SSH")

    def mysql_backup_only_option(self):
        print("\nBACKUP SOLO DE MySQL")
        print("-" * 40)

        if not self.load_config():
            return

        mysql_config = self.config.get('mysql', {})
        if not mysql_config.get('enabled', False):
            print("[ERROR] MySQL backup no está habilitado en la configuración")
            return

        if not self.establish_connection():
            return

        backup_config = self.config['backup']
        local_save_path = self.ensure_local_directory(backup_config['local_save_path'])
        if not local_save_path:
            return

        mysql_backup_path = self.process_mysql_backup(local_save_path, mysql_config)
        if mysql_backup_path:
            backup_info = self.get_backup_info(mysql_backup_path)
            print(f"\n[✓] Backup MySQL completado: {backup_info['size_formatted']}")
        else:
            print("[ERROR] Error en backup de MySQL")

    def directories_backup_only_option(self):
        print("\nBACKUP SOLO DE DIRECTORIOS")
        print("-" * 40)

        if not self.load_config():
            return

        if not self.establish_connection():
            return

        backup_config = self.config['backup']
        settings = self.config.get('settings', {})
        local_save_path = self.ensure_local_directory(backup_config['local_save_path'])
        if not local_save_path:
            return

        backup_files = []

        for folder in backup_config['remote_folders']:
            print(f"\n--- Procesando: {folder} ---")

            try:
                remote_backup_path = self.compress_directory(folder)
                if not remote_backup_path:
                    print(f"[ERROR] No se pudo comprimir {folder}")
                    continue

                file_size = self.get_file_size(remote_backup_path)
                print(f"[INFO] Tamaño del backup: {self.format_file_size(file_size)}")

                backup_filename = os.path.basename(remote_backup_path)
                local_backup_path = os.path.join(local_save_path, backup_filename)

                print(f"[INFO] Descargando a: {local_backup_path}")
                if self.download_file(remote_backup_path, local_backup_path):
                    backup_info = self.get_backup_info(local_backup_path)
                    if backup_info:
                        print(f"[OK] Backup completado: {backup_info['size_formatted']}")

                    backup_files.append(local_backup_path)

                    if not settings.get('keep_remote_copies', False):
                        self.execute_command(f"rm -f {remote_backup_path}")
                        print(f"[INFO] Archivo remoto limpiado: {remote_backup_path}")
                else:
                    print(f"[ERROR] Error descargando {folder}")

            except Exception as e:
                print(f"[ERROR] Error procesando {folder}: {e}")

        if backup_files:
            print(f"\n[✓] {len(backup_files)} directorios respaldados exitosamente")
        else:
            print("\n[WARNING] No se completaron backups de directorios")

    def clean_old_backups_option(self):
        print("\nLIMPIAR BACKUPS ANTIGUOS")
        print("-" * 40)

        if not self.load_config():
            return

        backup_config = self.config['backup']
        local_save_path = backup_config['local_save_path']

        if not os.path.exists(local_save_path):
            print(f"[ERROR] Directorio no existe: {local_save_path}")
            return

        print(f"Directorio de backups: {local_save_path}")

        try:
            days_input = input("¿Eliminar backups de más de cuántos días? (por defecto 7): ").strip()
            max_age_days = int(days_input) if days_input else 7
        except ValueError:
            max_age_days = 7

        print(f"Eliminando backups de más de {max_age_days} días...")

        deleted_files = self.clean_old_backups(local_save_path, max_age_days)

        if deleted_files:
            print(f"\n[✓] Eliminados {len(deleted_files)} backups antiguos:")
            for filename in deleted_files:
                print(f"   • {filename}")
        else:
            print("\n[INFO] No hay backups antiguos para eliminar")

    def run_complete_backup_option(self):
        print("\nEJECUTAR BACKUP COMPLETO")
        print("-" * 40)

        success = self.run_backup()

        if success:
            print("\n[✓] Backup completo ejecutado exitosamente")
        else:
            print("\n[ERROR] Error en backup completo")

    def execute_command(self, command):
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            if error:
                print(f"[ERROR SSH] {error}")
            return output
        except Exception as e:
            print(f"[ERROR] Error ejecutando comando: {e}")
            return ""

    def download_file(self, remote_path, local_path):
        try:
            sftp = self.ssh_client.open_sftp()

            file_attrs = sftp.stat(remote_path)
            total_size = file_attrs.st_size

            def progress_callback(transferred, total):
                percent = (transferred / total) * 100
                print(
                    f"\r[INFO] Progreso: {percent:.1f}% ({self.format_file_size(transferred)}/{self.format_file_size(total)})",
                    end="")

            sftp.get(remote_path, local_path, callback=progress_callback)
            print()
            sftp.close()
            return True
        except Exception as e:
            print(f"[ERROR] Error descargando {remote_path}: {e}")
            return False

    def compress_directory(self, directory_path):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = os.path.basename(directory_path.rstrip('/'))
            backup_filename = f"{folder_name}_{timestamp}.tar.gz"
            remote_backup_path = f"/tmp/{backup_filename}"

            print(f"[INFO] Comprimiendo: {directory_path}")

            compress_cmd = f"tar -czf {remote_backup_path} -C {os.path.dirname(directory_path)} {os.path.basename(directory_path)}"
            result = self.execute_command(compress_cmd)

            check_cmd = f"ls -la {remote_backup_path}"
            check_result = self.execute_command(check_cmd)

            if backup_filename in check_result:
                print(f"[OK] Directorio comprimido: {remote_backup_path}")
                return remote_backup_path
            else:
                print(f"[ERROR] No se pudo comprimir {directory_path}")
                return None

        except Exception as e:
            print(f"[ERROR] Error comprimiendo directorio: {e}")
            return None

    def get_file_size(self, file_path):
        try:
            result = self.execute_command(f"stat -c%s {file_path}")
            return int(result.strip()) if result.strip().isdigit() else 0
        except:
            return 0

    def stop_mysql_service(self):
        print(f"[INFO] Deteniendo servicio {self.mysql_service_name}...")
        self.execute_command(f"sudo systemctl stop {self.mysql_service_name}")

        status_result = self.execute_command(f"sudo systemctl is-active {self.mysql_service_name}")
        if "inactive" in status_result.lower() or "failed" in status_result.lower():
            print(f"[OK] Servicio {self.mysql_service_name} detenido correctamente")
            return True
        else:
            print(f"[ERROR] No se pudo detener el servicio {self.mysql_service_name}")
            return False

    def start_mysql_service(self):
        print(f"[INFO] Iniciando servicio {self.mysql_service_name}...")
        self.execute_command(f"sudo systemctl start {self.mysql_service_name}")

        status_result = self.execute_command(f"sudo systemctl is-active {self.mysql_service_name}")
        if "active" in status_result.lower():
            print(f"[OK] Servicio {self.mysql_service_name} iniciado correctamente")
            return True
        else:
            print(f"[ERROR] No se pudo iniciar el servicio {self.mysql_service_name}")
            return False

    def create_mysql_cold_backup(self, backup_name=None):
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"mysql_backup_{timestamp}"

        backup_path = f"/tmp/{backup_name}.tar.gz"

        print(f"[INFO] Creando backup en frío de MySQL...")
        print(f"[INFO] Ruta de datos MySQL: {self.mysql_data_path}")
        print(f"[INFO] Archivo de backup: {backup_path}")

        compress_cmd = f"sudo tar -czf {backup_path} -C {os.path.dirname(self.mysql_data_path)} {os.path.basename(self.mysql_data_path)}"
        self.execute_command(compress_cmd)

        check_cmd = f"ls -la {backup_path}"
        check_result = self.execute_command(check_cmd)

        if backup_path in check_result:
            print(f"[OK] Backup creado exitosamente: {backup_path}")
            return backup_path
        else:
            print(f"[ERROR] No se pudo crear el backup")
            return None

    def process_mysql_backup(self, local_save_path, mysql_config):
        print(f"\n--- Procesando backup MySQL ---")

        try:
            backup_name = mysql_config.get('backup_name')
            restart_after_backup = mysql_config.get('restart_after_backup', True)

            if not self.stop_mysql_service():
                raise Exception("No se pudo detener el servicio MySQL")

            try:
                remote_backup_path = self.create_mysql_cold_backup(backup_name)
                if not remote_backup_path:
                    raise Exception("No se pudo completar el backup en frío de MySQL")

                file_size = self.get_file_size(remote_backup_path)
                print(f"[INFO] Tamaño del backup MySQL: {self.format_file_size(file_size)}")

                backup_filename = os.path.basename(remote_backup_path)
                local_backup_path = os.path.join(local_save_path, backup_filename)

                print(f"[INFO] Descargando MySQL backup a: {local_backup_path}")
                if not self.download_file(remote_backup_path, local_backup_path):
                    raise Exception("Error descargando backup MySQL")

                backup_info = self.get_backup_info(local_backup_path)
                if backup_info:
                    print(f"[OK] Backup MySQL completado: {backup_info['size_formatted']}")

                self.execute_command(f"sudo rm -f {remote_backup_path}")
                print(f"[INFO] Archivo remoto limpiado: {remote_backup_path}")

                return local_backup_path

            finally:
                if restart_after_backup:
                    if not self.start_mysql_service():
                        print("[WARNING] No se pudo reiniciar MySQL automáticamente")
                        print("[WARNING] Deberás reiniciar MySQL manualmente: sudo systemctl start mysql")

        except Exception as e:
            print(f"[ERROR] Error en backup MySQL: {e}")
            return None

    def ensure_local_directory(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except Exception as e:
            print(f"[ERROR] No se pudo crear directorio {path}: {e}")
            return None

    def format_file_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def get_backup_info(self, file_path):
        try:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                return {
                    'size': size,
                    'size_formatted': self.format_file_size(size),
                    'path': file_path
                }
        except:
            pass
        return None

    def create_final_backup_zip(self, local_save_path, backup_files):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_zip_name = f"backup_completo_{timestamp}.zip"
        final_zip_path = os.path.join(local_save_path, final_zip_name)

        print(f"\n--- Creando archivo ZIP final ---")
        print(f"[INFO] Creando: {final_zip_name}")

        try:
            with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for backup_file in backup_files:
                    if os.path.exists(backup_file):
                        arcname = os.path.basename(backup_file)
                        zipf.write(backup_file, arcname)
                        print(f"[INFO] Añadido al ZIP: {arcname}")

            backup_info = self.get_backup_info(final_zip_path)
            if backup_info:
                print(f"[OK] ZIP final creado: {backup_info['size_formatted']}")

            for backup_file in backup_files:
                try:
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                        print(f"[INFO] Eliminado archivo individual: {os.path.basename(backup_file)}")
                except OSError as e:
                    print(f"[WARNING] No se pudo eliminar {backup_file}: {e}")

            return final_zip_path

        except Exception as e:
            print(f"[ERROR] Error creando ZIP final: {e}")
            return None

    def clean_old_backups(self, directory, max_age_days=7):
        deleted_files = []
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)

            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        deleted_files.append(filename)
                        print(f"[INFO] Eliminado backup antiguo: {filename}")
        except Exception as e:
            print(f"[ERROR] Error limpiando backups antiguos: {e}")

        return deleted_files

    def close_connection(self):
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def handle_user_choice(self, choice):
        if choice == '1':
            self.run_complete_backup_option()
        elif choice == '2':
            self.validate_config_option()
        elif choice == '3':
            self.test_connection_option()
        elif choice == '4':
            self.mysql_backup_only_option()
        elif choice == '5':
            self.directories_backup_only_option()
        elif choice == '6':
            self.clean_old_backups_option()
        elif choice == '7':
            self.show_config_info_option()
        elif choice == '0':
            print("\n↩ Regresando al menú principal...")
            self.running = False
        else:
            print("Opción inválida. Por favor, selecciona una opción válida.")

    def run(self):
        print("Módulo de Gestión de Backups iniciado")

        try:
            while self.running:
                self.display_menu()
                choice = input("Selecciona una opción: ").strip()
                self.handle_user_choice(choice)

                if choice != '0' and self.running:
                    input("\nPresiona Enter para continuar...")

        except KeyboardInterrupt:
            print("\n\nMódulo de backups interrumpido")
        except Exception as e:
            print(f"Error en el módulo de backups: {e}")
        finally:
            self.close_connection()
            print("Módulo de gestión de backups finalizado")

    def run_backup(self):
        print("=== BACKUP MAKER ===")
        start_time = datetime.now()

        backup_success = False
        local_save_path = None

        try:
            if not self.load_config():
                return False

            vps_config = self.config['vps']
            backup_config = self.config['backup']
            settings = self.config.get('settings', {})
            mysql_config = self.config.get('mysql', {})

            local_save_path = self.ensure_local_directory(backup_config['local_save_path'])
            if not local_save_path:
                return False

            if not self.connect_ssh():
                return False

            backup_files = []

            try:
                if mysql_config.get('enabled', False):
                    mysql_backup_path = self.process_mysql_backup(local_save_path, mysql_config)
                    if mysql_backup_path:
                        backup_files.append(mysql_backup_path)

                for folder in backup_config['remote_folders']:
                    print(f"\n--- Procesando: {folder} ---")

                    try:
                        remote_backup_path = self.compress_directory(folder)
                        if not remote_backup_path:
                            print(f"[ERROR] No se pudo comprimir {folder}")
                            continue

                        file_size = self.get_file_size(remote_backup_path)
                        print(f"[INFO] Tamaño del backup: {self.format_file_size(file_size)}")

                        backup_filename = os.path.basename(remote_backup_path)
                        local_backup_path = os.path.join(local_save_path, backup_filename)

                        print(f"[INFO] Descargando a: {local_backup_path}")
                        if self.download_file(remote_backup_path, local_backup_path):
                            backup_info = self.get_backup_info(local_backup_path)
                            if backup_info:
                                print(f"[OK] Backup completado: {backup_info['size_formatted']}")

                            backup_files.append(local_backup_path)

                            if not settings.get('keep_remote_copies', False):
                                self.execute_command(f"rm -f {remote_backup_path}")
                                print(f"[INFO] Archivo remoto limpiado: {remote_backup_path}")
                        else:
                            print(f"[ERROR] Error descargando {folder}")

                    except Exception as e:
                        print(f"[ERROR] Error procesando {folder}: {e}")

                if backup_files:
                    final_zip_path = self.create_final_backup_zip(local_save_path, backup_files)
                    if final_zip_path:
                        print(f"\n[OK] Todos los backups guardados en: {os.path.basename(final_zip_path)}")
                else:
                    print(f"\n[WARNING] No se descargaron backups para comprimir")

                print(f"\n--- Limpiando backups antiguos ---")
                deleted_files = self.clean_old_backups(local_save_path, max_age_days=7)
                if deleted_files:
                    print(f"[INFO] Eliminados {len(deleted_files)} backups antiguos")

                backup_success = True

            finally:
                self.close_connection()

        except Exception as e:
            print(f"[ERROR] Error general: {e}")
            backup_success = False

        finally:
            end_time = datetime.now()
            duration = end_time - start_time
            print(f"\n=== RESUMEN ===")
            print(f"Duración total: {duration}")
            if local_save_path:
                print(f"Backups guardados en: {local_save_path}")
            print(f"Estado: {'COMPLETADO' if backup_success else 'ERROR'}")

        return backup_success


def main():
    backup_cli = BackupCLI()
    backup_cli.run()


if __name__ == "__main__":
    main()