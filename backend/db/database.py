# backend/db/database.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv() # Cargar variables de .env

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set for SQLAlchemy")

# Crear un motor asíncrono de SQLAlchemy
# echo=True es útil para desarrollo para ver las consultas SQL generadas. Desactívalo en producción.
engine = create_async_engine(DATABASE_URL, echo=True)

# Crear una clase de sesión asíncrona configurada
# expire_on_commit=False previene que los atributos de los objetos SQLAlchemy expiren después de un commit,
# lo cual es útil en el patrón de FastAPI donde el objeto podría ser devuelto después del commit de la sesión.
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False, # Desactivar autoflush para control manual si es necesario
)

# Clase base para nuestros modelos ORM declarativos
Base = declarative_base()

# Función de dependencia para obtener una sesión de base de datos
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit() # Commit al final si todo fue bien
        except Exception:
            await session.rollback() # Rollback en caso de error
            raise
        finally:
            await session.close()