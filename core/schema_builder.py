import json
import os
from typing import Dict, List, Any

class SchemaBuilder:
    def __init__(self, schema_file: str = "database_schema.json"):
        self.schema_file = schema_file
        self.schema_data = None

    def load_schema(self) -> Dict[str, Any]:
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as file:
                self.schema_data = json.load(file)
                return self.schema_data
        except FileNotFoundError:
            raise Exception(f"Archivo de esquema no encontrado: {self.schema_file}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error al parsear JSON: {e}")

    def validate_schema(self) -> bool:
        if not self.schema_data:
            return False

        required_keys = ["database_name", "tables"]
        for key in required_keys:
            if key not in self.schema_data:
                raise Exception(f"Clave requerida '{key}' no encontrada en el esquema")

        for table in self.schema_data.get("tables", []):
            if "name" not in table or "columns" not in table:
                raise Exception(f"Tabla malformada: {table}")

            for column in table["columns"]:
                if "name" not in column or "type" not in column:
                    raise Exception(f"Columna malformada en tabla {table['name']}: {column}")

        return True

    def generate_create_tables_sql(self) -> List[str]:
        sql_statements = []

        for table in self.schema_data["tables"]:
            table_name = table["name"]
            columns_sql = []

            for column in table["columns"]:
                column_name = column["name"]
                column_type = column["type"]
                constraints = column.get("constraints", [])

                column_definition = f"`{column_name}` {column_type}"
                if constraints:
                    column_definition += " " + " ".join(constraints)

                columns_sql.append(column_definition)

            create_table_sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(columns_sql)});"
            sql_statements.append(create_table_sql)

        return sql_statements

    def generate_create_indexes_sql(self) -> List[str]:
        sql_statements = []

        indexes = self.schema_data.get("indexes", [])
        for index in indexes:
            index_name = index["name"]
            table_name = index["table"]
            columns = index["columns"]

            columns_str = ", ".join([f"`{col}`" for col in columns])

            drop_index_sql = f"DROP INDEX `{index_name}` ON `{table_name}`;"
            create_index_sql = f"CREATE INDEX `{index_name}` ON `{table_name}` ({columns_str});"

            sql_statements.append({
                "sql": drop_index_sql,
                "optional": True,
                "description": f"Eliminando índice existente {index_name}"
            })
            sql_statements.append({
                "sql": create_index_sql,
                "optional": False,
                "description": f"Creando índice {index_name}"
            })

        return sql_statements

    def create_database_structure(self, connection):
        if not self.schema_data:
            self.load_schema()

        self.validate_schema()

        database_name = self.schema_data["database_name"]

        print(f"Creando base de datos: {database_name}")
        if not connection.create_database(database_name):
            raise Exception(f"Error creando la base de datos {database_name}")

        connection.use_database(database_name)

        tables_sql = self.generate_create_tables_sql()
        for i, sql in enumerate(tables_sql, 1):
            print(f"Creando tabla {i}/{len(tables_sql)}...")
            if not connection.execute_sql(sql, database_name):
                raise Exception(f"Error creando tabla: {sql}")

        indexes_sql = self.generate_create_indexes_sql()
        index_count = len([idx for idx in indexes_sql if not idx.get("optional", False)])
        current_index = 0

        for sql_obj in indexes_sql:
            if isinstance(sql_obj, dict):
                sql = sql_obj["sql"]
                optional = sql_obj.get("optional", False)
                description = sql_obj.get("description", "Ejecutando comando")

                if optional:
                    print(f"⚠ {description} (puede fallar sin problema)...")
                    connection.execute_sql(sql, database_name)
                else:
                    current_index += 1
                    print(f"Creando índice {current_index}/{index_count}...")
                    if not connection.execute_sql(sql, database_name):
                        raise Exception(f"Error creando índice: {sql}")
            else:
                current_index += 1
                print(f"Creando índice {current_index}/{index_count}...")
                if not connection.execute_sql(sql_obj, database_name):
                    raise Exception(f"Error creando índice: {sql_obj}")

        print(f"✓ Base de datos '{database_name}' creada exitosamente")
        return True