# backend/main.py
from fastapi import FastAPI, HTTPException, Depends # Depends se usará más adelante
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field # Field para validaciones/defaults
import openai
import os
from pathlib import Path    
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from typing import List, Dict, Union, Optional, Any # Any podría ser útil para logs
import uuid # Para generar IDs únicos para los agentes

# --- Importaciones de Base de Datos ---
from sqlalchemy.ext.asyncio import AsyncSession
from .db.database import engine, Base, get_db_session # Importar de nuestra carpeta db
from .db import models as db_models # Importar nuestros modelos SQLAlchemy
from . import schemas # Crearemos este archivo para los modelos Pydantic

# --- Importaciones de Pydantic desde schemas.py ---
from .schemas import (
    Agent, AgentCreate, AgentInvokeRequest, AgentInvokeResponse,
    Flow, FlowCreate, FlowInvokeRequest, FlowInvokeResponse, FlowInvokeLogStep
)



try:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY no encontrada.")
except Exception as e:
    print(f"Error al inicializar el cliente de OpenAI: {e}")
    client = None

# --- NUEVO: Función para crear tablas de la BD (para desarrollo) ---
async def create_db_and_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Descomentar para borrar y recrear tablas en cada inicio (¡CUIDADO!)
        await conn.run_sync(Base.metadata.create_all)
        print("Tablas de base de datos creadas (si no existían).")

app = FastAPI(
    title="API del Gestor Multiagentes",
    version="0.3.0", # Incrementamos versión
    description="API con persistencia en MySQL para agentes y flujos."
)

# --- NUEVO: Evento de startup para crear tablas ---
@app.on_event("startup")
async def on_startup():
    print("Aplicación iniciándose...")
    await create_db_and_tables()
    # Aquí podrías poner más lógica de inicialización si es necesario

origins = ["http://localhost", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- "Base de datos" en memoria ---  Esto ya se podria eliminar si usamos una BD real
# Usaremos un diccionario para guardar los agentes. La clave será el ID del agente.
#db_agents: Dict[str, 'AgentConfig'] = {}
#db_flows: Dict[str, 'FlowConfig'] = {} # NUEVO: para almacenar flujos

# --- Modelos Pydantic ---

class AgentConfigBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="Nombre descriptivo del agente.")
    system_prompt: str = Field(..., min_length=10, description="El prompt de sistema que define el comportamiento del agente.")
    # Podríamos añadir 'description', 'tools_available', etc. más adelante

class AgentConfigCreate(AgentConfigBase):
    pass # Hereda todo de AgentConfigBase, usado para la creación

class AgentConfig(AgentConfigBase):
    id: str = Field(..., description="ID único del agente, generado automáticamente.")
    # Aquí podríamos añadir 'created_at', 'updated_at' si tuviéramos una BD real

class AgentInvokeRequest(BaseModel):
    # Opción 1: Usar un agente existente por su ID
    agent_id: Optional[str] = Field(None, description="ID de un agente preconfigurado para usar su system_prompt.")
    # Opción 2: O proveer un system_prompt ad-hoc (como antes)
    # Haremos que agent_id y system_prompt sean mutuamente excluyentes o que agent_id tenga precedencia.
    system_prompt: Optional[str] = Field(None, description="System prompt ad-hoc. Se ignora si se provee agent_id.")
    user_prompt: str = Field(..., description="El prompt del usuario para el agente.")

    # Validación personalizada para asegurar que se use agent_id o system_prompt, pero no necesariamente ambos
    # Pydantic v2 ofrece formas más elegantes con model_validator, pero esto funciona con v1/v2
    # @root_validator(pre=True)
    # def check_prompt_source(cls, values):
    #     # Esta validación se complica si queremos que system_prompt sea opcional y tenga default
    #     # Por ahora, la lógica la manejaremos en el endpoint.
    #     return values


class AgentInvokeResponse(BaseModel):
    agent_response: str
    used_system_prompt: str # Para saber qué system_prompt se usó realmente

class FlowConfigBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Nombre descriptivo del flujo.")
    description: Optional[str] = Field(None, max_length=255, description="Descripción opcional del flujo.")
    agent_ids: List[str] = Field(..., min_length=1, description="Lista ordenada de IDs de agentes que componen el flujo.")
    # Para flujos lineales, el orden es crucial. Mínimo 1 agente.

class FlowConfigCreate(FlowConfigBase):
    pass

class FlowConfig(FlowConfigBase):
    id: str = Field(..., description="ID único del flujo, generado automáticamente.")

class FlowInvokeRequest(BaseModel):
    initial_user_prompt: str = Field(..., description="El prompt inicial del usuario para el primer agente del flujo.")

class FlowInvokeLogStep(BaseModel):
    agent_id: str
    agent_name: str # Para facilitar la lectura del log
    input_prompt: str # Lo que recibió este agente como user_prompt
    output_response: str # Lo que respondió este agente
    system_prompt_used: str

class FlowInvokeResponse(BaseModel):
    final_output: str # La respuesta del último agente del flujo
    flow_id: str
    flow_name: str
    log: List[FlowInvokeLogStep] # Un log de cada paso del flujo

# --- Endpoints de Gestión de Agentes ---

@app.post("/api/v1/agents", response_model=schemas.Agent, status_code=201)
async def create_agent_endpoint(
    agent_data: schemas.AgentCreate,
    db: AsyncSession = Depends(get_db_session)
):
    db_agent = db_models.Agent(
        name=agent_data.name,
        system_prompt=agent_data.system_prompt
    )
    db.add(db_agent)
    await db.flush()           # ← acá se dispara el default y ya tenés el UUID
    # opcional: print(db_agent.id)  # comprobá que ahora NO es None
    return db_agent


@app.get("/api/v1/agents", response_model=List[schemas.Agent])
async def list_agents_endpoint(
    skip: int = 0, # Paginación simple
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(
        db_models.Agent.__table__.select().offset(skip).limit(limit)
    )
    agents = result.fetchall()
    # Pydantic V2 directamente con `return agents` si el modelo tiene from_attributes
    # Para Pydantic V1, a veces se necesita convertir explícitamente si la inferencia falla
    # return [schemas.Agent.from_orm(agent) for agent in agents] # Esto es más explícito
    return agents # FastAPI/Pydantic debería manejar la conversión

@app.get("/api/v1/agents/{agent_id}", response_model=schemas.Agent)
async def get_agent_endpoint(agent_id: str, db: AsyncSession = Depends(get_db_session)):
    agent = await db.get(db_models.Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    return agent

# --- NUEVO: Endpoints de Gestión de Flujos ---

@app.post("/api/v1/flows", response_model=schemas.Flow, status_code=201)
async def create_flow_endpoint(
    flow_data: schemas.FlowCreate,
    db: AsyncSession = Depends(get_db_session)
):
    # 1) Verificar que existan los agentes
    for agent_id in flow_data.agent_ids:
        if not await db.get(db_models.Agent, agent_id):
            raise HTTPException(400, f"Agente con ID '{agent_id}' no encontrado.")

    # 2) Crear el flujo
    db_flow = db_models.Flow(
        name=flow_data.name,
        description=flow_data.description,
        agent_ids=flow_data.agent_ids
    )
    db.add(db_flow)

    # 🔑 Dispara el INSERT y genera el UUID
    await db.flush()
    await db.refresh(db_flow)

    return db_flow


@app.get("/api/v1/flows", response_model=List[schemas.Flow])
async def list_flows_endpoint(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(
        db_models.Flow.__table__.select().offset(skip).limit(limit)
    )
    flows = result.fetchall()
    return flows

@app.get("/api/v1/flows/{flow_id}", response_model=schemas.Flow)
async def get_flow_endpoint(flow_id: str, db: AsyncSession = Depends(get_db_session)):
    flow = await db.get(db_models.Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flujo no encontrado.")
    return flow

# --- Endpoint de Invocación de Agente Individual (AHORA CON BD) ---
@app.post("/api/v1/agent/invoke", response_model=schemas.AgentInvokeResponse)
async def invoke_agent_endpoint( # Renombrado para consistencia
    request_data: schemas.AgentInvokeRequest,
    db: AsyncSession = Depends(get_db_session) # Inyectar sesión
):
    if not client: # cliente OpenAI
        raise HTTPException(status_code=500, detail="Cliente de OpenAI no inicializado.")

    actual_system_prompt = ""
    agent_name_for_log = "Ad-hoc" # Nombre por defecto para el log

    if request_data.agent_id:
        agent_config_db = await db.get(db_models.Agent, request_data.agent_id) # Obtener de BD
        if not agent_config_db:
            raise HTTPException(status_code=404, detail=f"Agente con ID '{request_data.agent_id}' no encontrado.")
        actual_system_prompt = agent_config_db.system_prompt
        agent_name_for_log = agent_config_db.name
        print(f"Usando system_prompt del agente ID {request_data.agent_id} ({agent_name_for_log})")
    elif request_data.system_prompt:
        actual_system_prompt = request_data.system_prompt
        print(f"Usando system_prompt ad-hoc")
    else:
         raise HTTPException(status_code=400, detail="Se debe proveer 'agent_id' o un 'system_prompt'.")

    # ... (lógica de llamada a OpenAI y manejo de errores sin cambios significativos,
    #      solo asegúrate de que usa `actual_system_prompt`) ...
    try:
        # ... (llamada a client.chat.completions.create) ...
        chat_completion = client.chat.completions.create( # Asegúrate que esta parte esté
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": actual_system_prompt},
                {"role": "user", "content": request_data.user_prompt}
            ],
            temperature=0.7, max_tokens=250
        )
        agent_text_response = chat_completion.choices[0].message.content if chat_completion.choices else "No se recibió respuesta válida."
        return schemas.AgentInvokeResponse(
            agent_response=agent_text_response,
            used_system_prompt=actual_system_prompt
        )
    except Exception as e: # Simplificado, pero deberías tener los manejadores de error de OpenAI
        print(f"Error en OpenAI o invocación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint de Invocación de Flujo (AHORA CON BD) ---
@app.post("/api/v1/flows/{flow_id}/invoke", response_model=schemas.FlowInvokeResponse)
async def invoke_flow_endpoint( # Renombrado
    flow_id: str,
    request_data: schemas.FlowInvokeRequest,
    db: AsyncSession = Depends(get_db_session) # Inyectar sesión
):
    if not client: # cliente OpenAI
        raise HTTPException(status_code=500, detail="Cliente de OpenAI no inicializado.")

    flow_config_db = await db.get(db_models.Flow, flow_id) # Obtener de BD
    if not flow_config_db:
        raise HTTPException(status_code=404, detail=f"Flujo con ID '{flow_id}' no encontrado.")

    current_input_prompt = request_data.initial_user_prompt
    log_steps: List[schemas.FlowInvokeLogStep] = [] # Usar el schema Pydantic para el log
    final_flow_output = ""

    # ... (Lógica de iteración sobre flow_config_db.agent_ids) ...
    # Dentro del bucle, para cada agent_id_in_flow:
    # agent_config_db_step = await db.get(db_models.Agent, agent_id_in_flow)
    # if not agent_config_db_step: raise HTTPException(...)
    # actual_system_prompt_step = agent_config_db_step.system_prompt
    # ... (llamada a OpenAI) ...
    # log_steps.append(schemas.FlowInvokeLogStep(...))
    # ... (actualizar current_input_prompt)

    print(f"\n--- Iniciando Invocación de Flujo: {flow_config_db.name} (ID: {flow_id}) ---")
    print(f"Prompt Inicial del Usuario: {current_input_prompt}")

    for i, agent_id_in_flow in enumerate(flow_config_db.agent_ids): # agent_ids es una lista JSON
        agent_config_db_step = await db.get(db_models.Agent, agent_id_in_flow)
        if not agent_config_db_step:
            error_detail = f"Configuración del Agente ID '{agent_id_in_flow}' no encontrada durante la ejecución del flujo."
            print(f"ERROR: {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)

        actual_system_prompt_step = agent_config_db_step.system_prompt

        print(f"\n  Paso {i+1}/{len(flow_config_db.agent_ids)} - Agente: {agent_config_db_step.name} (ID: {agent_id_in_flow})")
        # ... (resto de los prints de log) ...

        try:
            # ... (llamada a client.chat.completions.create con actual_system_prompt_step y current_input_prompt)
            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": actual_system_prompt_step},
                    {"role": "user", "content": current_input_prompt}
                ],
                temperature=0.7, max_tokens=300
            )
            agent_text_response = chat_completion.choices[0].message.content if chat_completion.choices else "No se recibió respuesta."

        except Exception as e:
            error_message = f"Error al invocar al agente '{agent_config_db_step.name}' (ID: {agent_id_in_flow}) en el paso {i+1} del flujo: {str(e)}"
            # ... (manejo de error y append al log) ...
            log_steps.append(schemas.FlowInvokeLogStep(
                agent_id=agent_id_in_flow, agent_name=agent_config_db_step.name,
                input_prompt=current_input_prompt, output_response=f"ERROR: {error_message}",
                system_prompt_used=actual_system_prompt_step
            ))
            raise HTTPException(status_code=500, detail=error_message)

        log_steps.append(schemas.FlowInvokeLogStep(
            agent_id=agent_id_in_flow, agent_name=agent_config_db_step.name,
            input_prompt=current_input_prompt, output_response=agent_text_response,
            system_prompt_used=actual_system_prompt_step
        ))

        current_input_prompt = agent_text_response
        final_flow_output = agent_text_response

    # ... (print de finalización) ...
    return schemas.FlowInvokeResponse(
        final_output=final_flow_output,
        flow_id=flow_id,
        flow_name=flow_config_db.name,
        log=log_steps
    )


# --- Endpoints de / y /saludo (sin cambios) ---
@app.get("/")
async def get_root_endpoint(): # Renombrado
    return {"message": f"API del Gestor Multiagentes v{app.version}. Persistencia: MySQL. Estado OpenAI: {'OK' if client and client.api_key else 'ERROR'}"}

@app.get("/saludo/{nombre}")
async def get_saludo_endpoint(nombre: str): # Renombrado
    return {"message": f"¡Hola, {nombre}! API v{app.version}."}