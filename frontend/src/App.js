// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';

// URLs de la API (buena práctica definirlas en un solo lugar)
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

function App() {
  // --- Estados para conexión raíz (sin cambios) ---
  const [rootMessage, setRootMessage] = useState('');
  const [rootLoading, setRootLoading] = useState(true);
  const [rootError, setRootError] = useState(null);

  // --- Estados para la Invocación del Agente (modificados ligeramente) ---
  const [selectedAgentId, setSelectedAgentId] = useState(''); // Para el <select>
  const [adhocSystemPrompt, setAdhocSystemPrompt] = useState('Eres un asistente virtual útil y conciso.'); // Para el textarea de system prompt ad-hoc
  const [userPrompt, setUserPrompt] = useState('');
  const [agentResponse, setAgentResponse] = useState('');
  const [usedSystemPromptInResponse, setUsedSystemPromptInResponse] = useState(''); // Para mostrar qué system prompt se usó
  const [isAgentInvoking, setIsAgentInvoking] = useState(false);
  const [agentInvokeError, setAgentInvokeError] = useState(null);

  // --- Estados para la Gestión de Agentes ---
  const [agentsList, setAgentsList] = useState([]); // Lista de agentes desde el backend
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [loadAgentsError, setLoadAgentsError] = useState(null);

  // --- Estados para el Formulario de Creación de Nuevo Agente ---
  const [newAgentName, setNewAgentName] = useState('');
  const [newAgentSystemPrompt, setNewAgentSystemPrompt] = useState('');
  const [isCreatingAgent, setIsCreatingAgent] = useState(false);
  const [createAgentError, setCreateAgentError] = useState(null);
  const [createAgentSuccess, setCreateAgentSuccess] = useState('');


  // --- Efecto para cargar mensaje raíz y lista de agentes al montar ---
  useEffect(() => {
    // Cargar mensaje raíz
    fetch('http://127.0.0.1:8000/') // URL raíz del backend
      .then(response => {
        if (!response.ok) throw new Error(`Error HTTP raíz: ${response.status}`);
        return response.json();
      })
      .then(data => setRootMessage(data.message))
      .catch(err => setRootError(err.message))
      .finally(() => setRootLoading(false));

    // Cargar lista de agentes
    fetchAgentsList();
  }, []);


  // --- Funciones para Gestión de Agentes ---
  const fetchAgentsList = async () => {
    setIsLoadingAgents(true);
    setLoadAgentsError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/agents`);
      if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
      const data = await response.json();
      setAgentsList(data);
    } catch (err) {
      console.error("Error al cargar agentes:", err);
      setLoadAgentsError(err.message);
      setAgentsList([]); // Asegurarse que la lista esté vacía en caso de error
    } finally {
      setIsLoadingAgents(false);
    }
  };

  const handleCreateAgent = async (event) => {
    event.preventDefault();
    setIsCreatingAgent(true);
    setCreateAgentError(null);
    setCreateAgentSuccess('');
    try {
      const response = await fetch(`${API_BASE_URL}/agents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newAgentName,
          system_prompt: newAgentSystemPrompt,
        }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }
      const newAgent = await response.json();
      setCreateAgentSuccess(`¡Agente "${newAgent.name}" creado con ID: ${newAgent.id}!`);
      setNewAgentName(''); // Limpiar formulario
      setNewAgentSystemPrompt(''); // Limpiar formulario
      fetchAgentsList(); // Recargar la lista de agentes
    } catch (err) {
      console.error("Error al crear agente:", err);
      setCreateAgentError(err.message);
    } finally {
      setIsCreatingAgent(false);
    }
  };

  // --- Función para Invocar al Agente (Modificada) ---
  const handleInvokeAgent = async (event) => {
    event.preventDefault();
    setIsAgentInvoking(true);
    setAgentResponse('');
    setUsedSystemPromptInResponse('');
    setAgentInvokeError(null);

    let requestBody = {
      user_prompt: userPrompt,
      // agent_id o system_prompt se añadirán condicionalmente
    };

    if (selectedAgentId) {
      requestBody.agent_id = selectedAgentId;
    } else {
      requestBody.system_prompt = adhocSystemPrompt;
    }

    // Validación simple: no permitir invocar si no hay user_prompt
    if (!userPrompt.trim()) {
        setAgentInvokeError("El 'User Prompt' no puede estar vacío.");
        setIsAgentInvoking(false);
        return;
    }
    // Validación: si no hay agent_id seleccionado, debe haber un system_prompt adhoc
    if (!selectedAgentId && !adhocSystemPrompt.trim()) {
        setAgentInvokeError("Debes seleccionar un agente existente o proveer un 'System Prompt Ad-hoc'.");
        setIsAgentInvoking(false);
        return;
    }


    try {
      const response = await fetch(`${API_BASE_URL}/agent/invoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }

      const data = await response.json();
      setAgentResponse(data.agent_response);
      setUsedSystemPromptInResponse(data.used_system_prompt);

    } catch (err) {
      console.error("Error al invocar al agente:", err);
      setAgentInvokeError(err.message);
    } finally {
      setIsAgentInvoking(false);
    }
  };

  // --- Renderizado (se va a volver grande, luego podríamos componentizar) ---
  if (rootLoading) {
    return <div className="App-header"><h1>Cargando conexión con el backend...</h1></div>;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Gestor Multiagentes</h1>
        {rootError ? (
          <p style={{ color: 'orange' }}>{rootError}</p>
        ) : (
          <p style={{ color: 'lightgreen', fontSize: 'small' }}>{rootMessage}</p>
        )}
      </header>

      <div className="main-content-grid">
        {/* --- Sección de Crear Agente --- */}
        <section className="card">
          <h2>Crear Nuevo Agente</h2>
          <form onSubmit={handleCreateAgent} className="agent-form">
            <div className="form-group">
              <label htmlFor="newAgentName">Nombre del Agente:</label>
              <input
                type="text"
                id="newAgentName"
                value={newAgentName}
                onChange={(e) => setNewAgentName(e.target.value)}
                placeholder="Ej: Experto en Historia Antigua"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="newAgentSystemPrompt">System Prompt del Nuevo Agente:</label>
              <textarea
                id="newAgentSystemPrompt"
                value={newAgentSystemPrompt}
                onChange={(e) => setNewAgentSystemPrompt(e.target.value)}
                rows="4"
                placeholder="Ej: Eres un catedrático de historia antigua de la Universidad de Oxford..."
                required
              />
            </div>
            <button type="submit" disabled={isCreatingAgent}>
              {isCreatingAgent ? 'Creando...' : 'Crear Agente'}
            </button>
            {createAgentError && <p className="error-message">{createAgentError}</p>}
            {createAgentSuccess && <p className="success-message">{createAgentSuccess}</p>}
          </form>
        </section>

        {/* --- Sección de Invocar Agente --- */}
        <section className="card">
          <h2>Interactuar con un Agente</h2>
          <form onSubmit={handleInvokeAgent} className="agent-form">
            <div className="form-group">
              <label htmlFor="selectAgent">Seleccionar Agente Existente:</label>
              <select
                id="selectAgent"
                value={selectedAgentId}
                onChange={(e) => {
                    setSelectedAgentId(e.target.value);
                    // Opcional: si se selecciona "Ninguno" o un agente, limpiar/actualizar el system prompt adhoc
                    if (e.target.value === "") { // si la opción "Ninguno" tiene value=""
                        // setAdhocSystemPrompt("Eres un asistente virtual útil y conciso."); // Resetear
                    } else {
                        // setAdhocSystemPrompt(""); // Limpiar para evitar confusión, o deshabilitarlo
                    }
                }}
                disabled={isLoadingAgents}
              >
                <option value="">-- Usar System Prompt Ad-hoc Abajo --</option>
                {agentsList.map(agent => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
              {isLoadingAgents && <p>Cargando agentes...</p>}
              {loadAgentsError && <p className="error-message">Error al cargar agentes: {loadAgentsError}</p>}
            </div>

            <div className="form-group">
              <label htmlFor="adhocSystemPrompt">System Prompt Ad-hoc (si no se selecciona agente):</label>
              <textarea
                id="adhocSystemPrompt"
                value={adhocSystemPrompt}
                onChange={(e) => setAdhocSystemPrompt(e.target.value)}
                rows="3"
                placeholder="Escribe aquí si no seleccionas un agente existente."
                disabled={!!selectedAgentId} // Deshabilitar si hay un agente seleccionado
              />
            </div>

            <div className="form-group">
              <label htmlFor="userPrompt">Tu Mensaje (User Prompt):</label>
              <textarea
                id="userPrompt"
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                rows="4"
                placeholder="Escribe tu pregunta o instrucción aquí..."
                required
              />
            </div>

            <button type="submit" disabled={isAgentInvoking}>
              {isAgentInvoking ? 'Enviando...' : 'Invocar Agente'}
            </button>
          </form>

          {isAgentInvoking && <p className="loading-message">Esperando respuesta del agente...</p>}
          {agentInvokeError && <p className="error-message">{agentInvokeError}</p>}
          {agentResponse && (
            <div className="agent-response-container">
              <h3>Respuesta del Agente:</h3>
              {usedSystemPromptInResponse && (
                <details className="used-prompt-details">
                    <summary>Ver System Prompt Usado</summary>
                    <pre className="system-prompt-display">{usedSystemPromptInResponse}</pre>
                </details>
              )}
              <pre className="agent-response-text">{agentResponse}</pre>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default App;