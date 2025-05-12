# backend/main.py
from fastapi import FastAPI, HTTPException, Depends # Depends se usará más adelante
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field # Field para validaciones/defaults
import openai
import os
from dotenv import load_dotenv
from typing import List, Dict, Union, Optional, Any # Any podría ser útil para logs
import uuid # Para generar IDs únicos para los agentes

load_dotenv()

try:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY no encontrada.")
except Exception as e:
    print(f"Error al inicializar el cliente de OpenAI: {e}")
    client = None

app = FastAPI(
    title="API del Gestor Multiagentes",
    version="0.2.0", # Incrementamos versión
    description="Una API para crear y gestionar agentes de IA y flujos multiagentes."
)

origins = ["http://localhost", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- "Base de datos" en memoria ---
# Usaremos un diccionario para guardar los agentes. La clave será el ID del agente.
db_agents: Dict[str, 'AgentConfig'] = {}
db_flows: Dict[str, 'FlowConfig'] = {} # NUEVO: para almacenar flujos

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

@app.post("/api/v1/agents", response_model=AgentConfig, status_code=201)
async def create_agent(agent_data: AgentConfigCreate):
    """
    Crea un nuevo agente con un nombre y un system_prompt.
    Genera un ID único para el agente.
    """
    agent_id = str(uuid.uuid4())
    new_agent = AgentConfig(id=agent_id, **agent_data.model_dump())
    db_agents[agent_id] = new_agent
    print(f"Agente creado: {new_agent}")
    return new_agent

@app.get("/api/v1/agents", response_model=List[AgentConfig])
async def list_agents():
    """
    Devuelve una lista de todos los agentes configurados.
    """
    return list(db_agents.values())

@app.get("/api/v1/agents/{agent_id}", response_model=AgentConfig)
async def get_agent(agent_id: str):
    """
    Obtiene la configuración de un agente específico por su ID.
    """
    agent = db_agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agente con ID '{agent_id}' no encontrado.")
    return agent

# --- NUEVO: Endpoints de Gestión de Flujos ---

@app.post("/api/v1/flows", response_model=FlowConfig, status_code=201)
async def create_flow(flow_data: FlowConfigCreate):
    """
    Crea un nuevo flujo multiagente.
    Valida que todos los agent_ids proporcionados existan.
    """
    # Validar que todos los agent_ids existan
    for agent_id in flow_data.agent_ids:
        if agent_id not in db_agents:
            raise HTTPException(
                status_code=404, # O 400 Bad Request, ya que es un problema con los datos de entrada
                detail=f"Agente con ID '{agent_id}' no encontrado en la configuración del flujo '{flow_data.name}'."
            )

    flow_id = str(uuid.uuid4())
    new_flow = FlowConfig(id=flow_id, **flow_data.model_dump())
    db_flows[flow_id] = new_flow
    print(f"Flujo creado: {new_flow}")
    return new_flow

@app.get("/api/v1/flows", response_model=List[FlowConfig])
async def list_flows():
    """
    Devuelve una lista de todos los flujos configurados.
    """
    return list(db_flows.values())

@app.get("/api/v1/flows/{flow_id}", response_model=FlowConfig)
async def get_flow(flow_id: str):
    """
    Obtiene la configuración de un flujo específico por su ID.
    """
    flow = db_flows.get(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flujo con ID '{flow_id}' no encontrado.")
    return flow

# --- Endpoint de Invocación de Agente (Modificado) ---

@app.post("/api/v1/agent/invoke", response_model=AgentInvokeResponse)
async def invoke_agent(request_data: AgentInvokeRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Cliente de OpenAI no inicializado.")

    actual_system_prompt = ""

    if request_data.agent_id:
        agent_config = db_agents.get(request_data.agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail=f"Agente con ID '{request_data.agent_id}' no encontrado.")
        actual_system_prompt = agent_config.system_prompt
        print(f"Usando system_prompt del agente ID {request_data.agent_id}: {actual_system_prompt}")
    elif request_data.system_prompt:
        actual_system_prompt = request_data.system_prompt
        print(f"Usando system_prompt ad-hoc: {actual_system_prompt}")
    else:
        # Si ni agent_id ni system_prompt se proveen, podríamos usar un default global o dar error.
        # Por ahora, usaremos un default simple si queremos permitirlo, o error.
        # Para que sea más claro, exijamos uno de los dos (o que el modelo AgentInvokeRequest tenga un default)
        # Modificamos AgentInvokeRequest para que system_prompt sea opcional y la lógica aquí maneje si no hay ninguno.
         raise HTTPException(status_code=400, detail="Se debe proveer 'agent_id' o un 'system_prompt'.")


    print(f"User Prompt recibido: {request_data.user_prompt}")

    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": actual_system_prompt},
                {"role": "user", "content": request_data.user_prompt}
            ],
            temperature=0.7,
            max_tokens=250 # Aumenté un poco por si acaso
        )

        agent_text_response = chat_completion.choices[0].message.content if chat_completion.choices else "No se recibió respuesta válida."

        print(f"Respuesta del agente: {agent_text_response}")
        return AgentInvokeResponse(
            agent_response=agent_text_response,
            used_system_prompt=actual_system_prompt # Devolvemos el prompt usado
        )

    except openai.APIConnectionError as e:
        # ... (mismos manejadores de error que antes)
        print(f"Error de conexión con OpenAI: {e}")
        raise HTTPException(status_code=503, detail=f"Error de conexión con la API de OpenAI: {e}")
    except openai.RateLimitError as e:
        print(f"Límite de tasa de OpenAI excedido: {e}")
        raise HTTPException(status_code=429, detail=f"Límite de tasa de OpenAI excedido: {e}")
    except openai.AuthenticationError as e:
        print(f"Error de autenticación con OpenAI (revisa tu API Key): {e}")
        raise HTTPException(status_code=401, detail=f"Error de autenticación con OpenAI (API Key inválida o sin permisos): {e}")
    except openai.APIError as e: # Error genérico de la API de OpenAI
        print(f"Error en la API de OpenAI: {e}")
        raise HTTPException(status_code=500, detail=f"Error en la API de OpenAI: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado en el servidor: {e}")

# --- NUEVO: Endpoint de Invocación de Flujo ---
@app.post("/api/v1/flows/{flow_id}/invoke", response_model=FlowInvokeResponse)
async def invoke_flow(flow_id: str, request_data: FlowInvokeRequest):
    """
    Invoca un flujo multiagente lineal.
    La salida de un agente se convierte en la entrada (user_prompt) del siguiente.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Cliente de OpenAI no inicializado.")

    flow_config = db_flows.get(flow_id)
    if not flow_config:
        raise HTTPException(status_code=404, detail=f"Flujo con ID '{flow_id}' no encontrado.")

    current_input_prompt = request_data.initial_user_prompt
    log_steps: List[FlowInvokeLogStep] = []
    final_flow_output = ""

    print(f"\n--- Iniciando Invocación de Flujo: {flow_config.name} (ID: {flow_id}) ---")
    print(f"Prompt Inicial del Usuario: {current_input_prompt}")

    for i, agent_id_in_flow in enumerate(flow_config.agent_ids):
        agent_config = db_agents.get(agent_id_in_flow)
        if not agent_config:
            # Esto debería haber sido atrapado en la creación del flujo, pero es una buena doble verificación.
            error_detail = f"Configuración del Agente ID '{agent_id_in_flow}' no encontrada durante la ejecución del flujo."
            print(f"ERROR: {error_detail}")
            # Podríamos añadir un log de error aquí también.
            raise HTTPException(status_code=500, detail=error_detail)

        actual_system_prompt = agent_config.system_prompt

        print(f"\n  Paso {i+1}/{len(flow_config.agent_ids)} - Agente: {agent_config.name} (ID: {agent_id_in_flow})")
        print(f"    System Prompt: {actual_system_prompt[:100]}...") # Mostrar solo una parte si es largo
        print(f"    Input (User Prompt): {current_input_prompt[:100]}...")

        try:
            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo", # O el modelo que prefieras
                messages=[
                    {"role": "system", "content": actual_system_prompt},
                    {"role": "user", "content": current_input_prompt}
                ],
                temperature=0.7,
                max_tokens=300 # Podrías querer ajustar esto por agente o por flujo
            )

            agent_text_response = chat_completion.choices[0].message.content if chat_completion.choices else "No se recibió respuesta válida del modelo para este paso."
            print(f"    Output (Respuesta del Agente): {agent_text_response[:100]}...")

        except Exception as e:
            # Capturar cualquier error de la API de OpenAI durante un paso
            error_message = f"Error al invocar al agente '{agent_config.name}' (ID: {agent_id_in_flow}) en el paso {i+1} del flujo: {str(e)}"
            print(f"ERROR: {error_message}")
            # Registrar el error en el log del flujo
            log_steps.append(FlowInvokeLogStep(
                agent_id=agent_id_in_flow,
                agent_name=agent_config.name,
                input_prompt=current_input_prompt,
                output_response=f"ERROR: {error_message}", # Indicar el error en la salida
                system_prompt_used=actual_system_prompt
            ))
            # Devolver una respuesta parcial o un error general del flujo
            # Por ahora, levantamos una excepción que terminará el flujo
            raise HTTPException(status_code=500, detail=error_message)

        log_steps.append(FlowInvokeLogStep(
            agent_id=agent_id_in_flow,
            agent_name=agent_config.name,
            input_prompt=current_input_prompt,
            output_response=agent_text_response,
            system_prompt_used=actual_system_prompt
        ))

        current_input_prompt = agent_text_response # La salida de este agente es la entrada del siguiente
        final_flow_output = agent_text_response # Guardar la salida del último agente ejecutado

    print(f"\n--- Invocación de Flujo '{flow_config.name}' Finalizada ---")
    print(f"Salida Final del Flujo: {final_flow_output[:100]}...")

    return FlowInvokeResponse(
        final_output=final_flow_output,
        flow_id=flow_id,
        flow_name=flow_config.name,
        log=log_steps
    )

# Endpoints de prueba (los mantenemos por ahora)
@app.get("/")
async def get_root():
    return {"message": f"API del Gestor Multiagentes v{app.version}. Estado del cliente OpenAI: {'OK' if client and client.api_key else 'ERROR'}"}

@app.get("/saludo/{nombre}")
async def get_saludo(nombre: str):
    return {"message": f"¡Hola, {nombre}! API v{app.version}."}