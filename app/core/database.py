from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crear el motor de la base de datos
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verificar conexión antes de usarla
    echo=settings.DEBUG,  # Mostrar SQL solo en modo debug
)

# Crear sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear la clase base para los modelos
Base = declarative_base()

# Función para obtener una sesión de base de datos
def get_db():
    """
    Dependencia para obtener una sesión de base de datos.
    Se usa con Depends en los endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()