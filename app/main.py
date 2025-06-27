from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base

# Import routers
from app.routers import (
    auth, users, schools, classrooms, 
    assets, qr_codes, incidents, subscriptions,
    invitations, dashboard , user_admin
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Función de configuración con el nuevo patrón de lifespan de FastAPI
    """
    # Inicialización de la aplicación
    # Base.metadata.create_all(bind=engine)  # Crear tablas si no existen
    # En producción es mejor usar Alembic para migraciones
    
    # Código de inicialización
    print("Iniciando aplicación de gestión de inventarios...")
    
    yield  # Se ejecuta la aplicación
    
    # Código de limpieza al cerrar
    print("Cerrando aplicación...")

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(schools.router, prefix=settings.API_PREFIX)
app.include_router(classrooms.router, prefix=settings.API_PREFIX)
app.include_router(assets.router, prefix=settings.API_PREFIX)
app.include_router(qr_codes.router, prefix=settings.API_PREFIX)
app.include_router(incidents.router, prefix=settings.API_PREFIX)
app.include_router(subscriptions.router, prefix=settings.API_PREFIX)
app.include_router(invitations.router, prefix=settings.API_PREFIX) # Added
app.include_router(dashboard.router, prefix=settings.API_PREFIX) # Added
app.include_router(user_admin.router, prefix=settings.API_PREFIX) # Added

# Ruta de verificación de salud
@app.get("/")
async def health_check():
    return {
        "status": "ok", 
        "name": settings.PROJECT_NAME, 
        "version": settings.PROJECT_VERSION
    }