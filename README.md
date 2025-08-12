# Sistema de Gestión de Bases de Datos y Backups

Sistema completo para gestionar bases de datos MySQL remotas y realizar backups automatizados a través de conexiones SSH.

## Características

- **Gestión de Bases de Datos**: Crear, listar y gestionar bases de datos MySQL remotas
- **Constructor de Esquemas**: Crear estructuras de BD desde archivos JSON
- **Extractor de Esquemas**: Exportar esquemas de bases de datos existentes
- **Sistema de Backups**: Backups automatizados de MySQL y directorios
- **Conexión SSH Segura**: Gestión remota mediante claves SSH
- **Interfaz CLI**: Menús interactivos fáciles de usar

## Instalación

### Prerrequisitos

- Python 3.8 o superior
- Acceso SSH al servidor remoto
- MySQL instalado en el servidor remoto
- Clave SSH configurada para el acceso

### Dependencias

Instala las dependencias necesarias:

```bash
pip install paramiko python-dotenv pyyaml
```

### Estructura del Proyecto

```
DB_Generator/
├── core/
│   ├── __init__.py
│   ├── connection.py
│   ├── database_cli.py
│   ├── schema_builder.py
│   └── backup_cli.py
├── dataModels/
│   └── database_schema.json
├── saved_backups/
├── main.py
├── .env                    # ⚠ DEBE llamarse exactamente así
├── config.yaml            # ⚠ DEBE llamarse exactamente así
└── README.md
```

## ⚙️ Configuración

### 1. Archivo de Entorno (.env)

**⚠ IMPORTANTE**: El archivo DEBE llamarse exactamente `.env` (con el punto al inicio).

Crea el archivo `.env` en el directorio raíz con la siguiente estructura:

```env
# Configuración del VPS
VPS_IP=192.168.1.100
VPS_USERNAME=tu_usuario
PRIVATE_KEY=/ruta/a/tu/clave_privada_ssh
PASSPHRASE=tu_passphrase_si_tiene

# Configuración de MySQL
MYSQL_USER=root
MYSQL_PASSWORD=tu_password_mysql
MYSQL_HOST=localhost
```

### 2. Archivo de Configuración de Backups (config.yaml)

**⚠ IMPORTANTE**: El archivo DEBE llamarse exactamente `config.yaml`.

Crea el archivo `config.yaml` en el directorio raíz:

```yaml
# Configuración del servidor VPS
vps:
  ip: "192.168.1.100"                    # IP de tu servidor
  user: "tu_usuario"                     # Usuario SSH
  key_path: "/ruta/a/tu/clave_ssh"      # Ruta a tu clave privada SSH
  passphrase: "tu_passphrase"           # Passphrase de la clave SSH (opcional)

# Configuración de backups
backup:
  local_save_path: "./saved_backups"    # Directorio local donde guardar backups
  remote_folders:                       # Directorios remotos a respaldar
    - "/var/www/html"
    - "/home/usuario/documentos"
    - "/etc/nginx"

# Configuración de MySQL
mysql:
  enabled: true                         # Habilitar backup de MySQL
  backup_name: "mysql_backup"          # Nombre base para backups MySQL
  restart_after_backup: true           # Reiniciar MySQL tras el backup

# Configuraciones adicionales
settings:
  keep_remote_copies: false            # Mantener copias en el servidor remoto
```

### 3. Configuración de Claves SSH

Asegúrate de tener configurado el acceso SSH:

```bash
# Generar clave SSH (si no tienes una)
ssh-keygen -t rsa -b 4096 -C "tu_email@ejemplo.com"

# Copiar la clave pública al servidor
ssh-copy-id -i ~/.ssh/id_rsa.pub usuario@tu_servidor

# Probar la conexión
ssh usuario@tu_servidor
```

## Esquemas de Base de Datos

### Formato JSON para Esquemas

Los archivos de esquema deben estar en formato JSON. Ejemplo (`dataModels/mi_esquema.json`):

```json
{
  "database_name": "mi_aplicacion",
  "tables": [
    {
      "name": "usuarios",
      "columns": [
        {
          "name": "id",
          "type": "INTEGER",
          "constraints": ["PRIMARY KEY", "AUTO_INCREMENT"]
        },
        {
          "name": "nombre",
          "type": "VARCHAR(100)",
          "constraints": ["NOT NULL"]
        },
        {
          "name": "email",
          "type": "VARCHAR(255)",
          "constraints": ["UNIQUE", "NOT NULL"]
        },
        {
          "name": "fecha_creacion",
          "type": "TIMESTAMP",
          "constraints": ["DEFAULT CURRENT_TIMESTAMP"]
        }
      ]
    },
    {
      "name": "productos",
      "columns": [
        {
          "name": "id",
          "type": "INTEGER",
          "constraints": ["PRIMARY KEY", "AUTO_INCREMENT"]
        },
        {
          "name": "nombre",
          "type": "VARCHAR(200)",
          "constraints": ["NOT NULL"]
        },
        {
          "name": "precio",
          "type": "DECIMAL(10,2)",
          "constraints": ["NOT NULL"]
        }
      ]
    }
  ],
  "indexes": [
    {
      "name": "idx_usuarios_email",
      "table": "usuarios",
      "columns": ["email"]
    }
  ]
}
```

## Uso de la Aplicación

### Ejecutar la Aplicación

```bash
python main.py
```

### Menú Principal

```
==================================================
    SISTEMA DE GESTIÓN - MENÚ PRINCIPAL
==================================================
1. Manage Databases
2. Manage Backups
3. Exit
--------------------------------------------------
```

## Gestión de Bases de Datos

### Opciones Disponibles

1. **Crear base de datos**: Crear estructura desde archivo JSON
2. **Mostrar bases de datos**: Listar todas las bases de datos
3. **Mostrar tablas**: Ver tablas de una base de datos específica
4. **Probar conexión**: Verificar conectividad SSH/MySQL
5. **Extraer esquema**: Exportar esquema de BD existente a JSON

### Flujo de Trabajo Típico

1. Crear un archivo JSON con el esquema deseado en `dataModels/`
2. Seleccionar "Crear base de datos" en el menú
3. Elegir el archivo JSON del esquema
4. La aplicación creará automáticamente:
   - La base de datos
   - Todas las tablas con sus columnas
   - Los índices definidos

## Sistema de Backups

### Tipos de Backup

- **Backup completo**: MySQL + directorios especificados
- **Solo MySQL**: Backup en frío de la base de datos
- **Solo directorios**: Backup de carpetas específicas
- **Limpieza automática**: Elimina backups antiguos

### Proceso de Backup MySQL

1. Detiene el servicio MySQL
2. Crea backup en frío del directorio `/var/lib/mysql`
3. Comprime el backup
4. Descarga a local
5. Reinicia MySQL automáticamente

### Configuración de Directorios

Edita `config.yaml` para especificar qué directorios respaldar:

```yaml
backup:
  remote_folders:
    - "/var/www/html"      # Sitios web
    - "/etc/nginx"         # Configuración Nginx
    - "/home/usuario/docs" # Documentos de usuario
```

## Ejemplos de Uso

### Crear una Base de Datos

1. Crea `dataModels/tienda.json`:
```json
{
  "database_name": "tienda_online",
  "tables": [
    {
      "name": "clientes",
      "columns": [
        {"name": "id", "type": "INTEGER", "constraints": ["PRIMARY KEY", "AUTO_INCREMENT"]},
        {"name": "nombre", "type": "VARCHAR(100)", "constraints": ["NOT NULL"]},
        {"name": "email", "type": "VARCHAR(255)", "constraints": ["UNIQUE"]}
      ]
    }
  ]
}
```

2. Ejecuta la aplicación y selecciona:
   - Opción 1: Manage Databases
   - Opción 1: Crear base de datos
   - Selecciona tu archivo `tienda.json`

### Realizar Backup Completo

1. Configura `config.yaml` con tus directorios
2. Ejecuta la aplicación y selecciona:
   - Opción 2: Manage Backups
   - Opción 1: Ejecutar backup completo

## ⚠ Consideraciones de Seguridad

- **Nunca** subas los archivos `.env` o `config.yaml` al control de versiones
- Usa permisos restrictivos en las claves SSH (600)
- Considera usar un usuario específico para backups con permisos limitados
- Realiza pruebas de restauración periódicamente

## Solución de Problemas

### Error de Conexión SSH

```bash
# Verificar conectividad
ssh -i /ruta/a/clave usuario@servidor

# Verificar permisos de clave
chmod 600 /ruta/a/clave_privada
```

### Error de MySQL

```bash
# En el servidor remoto, verificar estado
sudo systemctl status mysql

# Verificar acceso
mysql -u root -p
```

### Error de Archivos de Configuración

- Verifica que `.env` y `config.yaml` existan y tengan los nombres exactos
- Revisa la sintaxis YAML con un validador online
- Asegúrate de que las rutas en los archivos sean correctas

## Estructura de Archivos de Configuración

### Nombres Correctos
- `.env` (con punto al inicio)
- `config.yaml` (exactamente así)

### Nombres Incorrectos
- `env`, `environment.env`, `.env.txt`
- `config.yml`, `backup_config.yaml`, `config.txt`

## Contribución

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.

---

**Nota Importante**: Los archivos `.env` y `config.yaml` deben tener exactamente esos nombres para que la aplicación funcione correctamente. La aplicación busca estos archivos por nombre específico y fallará si no los encuentra.
