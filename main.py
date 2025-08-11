from core import DatabaseCLI, BackupCLI

class MainApplication:
    def __init__(self):
        self.running = True

    def display_main_menu(self):
        print("\n" + "="*50)
        print("    SISTEMA DE GESTIÓN - MENÚ PRINCIPAL")
        print("="*50)
        print("1. Manage Databases")
        print("2. Manage Backups")
        print("3. Exit")
        print("-"*50)

    def databases_option(self):
        print("\nIniciando módulo de gestión de bases de datos...")
        try:
            database_cli = DatabaseCLI()
            database_cli.run()
        except Exception as e:
            print(f"Error en el módulo de bases de datos: {e}")

        print("\nRegresando al menú principal...")

    def backup_option(self):
        print("\nIniciando módulo de backups...")
        try:
            backup_cli = BackupCLI()
            backup_cli.run()
        except Exception as e:
            print(f"Error en el módulo de backups: {e}")

        print("\nRegresando al menú principal...")

    def exit_option(self):
        print("\nCerrando aplicación...")
        print("¡Gracias por usar el sistema!")
        self.running = False

    def handle_user_choice(self, choice):
        if choice == '1':
            self.databases_option()
        elif choice == '2':
            self.backup_option()
        elif choice == '3':
            self.exit_option()
        else:
            print("Opción inválida. Por favor, selecciona 1, 2 o 3.")

    def run(self):
        print("Bienvenido al Sistema de Gestión")
        print("Versión 1.0")

        while self.running:
            try:
                self.display_main_menu()
                choice = input("Selecciona una opción: ").strip()
                self.handle_user_choice(choice)

            except KeyboardInterrupt:
                print("\n\nAplicación interrumpida por el usuario")
                self.running = False
            except Exception as e:
                print(f"Error inesperado: {e}")
                print("La aplicación continuará ejecutándose...")

        print("\nAplicación cerrada correctamente")

def main():
    app = MainApplication()
    app.run()

if __name__ == "__main__":
    main()