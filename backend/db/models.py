# backend/db/models.py
from sqlalchemy import Column, String, Text, ForeignKey, JSON # JSON para la lista de agent_ids
from sqlalchemy.orm import relationship
from .database import Base # Importar Base de nuestro archivo database.py
import uuid # Para generar IDs por defecto

def generate_uuid():
    return str(uuid.uuid4())

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=generate_uuid) # UUID como string
    name = Column(String(100), nullable=False, index=True)
    system_prompt = Column(Text, nullable=False)
    # description = Column(Text, nullable=True) # Podríamos añadir más campos
    # NUEVO: Campo para almacenar la lista de nombres de herramientas permitidas para este agente
    # Ejemplo: ["get_current_weather", "simple_calculator"]
    tools_enabled = Column(JSON, nullable=True, default=[]) # Lista de strings

    # Relación (si quisiéramos acceder a los flujos donde este agente es usado,
    # pero para una lista de IDs en Flow, esta relación es más compleja.
    # Por ahora, no definimos una relación inversa directa desde Agent a Flow
    # debido a que Flow.agent_ids es un campo JSON.)

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}')>"

class Flow(Base):
    __tablename__ = "flows"

    id = Column(String(36), primary_key=True, default=generate_uuid) # UUID como string
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    # Almacenaremos la lista de agent_ids como un JSON array.
    # SQLAlchemy puede manejar tipos JSON que se mapean a tipos JSON nativos de la BD
    # o a TEXT si la BD no tiene un tipo JSON nativo (MySQL sí lo tiene).
    agent_ids = Column(JSON, nullable=False) # Debería ser una lista de strings (UUIDs de agentes)

    def __repr__(self):
        return f"<Flow(id={self.id}, name='{self.name}')>"

# No necesitamos definir aquí relaciones inversas explícitas si Flow.agent_ids
# es solo una lista de IDs. Si fuera una tabla de asociación (muchos a muchos),
# entonces sí definiríamos `relationship` en ambos modelos.