import paramiko
from dotenv import load_dotenv
import os
import time

class Connection:
    def __init__(self):
        self.current_database = None
        load_dotenv()
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.IP = os.getenv('VPS_IP')
        self.USERNAME = os.getenv('VPS_USERNAME')
        self.KEY = os.getenv('PRIVATE_KEY')
        self.PASSPHRASE = os.getenv('PASSPHRASE')

        self.MYSQL_USER = os.getenv('MYSQL_USER', 'root')
        self.MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
        self.MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')

        if not self.connect():
            print("Connection failed with parameters: ", self.IP, self.USERNAME, self.KEY, self.PASSPHRASE, sep="\n")
            exit()
        else:
            print("Connected to VPS")

    def connect(self):
        try:
            self.ssh.connect(hostname=self.IP, username=self.USERNAME, key_filename=self.KEY, passphrase=self.PASSPHRASE)
            return True
        except Exception as e:
            print(e)
            return False

    def execute_mysql_command(self, sql_command, database=None, ignore_errors=False):
        try:
            timestamp = int(time.time())
            temp_sql_file = f"/tmp/temp_sql_{timestamp}.sql"

            create_file_cmd = f"cat > {temp_sql_file} << 'EOF'\n{sql_command}\nEOF"

            print(f"Ejecutando SQL: {sql_command}")

            stdin, stdout, stderr = self.ssh.exec_command(create_file_cmd)
            create_exit_status = stdout.channel.recv_exit_status()

            if create_exit_status != 0:
                print(f"Error creando archivo temporal")
                return False

            if database:
                mysql_cmd = f"mysql -u {self.MYSQL_USER} -p'{self.MYSQL_PASSWORD}' -h {self.MYSQL_HOST} {database} < {temp_sql_file}"
            else:
                mysql_cmd = f"mysql -u {self.MYSQL_USER} -p'{self.MYSQL_PASSWORD}' -h {self.MYSQL_HOST} < {temp_sql_file}"

            stdin, stdout, stderr = self.ssh.exec_command(mysql_cmd)
            exit_status = stdout.channel.recv_exit_status()

            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()

            cleanup_cmd = f"rm -f {temp_sql_file}"
            self.ssh.exec_command(cleanup_cmd)

            if exit_status != 0:
                if ignore_errors:
                    print(f"⚠ Advertencia MySQL (ignorando error): {error}")
                    return True
                else:
                    print(f"Error MySQL (código {exit_status}): {error}")
                    return False
            else:
                if output:
                    print(f"Resultado: {output}")
                print("✓ Comando ejecutado exitosamente")
                return True

        except Exception as e:
            if ignore_errors:
                print(f"⚠ Advertencia: {e} (ignorando error)")
                return True
            else:
                print(f"Error ejecutando comando MySQL: {e}")
                return False

    def execute_mysql_simple(self, sql_command, ignore_errors=False):
        try:
            mysql_cmd = f"mysql -u {self.MYSQL_USER} -p'{self.MYSQL_PASSWORD}' -h {self.MYSQL_HOST} -e '{sql_command}'"

            print(f"Ejecutando SQL simple: {sql_command}")

            stdin, stdout, stderr = self.ssh.exec_command(mysql_cmd)
            exit_status = stdout.channel.recv_exit_status()

            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()

            if exit_status != 0:
                if ignore_errors:
                    print(f"⚠ Advertencia MySQL (ignorando error): {error}")
                    return True
                else:
                    print(f"Error MySQL (código {exit_status}): {error}")
                    return False
            else:
                if output:
                    print(f"Resultado: {output}")
                print("✓ Comando ejecutado exitosamente")
                return True

        except Exception as e:
            if ignore_errors:
                print(f"⚠ Advertencia: {e} (ignorando error)")
                return True
            else:
                print(f"Error ejecutando comando MySQL simple: {e}")
                return False

    def create_database(self, database_name):
        sql_simple = f"CREATE DATABASE IF NOT EXISTS {database_name}"

        print("Intentando crear base de datos sin backticks...")
        if self.execute_mysql_simple(sql_simple):
            return True

        sql_with_backticks = f"CREATE DATABASE IF NOT EXISTS `{database_name}`;"
        print("Intentando crear base de datos con backticks usando archivo temporal...")
        return self.execute_mysql_command(sql_with_backticks)

    def use_database(self, database_name):
        self.current_database = database_name
        return True

    def execute_sql(self, sql_command, database=None, ignore_errors=False):
        if database is None and hasattr(self, 'current_database'):
            database = self.current_database

        return self.execute_mysql_command(sql_command, database, ignore_errors)

    def test_mysql_connection(self):
        return self.execute_mysql_simple("SELECT 1")

    def show_databases(self):
        return self.execute_mysql_simple("SHOW DATABASES")

    def show_tables(self, database_name):
        sql = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{database_name}'"
        return self.execute_mysql_command(sql)

    def close(self):
        try:
            self.ssh.close()
            return True
        except Exception as e:
            print(e)
            return False

    def execute_query_with_results(self, sql_query, database=None, format_output='dict'):
        try:
            timestamp = int(time.time())
            temp_sql_file = f"/tmp/temp_query_{timestamp}.sql"

            create_file_cmd = f"cat > {temp_sql_file} << 'EOF'\n{sql_query}\nEOF"

            stdin, stdout, stderr = self.ssh.exec_command(create_file_cmd)
            create_exit_status = stdout.channel.recv_exit_status()

            if create_exit_status != 0:
                print(f"Error creando archivo temporal")
                return None

            if database:
                mysql_cmd = f"mysql -u {self.MYSQL_USER} -p'{self.MYSQL_PASSWORD}' -h {self.MYSQL_HOST} {database} --batch --raw -e \"{sql_query}\""
            else:
                mysql_cmd = f"mysql -u {self.MYSQL_USER} -p'{self.MYSQL_PASSWORD}' -h {self.MYSQL_HOST} --batch --raw -e \"{sql_query}\""

            stdin, stdout, stderr = self.ssh.exec_command(mysql_cmd)
            exit_status = stdout.channel.recv_exit_status()

            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()

            cleanup_cmd = f"rm -f {temp_sql_file}"
            self.ssh.exec_command(cleanup_cmd)

            if exit_status != 0:
                print(f"Error ejecutando consulta: {error}")
                return None

            if not output:
                return []

            lines = output.strip().split('\n')
            if len(lines) < 2:
                return []

            headers = [h.strip() for h in lines[0].split('\t')]

            results = []

            for i, line in enumerate(lines[1:], 1):
                if line.strip():
                    values = line.split('\t')

                    while len(values) < len(headers):
                        values.append(None)

                    row_dict = {}
                    for j, header in enumerate(headers):
                        value = values[j] if j < len(values) else None

                        if value == 'NULL' or value == '\\N' or value == '':
                            value = None

                        row_dict[header] = value

                    results.append(row_dict)

            print(f"✓ Consulta ejecutada: {len(results)} filas obtenidas")
            return results

        except Exception as e:
            print(f"Error ejecutando consulta con resultados: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_databases_list(self):
        query = "SELECT schema_name as database_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')"
        return self.execute_query_with_results(query)