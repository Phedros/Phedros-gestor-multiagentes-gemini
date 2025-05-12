# backend/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict # Dict no se usa aquí pero es común

# --- Esquemas para Agentes ---
class AgentBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    system_prompt: str = Field(min_length=10)
    # description: Optional[str] = None

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