# backend/main.py
from fastapi import FastAPI, HTTPException, Depends # Depends se usará más adelante
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field # Field para validaciones/defaults
from sqlalchemy.future import select # Necesario para SQLAlchemy 2.0 style queries si lo usas
import openai
import os
from pathlib import Path    
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")
import json

from typing import List, Dict, Union, Optional, Any # Any podría ser útil para logs
import uuid # Para generar IDs únicos para los agentes

# --- Importaciones de Base de Datos ---
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, JSON # Asegúrate de importar func y select
from .db.database import engine, Base, get_db_session # Importar de nuestra carpeta db
from .db import models as db_models # Importar nuestros modelos SQLAlchemy
from . import schemas # Crearemos este archivo para los modelos Pydantic

# --- Importaciones de Pydantic desde schemas.py ---
from .schemas import (
    Agent, AgentCreate, AgentInvokeRequest, AgentInvokeResponse,
    Flow, FlowCreate, FlowInvokeRequest, FlowInvokeResponse, FlowInvokeLogStep, AvailableTool 
)

from .agent_tools.available_tools import AVAILABLE_TOOLS_SCHEMAS, TOOL_NAME_TO_FUNCTION_MAP


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
    if agent_data.tools_enabled:
        valid_tool_names = [tool_schema["function"]["name"] for tool_schema in AVAILABLE_TOOLS_SCHEMAS]
        for tool_name in agent_data.tools_enabled:
            if tool_name not in valid_tool_names:
                raise HTTPException(
                    status_code=400,
                    detail=f"Herramienta '{tool_name}' no es una herramienta válida. Las herramientas disponibles son: {', '.join(valid_tool_names)}"
                )
    db_agent = db_models.Agent(
        name=agent_data.name,
        system_prompt=agent_data.system_prompt,
        tools_enabled=agent_data.tools_enabled or []
    )
    db.add(db_agent)
    await db.flush()
    await db.refresh(db_agent)
    return db_agent


@app.get("/api/v1/agents", response_model=List[schemas.Agent])
async def list_agents_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    # Usar select() directamente con el modelo para SQLAlchemy 2.0 style
    stmt = select(db_models.Agent).offset(skip).limit(limit)
    result = await db.execute(stmt)
    agents = result.scalars().all()
    return agents

@app.get("/api/v1/agents/{agent_id}", response_model=schemas.Agent)
async def get_agent_endpoint(agent_id: str, db: AsyncSession = Depends(get_db_session)):
    agent = await db.get(db_models.Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    return agent

@app.put("/api/v1/agents/{agent_id}", response_model=schemas.Agent)
async def update_agent_endpoint(
    agent_id: str,
    agent_data: schemas.AgentUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    db_agent = await db.get(db_models.Agent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")

    update_data = agent_data.model_dump(exclude_unset=True) # Pydantic v2

    if "tools_enabled" in update_data and update_data["tools_enabled"] is not None:
        valid_tool_names = [tool_schema["function"]["name"] for tool_schema in AVAILABLE_TOOLS_SCHEMAS]
        for tool_name in update_data["tools_enabled"]:
            if tool_name not in valid_tool_names:
                raise HTTPException(
                    status_code=400,
                    detail=f"Herramienta '{tool_name}' no es una herramienta válida."
                )
    
    for key, value in update_data.items():
        setattr(db_agent, key, value)
    
    db.add(db_agent)
    await db.flush()
    await db.refresh(db_agent)
    return db_agent

@app.delete("/api/v1/agents/{agent_id}", status_code=204)
async def delete_agent_endpoint(
    agent_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    db_agent = await db.get(db_models.Agent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")

    # --- MODIFICADO: Verificar si el agente está en uso en algún flujo ---
    # Construir el valor a buscar en el JSON array. MySQL JSON_CONTAINS espera un valor JSON,
    # así que casteamos el agent_id (que es un string) a un string JSON.
    # Para buscar 'some_string' en un array JSON como ["id1", "some_string"],
    # el segundo argumento de JSON_CONTAINS debe ser '"some_string"' (un string JSON).
    # En SQLAlchemy, esto se puede lograr con func.json_quote para algunos dialectos,
    # o simplemente asegurándose de que el valor comparado sea un string JSON válido.
    # Una forma más directa es usar `func.cast(agent_id, JSON)` si el motor lo interpreta bien,
    # o construir el string JSON `f'"{agent_id}"'` y castearlo a JSON.

    # Para MySQL, JSON_CONTAINS(json_doc, val[, path])
    # Si agent_ids es como ["id1", "id2"], queremos buscar si agent_id es uno de esos elementos.
    # El valor a buscar (val) debe ser un escalar JSON o un candidato de array/objeto.
    # Aquí agent_id es un string, así que necesitamos compararlo con los strings dentro del array JSON.
    # La forma más segura es castear agent_id a un tipo que SQLAlchemy sepa que debe ser tratado como un literal JSON string para la comparación.
    
    # Se crea un valor JSON que representa el string del ID del agente.
    # Por ejemplo, si agent_id es "abc", json_string_agent_id será '"abc"'.
    # Esto es necesario porque JSON_CONTAINS busca un *valor* JSON dentro del array JSON.
    json_string_agent_id = json.dumps(agent_id)


    flows_using_agent_query = select(db_models.Flow).where(
        func.json_contains(db_models.Flow.agent_ids, func.cast(json_string_agent_id, JSON))
    )
    # Alternativamente, si tu base de datos y SQLAlchemy pueden inferirlo mejor,
    # podrías intentar con `func.json_contains(db_models.Flow.agent_ids, agent_id)`
    # pero el casteo explícito o el formateo como string JSON es más robusto.

    result = await db.execute(flows_using_agent_query)
    flows_using_this_agent = result.scalars().all()

    if flows_using_this_agent:
        flow_names = ", ".join([f.name for f in flows_using_this_agent])
        detail_message = f"Agente '{db_agent.name}' no puede ser eliminado. Está siendo utilizado en los siguientes flujos: {flow_names}."
        print(f"Intento de eliminación bloqueado: {detail_message}") # Log para el servidor
        raise HTTPException(
            status_code=409, # 409 Conflict es apropiado aquí
            detail=detail_message
        )
    
    # Si no está en uso, proceder a eliminar
    await db.delete(db_agent)
    await db.flush() # Aplicar el cambio a la BD
    # No es necesario `await db.commit()` aquí si `get_db_session` lo maneja
    return # Devuelve 204 No Content

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

MAX_TOOL_CALLS_PER_INVOCATION = 5 # Para evitar bucles infinitos

@app.put("/api/v1/flows/{flow_id}", response_model=schemas.Flow)
async def update_flow_endpoint(
    flow_id: str,
    flow_data: schemas.FlowUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    db_flow = await db.get(db_models.Flow, flow_id)
    if not db_flow:
        raise HTTPException(status_code=404, detail="Flujo no encontrado.")

    update_data = flow_data.model_dump(exclude_unset=True) # Pydantic v2

    if "agent_ids" in update_data and update_data["agent_ids"] is not None:
        for agent_id_in_flow_update in update_data["agent_ids"]:
            agent = await db.get(db_models.Agent, agent_id_in_flow_update)
            if not agent:
                raise HTTPException(status_code=400, detail=f"Agente con ID '{agent_id_in_flow_update}' no encontrado al actualizar flujo.")
    
    for key, value in update_data.items():
        setattr(db_flow, key, value)
        
    db.add(db_flow)
    await db.flush()
    await db.refresh(db_flow)
    return db_flow

@app.delete("/api/v1/flows/{flow_id}", status_code=204)
async def delete_flow_endpoint(
    flow_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    db_flow = await db.get(db_models.Flow, flow_id)
    if not db_flow:
        raise HTTPException(status_code=404, detail="Flujo no encontrado.")
    
    await db.delete(db_flow)
    await db.flush()
    return

# ... (resto de tus endpoints: invoke_agent_endpoint, invoke_flow_endpoint, list_available_tools, etc.)
# Asegúrate de que las importaciones necesarias como `json`, `func` y `select` de SQLAlchemy estén presentes.


# --- Endpoint de Invocación de Agente Individual (AHORA CON BD) ---
@app.post("/api/v1/agent/invoke", response_model=schemas.AgentInvokeResponse)
async def invoke_agent_endpoint(
    request_data: schemas.AgentInvokeRequest, # Corregido a schemas.AgentInvokeRequest
    db: AsyncSession = Depends(get_db_session)
):
    if not client:
        raise HTTPException(status_code=500, detail="Cliente de OpenAI no inicializado.")

    actual_system_prompt = ""
    agent_name_for_log = "Ad-hoc"
    agent_id_for_log = "ad-hoc" # Usar el ID real si se usa un agente existente

    agent_tools_to_pass_to_llm = [] 
    agent_enabled_tool_names = []  

    if request_data.agent_id:
        agent_config_db = await db.get(db_models.Agent, request_data.agent_id)
        if not agent_config_db:
            raise HTTPException(status_code=404, detail=f"Agente con ID '{request_data.agent_id}' no encontrado.")
        actual_system_prompt = agent_config_db.system_prompt
        agent_name_for_log = agent_config_db.name
        agent_id_for_log = agent_config_db.id 
        agent_enabled_tool_names = agent_config_db.tools_enabled or []

        if agent_enabled_tool_names:
            for tool_schema in AVAILABLE_TOOLS_SCHEMAS:
                if tool_schema["function"]["name"] in agent_enabled_tool_names:
                    agent_tools_to_pass_to_llm.append(tool_schema)
        
        print(f"Usando agente: {agent_name_for_log} (ID: {agent_id_for_log}) con herramientas: {agent_enabled_tool_names}")
    elif request_data.system_prompt:
        actual_system_prompt = request_data.system_prompt
        print(f"Usando system_prompt ad-hoc (sin herramientas por defecto)")
    else:
         raise HTTPException(status_code=400, detail="Se debe proveer 'agent_id' o un 'system_prompt'.")

    messages = [
        {"role": "system", "content": actual_system_prompt},
        {"role": "user", "content": request_data.user_prompt}
    ]

    print(f"\n--- Iniciando Invocación de Agente: {agent_name_for_log} ---")
    print(f"  User Prompt Inicial: {request_data.user_prompt[:200]}...")
    if agent_tools_to_pass_to_llm:
         print(f"  Herramientas disponibles para el LLM: {[t['function']['name'] for t in agent_tools_to_pass_to_llm]}")

    tool_calls_count = 0
    openai_call_attempts = 0
    MAX_TOOL_CALLS_PER_INVOCATION = 5 

    while tool_calls_count < MAX_TOOL_CALLS_PER_INVOCATION:
        try:
            openai_call_attempts += 1
            print(f"--> Enviando a OpenAI (Llamada LLM #{openai_call_attempts}): {len(messages)} mensajes.")

            openai_call_params = {
                "model": "gpt-3.5-turbo", 
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 350
            }
            if agent_tools_to_pass_to_llm:
                openai_call_params["tools"] = agent_tools_to_pass_to_llm
                openai_call_params["tool_choice"] = "auto"

            chat_completion = client.chat.completions.create(**openai_call_params)
            response_message = chat_completion.choices[0].message

        except Exception as e: 
            print(f"Error en llamada a OpenAI: {e}")
            raise HTTPException(status_code=500, detail=f"Error en llamada a OpenAI: {str(e)}")

        if response_message.tool_calls:
            print(f" <-- LLM solicitó {len(response_message.tool_calls)} llamada(s) a herramientas.")
            messages.append(response_message) 

            for tool_call in response_message.tool_calls:
                tool_calls_count += 1
                function_name = tool_call.function.name
                function_args_str = tool_call.function.arguments

                print(f"    [Procesando Herramienta #{tool_calls_count}]")
                print(f"      ID Llamada: {tool_call.id}")
                print(f"      Función: {function_name}")
                print(f"      Argumentos: {function_args_str}")

                try:
                    function_args = json.loads(function_args_str)
                except json.JSONDecodeError:
                    error_msg = f"Error: Argumentos de la función '{function_name}' no son JSON válido: {function_args_str}"
                    print(f"    ERROR: {error_msg}")
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"error": "Argumentos no válidos", "details": error_msg}),
                    })
                    continue

                if function_name in TOOL_NAME_TO_FUNCTION_MAP:
                    function_to_call = TOOL_NAME_TO_FUNCTION_MAP[function_name]
                    try:
                        print(f"      Ejecutando: {function_name}(**{function_args})")
                        function_response = function_to_call(**function_args)
                        response_preview = str(function_response)
                        if len(response_preview) > 200:
                            response_preview = response_preview[:197] + "..."
                        print(f"      Respuesta Herramienta: {response_preview}") 

                    except Exception as e:
                        print(f"    ERROR al ejecutar la herramienta '{function_name}': {str(e)}")
                        function_response = json.dumps({"error": f"Error al ejecutar la herramienta: {str(e)}"})

                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(function_response), 
                    })
                else:
                    print(f"    ERROR: Función '{function_name}' desconocida.")
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"error": f"Función '{function_name}' no implementada o desconocida."}),
                    })
        else: 
            print(f" <-- LLM devolvió respuesta final de texto.")
            agent_text_response = response_message.content or "El agente no proporcionó contenido."
            print(f"--- Invocación de Agente '{agent_name_for_log}' Finalizada ---")
            return schemas.AgentInvokeResponse(
                agent_response=agent_text_response,
                used_system_prompt=actual_system_prompt
            )

    print(f"ERROR: Se excedió el máximo de llamadas a herramientas ({MAX_TOOL_CALLS_PER_INVOCATION}).")
    raise HTTPException(status_code=400, detail=f"Se excedió el máximo de {MAX_TOOL_CALLS_PER_INVOCATION} llamadas a herramientas.")



# --- Endpoint de Invocación de Flujo (AHORA CON BD) ---
@app.post("/api/v1/flows/{flow_id}/invoke", response_model=schemas.FlowInvokeResponse)
async def invoke_flow_endpoint(
    flow_id: str,
    request_data: schemas.FlowInvokeRequest, # Corregido a schemas.FlowInvokeRequest
    db: AsyncSession = Depends(get_db_session)
):
    if not client:
        raise HTTPException(status_code=500, detail="Cliente de OpenAI no inicializado.")

    flow_config_db = await db.get(db_models.Flow, flow_id)
    if not flow_config_db:
        raise HTTPException(status_code=404, detail=f"Flujo con ID '{flow_id}' no encontrado.")

    current_input_prompt = request_data.initial_user_prompt
    log_steps: List[schemas.FlowInvokeLogStep] = []
    final_flow_output = ""

    print(f"\n--- Iniciando Invocación de Flujo: {flow_config_db.name} (ID: {flow_id}) ---")
    print(f"Prompt Inicial del Usuario: {current_input_prompt}")

    for i, agent_id_in_flow in enumerate(flow_config_db.agent_ids):
        agent_config_db_step = await db.get(db_models.Agent, agent_id_in_flow)
        if not agent_config_db_step:
            error_detail = f"Configuración del Agente ID '{agent_id_in_flow}' no encontrada."
            print(f"ERROR: {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)

        actual_system_prompt_step = agent_config_db_step.system_prompt
        print(f"\n  Paso {i+1}/{len(flow_config_db.agent_ids)} - Agente: {agent_config_db_step.name} (ID: {agent_id_in_flow})")
        print(f"    System Prompt: {actual_system_prompt_step[:100]}...")
        print(f"    Input Prompt: {current_input_prompt[:100]}...")

        try:
            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": actual_system_prompt_step},
                    {"role": "user", "content": current_input_prompt}
                ],
                temperature=0.7, max_tokens=300
            )
            agent_text_response = chat_completion.choices[0].message.content if chat_completion.choices and chat_completion.choices[0].message.content else "No se recibió respuesta del agente."
            print(f"    Output Respuesta: {agent_text_response[:100]}...")

        except Exception as e:
            error_message = f"Error al invocar al agente '{agent_config_db_step.name}' (ID: {agent_id_in_flow}) en el paso {i+1} del flujo: {str(e)}"
            print(f"ERROR: {error_message}")
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
    
    print(f"--- Invocación de Flujo '{flow_config_db.name}' Finalizada ---")
    return schemas.FlowInvokeResponse(
        final_output=final_flow_output,
        flow_id=flow_id,
        flow_name=flow_config_db.name,
        log=log_steps
    )

@app.get("/api/v1/tools/available", response_model=List[schemas.AvailableTool])
async def list_available_tools():
    """
    Devuelve una lista de todas las herramientas disponibles en el sistema
    con sus descripciones y esquemas de parámetros.
    """
    # AVAILABLE_TOOLS_SCHEMAS ya tiene el formato correcto que espera Pydantic
    # si coincide con el schema AvailableTool.
    # Vamos a asegurar que se parseen correctamente por Pydantic.
    # Si AVAILABLE_TOOLS_SCHEMAS es una lista de dicts que ya cumplen la estructura,
    # FastAPI/Pydantic deberían manejarlo.
    
    # Simplemente devolvemos la constante que ya tenemos
    # Pydantic validará si su estructura coincide con List[schemas.AvailableTool]
    # Si no coincide, levantará un error en el servidor, lo cual es bueno para desarrollo.
    return AVAILABLE_TOOLS_SCHEMAS


@app.put("/api/v1/flows/{flow_id}", response_model=schemas.Flow)
async def update_flow_endpoint(
    flow_id: str,
    flow_data: schemas.FlowUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    db_flow = await db.get(db_models.Flow, flow_id)
    if not db_flow:
        raise HTTPException(status_code=404, detail="Flujo no encontrado.")

    update_data = flow_data.model_dump(exclude_unset=True) # Pydantic v2

    if "agent_ids" in update_data and update_data["agent_ids"] is not None:
        for agent_id_in_flow_update in update_data["agent_ids"]:
            agent = await db.get(db_models.Agent, agent_id_in_flow_update)
            if not agent:
                raise HTTPException(status_code=400, detail=f"Agente con ID '{agent_id_in_flow_update}' no encontrado al actualizar flujo.")
    
    for key, value in update_data.items():
        setattr(db_flow, key, value)
        
    db.add(db_flow)
    await db.flush()
    await db.refresh(db_flow)
    return db_flow

@app.delete("/api/v1/flows/{flow_id}", status_code=204)
async def delete_flow_endpoint(
    flow_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    db_flow = await db.get(db_models.Flow, flow_id)
    if not db_flow:
        raise HTTPException(status_code=404, detail="Flujo no encontrado.")
    
    await db.delete(db_flow)
    await db.flush()
    return


# --- Endpoints de / y /saludo (sin cambios) ---
@app.get("/")
async def get_root_endpoint(): # Renombrado
    return {"message": f"API del Gestor Multiagentes v{app.version}. Persistencia: MySQL. Estado OpenAI: {'OK' if client and client.api_key else 'ERROR'}"}

@app.get("/saludo/{nombre}")
async def get_saludo_endpoint(nombre: str): # Renombrado
    return {"message": f"¡Hola, {nombre}! API v{app.version}."}

# --- Importación de Herramientas y Mapas (al final o en un archivo separado si crece mucho) ---
from .agent_tools.available_tools import AVAILABLE_TOOLS_SCHEMAS, TOOL_NAME_TO_FUNCTION_MAP