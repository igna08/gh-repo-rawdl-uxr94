import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("ERROR: la variable DATABASE_URL no está definida. Revisa tu .env")

print(f"[INFO] Usando DATABASE_URL = {DATABASE_URL}")

engine = create_engine(DATABASE_URL)

# Parámetros de inserción
user_id   = '97f45c67-5c74-493d-bcb6-757c5253d0a1'
role_id   = 1   # Super Admin
school_id = '3708b4de-bf47-4adf-bfe0-eadf152edd8b'

insert_query = text("""
INSERT INTO user_roles (user_id, role_id, school_id)
VALUES (:user_id, :role_id, :school_id)
ON CONFLICT DO NOTHING;
""")

# -- Abrimos un bloque transaccional con engine.begin() para auto-commit --
with engine.begin() as conn:
    conn.execute(insert_query, {
        "user_id":   user_id,
        "role_id":   role_id,
        "school_id": school_id
    })
    # Al salir del with engine.begin(), hace COMMIT automáticamente
    print("[SUCCESS] Rol Super Admin asignado (si no existía).")
