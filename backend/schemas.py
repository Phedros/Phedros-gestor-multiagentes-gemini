# backend/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict # Dict no se usa aquí pero es común

# --- Esquemas para Agentes ---
class AgentBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    system_prompt: str = Field(min_length=10)
    tools_enabled: Optional[List[str]] = Field(default_factory=list, description="Lista de nombres de herramientas habilitadas para este agente.") # NUEVO

class AgentCreate(AgentBase):
    pass

class Agent(AgentBase): # Esquema para devolver un agente (incluye ID)
    id: str

    class Config: # Pydantic V1
        from_attributes = True # Permite a Pydantic mapear desde modelos ORM
        # En Pydantic V2 sería: model_config = {"from_attributes": True}


# --- Esquemas para Flujos ---
class FlowBase(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    description: Optional[str] = Field(None, max_length=255)
    agent_ids: List[str] = Field(min_length=1)

class FlowCreate(FlowBase):
    pass

class Flow(FlowBase): # Esquema para devolver un flujo (incluye ID)
    id: str

    class Config:
        from_attributes = True

# --- Esquemas para Invocación de Agente Individual ---
class AgentInvokeRequest(BaseModel):
    agent_id: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: str

class AgentInvokeResponse(BaseModel):
    agent_response: str
    used_system_prompt: str

# --- Esquemas para Invocación de Flujo ---
class FlowInvokeRequest(BaseModel):
    initial_user_prompt: str

class FlowInvokeLogStep(BaseModel):
    agent_id: str
    agent_name: str
    input_prompt: str
    output_response: str
    system_prompt_used: str

    class Config:
        from_attributes = True # Si alguna vez creamos un modelo ORM para LogStep

class FlowInvokeResponse(BaseModel):
    final_output: str
    flow_id: str
    flow_name: str
    log: List[FlowInvokeLogStep]

# --- NUEVO: Esquema para Herramientas Disponibles ---
class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict # El schema JSON de los parámetros

class AvailableTool(BaseModel):
    type: str # Debería ser "function"
    function: ToolDefinition

# --- Esquemas para Actualización de Agentes ---
class AgentUpdate(AgentBase): # Opcional: puedes crear uno nuevo si los campos varían mucho
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    system_prompt: Optional[str] = Field(None, min_length=10)
    tools_enabled: Optional[List[str]] = Field(None, description="Lista de nombres de herramientas habilitadas para este agente.")

# --- Esquemas para Actualización de Flujos ---
class FlowUpdate(FlowBase): # Opcional: puedes crear uno nuevo
    name: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = Field(None, max_length=255)
    agent_ids: Optional[List[str]] = Field(None, min_length=1)