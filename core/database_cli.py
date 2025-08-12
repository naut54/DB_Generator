import os
import json
import glob
from core import Connection
from core.schema_builder import SchemaBuilder

class DatabaseCLI:
    def __init__(self):
        self.connection = None
        self.running = True

    def display_menu(self):
        print("\n" + "="*50)
        print("    GESTIÓN DE BASES DE DATOS")
        print("="*50)
        print("1. Crear base de datos")
        print("2. Mostrar bases de datos existentes")
        print("3. Mostrar tablas de una base de datos")
        print("4. Probar conexión SSH/MySQL")
        print("5. Extraer esquema de base de datos existente")  # NUEVA OPCIÓN
        print("0. Volver al menú principal")
        print("-"*50)

    def get_json_files(self):
        json_files = []

        current_dir_files = glob.glob("*.json")
        json_files.extend(current_dir_files)

        if os.path.exists("dataModels"):
            datamodels_files = glob.glob("dataModels/*.json")
            json_files.extend(datamodels_files)

        return json_files

    def select_json_file(self):
        json_files = self.get_json_files()

        if not json_files:
            print("No se encontraron archivos JSON en el proyecto")
            print("Tip: Coloca archivos .json en el directorio actual o en dataModels/")
            return None

        print("\n" + "-"*40)
        print("   SELECCIONA UN ARCHIVO DE ESQUEMA")
        print("-"*40)

        for i, file in enumerate(json_files, 1):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    db_name = data.get('database_name', 'Sin nombre')
                    table_count = len(data.get('tables', []))
                    print(f"{i}. {file}")
                    print(f"   └── Base de datos: {db_name}")
                    print(f"   └── Tablas: {table_count}")
            except Exception as e:
                print(f"{i}. {file} (Error al leer: {e})")

        print("0. Cancelar")
        print("-"*40)

        while True:
            try:
                choice = int(input("Selecciona un archivo (número): "))
                if choice == 0:
                    return None
                elif 1 <= choice <= len(json_files):
                    selected_file = json_files[choice - 1]
                    print(f"✓ Archivo seleccionado: {selected_file}")
                    return selected_file
                else:
                    print("Opción inválida. Intenta de nuevo.")
            except ValueError:
                print("Por favor, introduce un número válido.")

    def establish_connection(self):
        if self.connection is None:
            try:
                print("Estableciendo conexión SSH...")
                self.connection = Connection()
                print("✓ Conexión SSH establecida")

                if not self.connection.test_mysql_connection():
                    print("Error: No se puede conectar a MySQL")
                    self.connection = None
                    return False

                print("✓ Conexión MySQL verificada")
                return True

            except Exception as e:
                print(f"Error de conexión: {e}")
                self.connection = None
                return False
        else:
            print("✓ Utilizando conexión existente")
            return True

    def create_database_option(self):
        print("\nCREAR BASE DE DATOS")

        if not self.establish_connection():
            return

        schema_file = self.select_json_file()
        if schema_file is None:
            print("Operación cancelada")
            return

        try:
            print("\nMostrando bases de datos existentes...")
            self.connection.show_databases()

            schema_builder = SchemaBuilder(schema_file)

            print(f"\nCreando estructura desde: {schema_file}")
            if schema_builder.create_database_structure(self.connection):
                print("Estructura de base de datos creada exitosamente")

                print("\nVerificando que la base de datos se creó...")
                self.connection.show_databases()

                db_name = schema_builder.schema_data['database_name']
                print(f"\nMostrando tablas en la base de datos '{db_name}'...")
                self.connection.show_tables(db_name)

            else:
                print("Error creando la estructura de la base de datos")

        except Exception as e:
            print(f"Error: {e}")

    def show_databases_option(self):
        print("\nMOSTRAR BASES DE DATOS EXISTENTES")

        if not self.establish_connection():
            return

        try:
            self.connection.show_databases()
        except Exception as e:
            print(f"Error: {e}")

    def show_tables_option(self):
        print("\nMOSTRAR TABLAS DE UNA BASE DE DATOS")

        if not self.establish_connection():
            return

        try:
            print("\nBases de datos disponibles:")
            self.connection.show_databases()

            db_name = input("\nIntroduce el nombre de la base de datos: ").strip()
            if db_name:
                print(f"\nTablas en la base de datos '{db_name}':")
                self.connection.show_tables(db_name)
            else:
                print("Nombre de base de datos no válido")

        except Exception as e:
            print(f"Error: {e}")

    def test_connection_option(self):
        print("\nPROBANDO CONEXIÓN SSH/MySQL")

        if self.connection:
            self.connection.close()
            self.connection = None

        self.establish_connection()

    def extract_schema_option(self):
        print("\nEXTRAER ESQUEMA DE BASE DE DATOS")

        if not self.establish_connection():
            return

        try:
            print("\nBases de datos disponibles:")
            databases = self.connection.get_databases_list()

            if not databases:
                print("No se encontraron bases de datos disponibles")
                return

            print("\n" + "-"*40)
            print("   SELECCIONA UNA BASE DE DATOS")
            print("-"*40)

            for i, db in enumerate(databases, 1):
                print(f"{i}. {db['database_name']}")

            print("0. Cancelar")
            print("-"*40)

            while True:
                try:
                    choice = int(input("Selecciona una base de datos (número): "))
                    if choice == 0:
                        print("Operación cancelada")
                        return
                    elif 1 <= choice <= len(databases):
                        selected_db = databases[choice - 1]['database_name']
                        break
                    else:
                        print("Opción inválida. Intenta de nuevo.")
                except ValueError:
                    print("Por favor, introduce un número válido.")

            print(f"\nBase de datos seleccionada: {selected_db}")

            # Preguntar por nombre de archivo personalizado (opcional)
            custom_name = input("\nNombre personalizado para el archivo (Enter para auto): ").strip()
            output_file = None
            if custom_name:
                if not custom_name.endswith('.json'):
                    custom_name += '.json'
                output_file = f"dataModels/{custom_name}"

            schema_builder = SchemaBuilder()

            print(f"\nExtrayendo esquema de '{selected_db}'...")
            if schema_builder.extract_database_schema(self.connection, selected_db, output_file):
                print("\n✓ Extracción de esquema completada exitosamente")
            else:
                print("\n✗ Error en la extracción del esquema")

        except Exception as e:
            print(f"Error: {e}")

    def close_connection(self):
        if self.connection:
            try:
                if self.connection.close():
                    print("Conexión de base de datos cerrada correctamente")
                else:
                    print("Error al cerrar la conexión de base de datos")
            except Exception as e:
                print(f"Error cerrando conexión: {e}")
            finally:
                self.connection = None

    def handle_user_choice(self, choice):
        if choice == '1':
            self.create_database_option()
        elif choice == '2':
            self.show_databases_option()
        elif choice == '3':
            self.show_tables_option()
        elif choice == '4':
            self.test_connection_option()
        elif choice == '5':  # NUEVA OPCIÓN
            self.extract_schema_option()
        elif choice == '0':
            print("\n↩Regresando al menú principal...")
            self.running = False
        else:
            print("Opción inválida. Por favor, selecciona una opción válida.")

    def run(self):
        print("Módulo de Gestión de Bases de Datos iniciado")

        try:
            while self.running:
                self.display_menu()
                choice = input("Selecciona una opción: ").strip()
                self.handle_user_choice(choice)

                if choice != '0' and self.running:
                    input("\nPresiona Enter para continuar...")

        except KeyboardInterrupt:
            print("\n\nMódulo de bases de datos interrumpido")
        except Exception as e:
            print(f"Error en el módulo de bases de datos: {e}")
        finally:
            self.close_connection()
            print("Módulo de gestión de bases de datos finalizado")