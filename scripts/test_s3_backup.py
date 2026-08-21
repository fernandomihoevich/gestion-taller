import sys
import os

# Asegurar que el directorio raíz del proyecto esté en sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database_adapter import crear_respaldo_db, _get_s3_config

if __name__ == '__main__':
    print('S3 config:', _get_s3_config())
    path = crear_respaldo_db()
    print('Backup created at:', path)
