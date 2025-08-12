import yaml
import subprocess
import sys
import signal
import time
import os
from threading import Thread

class DevelopmentCLI:
    def __init__(self, config_path='config.yaml'):
        self.connection = None
        self.running = True
        self.config_path = config_path
        self.config = None
        self.tunnel_process = None

        if not self.load_config():
            print("[ERROR] No se pudo cargar la configuración. El programa no funcionará correctamente.")
            self.running = False

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        print("\n[INFO] Cerrando conexiones...")
        self._cleanup_tunnel()
        sys.exit(0)

    def display_menu(self):
        print("\n" + "="*50)
        print("    GESTIÓN DE DESARROLLO")
        print("="*50)
        print("1. Crear Túnel SSH")
        print("2. Cerrar Túnel SSH")
        print("3. Ver Estado del Túnel")
        print("4. Salir")
        print("="*50)

    def load_config(self):
        try:
            if not os.path.exists(self.config_path):
                print(f"[ERROR] No se encontró el archivo {self.config_path}")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)

            if not self.config or 'ssh_tunnel' not in self.config:
                print("[ERROR] Configuración ssh_tunnel no encontrada en config.yaml")
                return False

            required_keys = ['remote_host', 'remote_port', 'username', 'host']
            ssh_config = self.config['ssh_tunnel']

            for key in required_keys:
                if key not in ssh_config:
                    print(f"[ERROR] Clave requerida '{key}' no encontrada en ssh_tunnel")
                    return False

            return True

        except FileNotFoundError:
            print(f"[ERROR] No se encontró {self.config_path}")
            return False
        except yaml.YAMLError as e:
            print(f"[ERROR] Error al parsear {self.config_path}: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Error inesperado al cargar configuración: {e}")
            return False

    def _validate_port(self, port_str):
        if not port_str:
            return 3307

        try:
            port = int(port_str)
            if 1024 <= port <= 65535:
                return port
            else:
                print("[ERROR] El puerto debe estar entre 1024 y 65535")
                return None
        except ValueError:
            print("[ERROR] El puerto debe ser un número válido")
            return None

    def assemble_ssh_tunnel_command(self, port=None):
        local_port = port or 3307
        ssh_config = self.config['ssh_tunnel']

        command = [
            'ssh',
            '-L', f"{local_port}:{ssh_config['remote_host']}:{ssh_config['remote_port']}",
            f"{ssh_config['username']}@{ssh_config['host']}"
        ]

        if 'key_path' in ssh_config:
            command.extend(['-i', ssh_config['key_path']])

        if 'port' in ssh_config:
            command.extend(['-p', str(ssh_config['port'])])

        print(f"[INFO] Comando: {' '.join(command)}")

        return command

    def create_ssh_tunnel_option(self):
        if self.tunnel_process and self.tunnel_process.poll() is None:
            print("[INFO] Ya existe un túnel SSH activo")
            return

        print("-" * 40)
        port_input = input("Ingresa el puerto local (vacío para usar 3307): ").strip()
        print("-" * 40)

        port = self._validate_port(port_input)
        if port is None:
            return

        try:
            command = self.assemble_ssh_tunnel_command(port)
            print(f"[INFO] Creando túnel SSH en puerto {port}...")
            print(f"[INFO] Manteniendo túnel activo... (Ctrl+C para salir del programa cerrará el túnel)")

            if os.name == 'nt':
                self.tunnel_process = subprocess.Popen(
                    ' '.join(command),
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.tunnel_process = subprocess.Popen(command)

            time.sleep(3)

            if self.tunnel_process.poll() is None:
                print(f"[✓] Túnel SSH creado exitosamente en puerto {port}")
                print(f"[INFO] Puedes conectarte a localhost:{port}")
                print(f"[INFO] El túnel permanecerá activo mientras el programa esté ejecutándose")
            else:
                print(f"[ERROR] Error al crear el túnel SSH")
                print(f"[ERROR] El proceso SSH terminó inmediatamente")
                return_code = self.tunnel_process.returncode
                print(f"[ERROR] Código de salida: {return_code}")
                self.tunnel_process = None

        except FileNotFoundError:
            print("[ERROR] SSH no está disponible en el sistema")
            print("[ERROR] Asegúrate de tener OpenSSH instalado o usar Git Bash")
        except Exception as e:
            print(f"[ERROR] Error inesperado al crear túnel: {e}")

    def close_ssh_tunnel_option(self):
        if not self.tunnel_process or self.tunnel_process.poll() is not None:
            print("[INFO] No hay túnel SSH activo")
            return

        self._cleanup_tunnel()
        print("[✓] Túnel SSH cerrado exitosamente")

    def show_tunnel_status(self):
        if not self.tunnel_process:
            print("[INFO] No hay túnel SSH configurado")
        elif self.tunnel_process.poll() is None:
            print("[✓] Túnel SSH activo")
            print(f"[INFO] PID: {self.tunnel_process.pid}")
        else:
            print("[INFO] Túnel SSH no está activo")

    def _cleanup_tunnel(self):
        if self.tunnel_process and self.tunnel_process.poll() is None:
            try:
                self.tunnel_process.terminate()
                try:
                    self.tunnel_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.tunnel_process.kill()
                    self.tunnel_process.wait()
            except Exception as e:
                print(f"[WARNING] Error al cerrar túnel: {e}")
            finally:
                self.tunnel_process = None

    def handle_user_choice(self, choice):
        """Maneja la elección del usuario"""
        choice_map = {
            '1': self.create_ssh_tunnel_option,
            '2': self.close_ssh_tunnel_option,
            '3': self.show_tunnel_status,
            '4': self._exit_program
        }

        action = choice_map.get(choice)
        if action:
            action()
        elif choice != '4':
            print("[WARNING] Opción no válida")

    def _exit_program(self):
        print("[INFO] Cerrando módulo de desarrollo...")
        self._cleanup_tunnel()
        self.running = False

    def run(self):
        print("Módulo de Desarrollo Iniciado")

        if not self.running:
            print("[ERROR] No se puede iniciar debido a errores de configuración")
            return

        try:
            while self.running:
                self.display_menu()
                choice = input("Selecciona una opción: ").strip()

                if choice == '4':
                    self._exit_program()
                    break

                self.handle_user_choice(choice)

                if self.running:
                    input("\nPresiona Enter para continuar...")

        except KeyboardInterrupt:
            print("\n\n[INFO] Módulo de Desarrollo interrumpido por el usuario")
        except Exception as e:
            print(f"[ERROR] Error en el módulo de Desarrollo: {e}")
        finally:
            self._cleanup_tunnel()
            self.running = False
            print("Módulo de Desarrollo finalizado")