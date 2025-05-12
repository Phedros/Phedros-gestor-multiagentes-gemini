// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';

// URLs de la API
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

function App() {
  // --- Estados para conexión raíz ---
  const [rootMessage, setRootMessage] = useState('');
  const [rootLoading, setRootLoading] = useState(true);
  const [rootError, setRootError] = useState(null);

  // --- NUEVO: Estados para Herramientas Disponibles ---
  const [availableSystemTools, setAvailableSystemTools] = useState([]);
  const [isLoadingSystemTools, setIsLoadingSystemTools] = useState(false);
  const [loadSystemToolsError, setLoadSystemToolsError] = useState(null);

  // --- Estados para la Invocación del Agente Individual ---
  const [selectedAgentIdForInvoke, setSelectedAgentIdForInvoke] = useState('');
  const [adhocSystemPrompt, setAdhocSystemPrompt] = useState('Eres un asistente virtual útil y conciso.');
  const [userPromptForAgent, setUserPromptForAgent] = useState(''); // Renombrado para claridad
  const [agentInvokeResponse, setAgentInvokeResponse] = useState(''); // Renombrado para claridad
  const [usedSystemPromptInAgentResponse, setUsedSystemPromptInAgentResponse] = useState('');
  const [isAgentInvoking, setIsAgentInvoking] = useState(false);
  const [agentInvokeError, setAgentInvokeError] = useState(null);

  // --- Estados para la Gestión de Agentes ---
  const [agentsList, setAgentsList] = useState([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [loadAgentsError, setLoadAgentsError] = useState(null);
  const [newAgentName, setNewAgentName] = useState('');
  const [newAgentSystemPrompt, setNewAgentSystemPrompt] = useState('');
  const [newAgentEnabledTools, setNewAgentEnabledTools] = useState([]); // NUEVO: array de strings (nombres de herramientas seleccionadas)
  const [isCreatingAgent, setIsCreatingAgent] = useState(false);
  const [createAgentError, setCreateAgentError] = useState(null);
  const [createAgentSuccess, setCreateAgentSuccess] = useState('');

  // --- NUEVO: Estados para la Gestión de Flujos ---
  const [flowsList, setFlowsList] = useState([]);
  const [isLoadingFlows, setIsLoadingFlows] = useState(false);
  const [loadFlowsError, setLoadFlowsError] = useState(null);
  const [newFlowName, setNewFlowName] = useState('');
  const [newFlowDescription, setNewFlowDescription] = useState('');
  const [newFlowAgentIds, setNewFlowAgentIds] = useState(''); // IDs separados por comas por ahora
  const [isCreatingFlow, setIsCreatingFlow] = useState(false);
  const [createFlowError, setCreateFlowError] = useState(null);
  const [createFlowSuccess, setCreateFlowSuccess] = useState('');

  // --- NUEVO: Estados para la Invocación de Flujos ---
  const [selectedFlowIdForInvoke, setSelectedFlowIdForInvoke] = useState('');
  const [initialUserPromptForFlow, setInitialUserPromptForFlow] = useState('');
  const [flowInvokeResponse, setFlowInvokeResponse] = useState(null); // Almacenará el objeto completo de respuesta del flujo
  const [isFlowInvoking, setIsFlowInvoking] = useState(false);
  const [flowInvokeError, setFlowInvokeError] = useState(null);




  // --- Efecto para cargar datos iniciales ---
  useEffect(() => {
    fetch('http://127.0.0.1:8000/')
      .then(response => {
        if (!response.ok) throw new Error(`Error HTTP raíz: ${response.status}`);
        return response.json();
      })
      .then(data => setRootMessage(data.message))
      .catch(err => setRootError(err.message))
      .finally(() => setRootLoading(false));

    fetchAgentsList();
    fetchFlowsList();
    fetchAvailableSystemTools();
  }, []);

  // --- Funciones para Gestión de Agentes (sin cambios significativos) ---
  const fetchAgentsList = async () => { /* ... (código existente sin cambios) ... */
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
      setAgentsList([]);
    } finally {
      setIsLoadingAgents(false);
    }
  };

  const handleCreateAgent = async (event) => { /* ... (código existente sin cambios) ... */
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
          tools_enabled: newAgentEnabledTools,
        }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }
      const newAgent = await response.json();
      setCreateAgentSuccess(`¡Agente "${newAgent.name}" creado!`);
      setNewAgentName('');
      setNewAgentSystemPrompt('');
      setNewAgentEnabledTools([]);
      fetchAgentsList();
    } catch (err) {
      console.error("Error al crear agente:", err);
      setCreateAgentError(err.message);
    } finally {
      setIsCreatingAgent(false);
    }
  };

  // --- NUEVO: Handler para cambiar la selección de herramientas ---
  const handleToolSelectionChange = (toolName) => {
    setNewAgentEnabledTools(prevSelectedTools => {
      if (prevSelectedTools.includes(toolName)) {
        return prevSelectedTools.filter(t => t !== toolName); // Deseleccionar
      } else {
        return [...prevSelectedTools, toolName]; // Seleccionar
      }
    });
  };

  // --- NUEVO: Función para Cargar Herramientas Disponibles ---
  const fetchAvailableSystemTools = async () => {
    setIsLoadingSystemTools(true);
    setLoadSystemToolsError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/tools/available`);
      if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
      const data = await response.json();
      // Guardamos solo la parte 'function' que tiene name, description, parameters
      setAvailableSystemTools(data.map(tool => tool.function));
    } catch (err) {
      console.error("Error al cargar herramientas del sistema:", err);
      setLoadSystemToolsError(err.message);
      setAvailableSystemTools([]);
    } finally {
      setIsLoadingSystemTools(false);
    }
  };

  // --- Función para Invocar Agente Individual (sin cambios significativos, solo renombrado de estados) ---
  const handleInvokeAgent = async (event) => { /* ... (código existente con estados renombrados) ... */
    event.preventDefault();
    setIsAgentInvoking(true);
    setAgentInvokeResponse('');
    setUsedSystemPromptInAgentResponse('');
    setAgentInvokeError(null);

    let requestBody = {
      user_prompt: userPromptForAgent,
    };

    if (selectedAgentIdForInvoke) {
      requestBody.agent_id = selectedAgentIdForInvoke;
    } else {
      requestBody.system_prompt = adhocSystemPrompt;
    }
    
    if (!userPromptForAgent.trim()) {
        setAgentInvokeError("El 'User Prompt' no puede estar vacío.");
        setIsAgentInvoking(false);
        return;
    }
    if (!selectedAgentIdForInvoke && !adhocSystemPrompt.trim()) {
        setAgentInvokeError("Debes seleccionar un agente o proveer un 'System Prompt Ad-hoc'.");
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
      setAgentInvokeResponse(data.agent_response);
      setUsedSystemPromptInAgentResponse(data.used_system_prompt);
    } catch (err) {
      console.error("Error al invocar al agente:", err);
      setAgentInvokeError(err.message);
    } finally {
      setIsAgentInvoking(false);
    }
  };

  // --- NUEVO: Funciones para Gestión de Flujos ---
  const fetchFlowsList = async () => {
    setIsLoadingFlows(true);
    setLoadFlowsError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/flows`);
      if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
      const data = await response.json();
      setFlowsList(data);
    } catch (err) {
      console.error("Error al cargar flujos:", err);
      setLoadFlowsError(err.message);
      setFlowsList([]);
    } finally {
      setIsLoadingFlows(false);
    }
  };

  const handleCreateFlow = async (event) => {
    event.preventDefault();
    setIsCreatingFlow(true);
    setCreateFlowError(null);
    setCreateFlowSuccess('');

    const agentIdsArray = newFlowAgentIds.split(',').map(id => id.trim()).filter(id => id);
    if (agentIdsArray.length === 0) {
        setCreateFlowError("Debes especificar al menos un ID de agente para el flujo.");
        setIsCreatingFlow(false);
        return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/flows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newFlowName,
          description: newFlowDescription,
          agent_ids: agentIdsArray,
        }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }
      const newFlow = await response.json();
      setCreateFlowSuccess(`¡Flujo "${newFlow.name}" creado!`);
      setNewFlowName('');
      setNewFlowDescription('');
      setNewFlowAgentIds('');
      fetchFlowsList(); // Recargar la lista de flujos
    } catch (err) {
      console.error("Error al crear flujo:", err);
      setCreateFlowError(err.message);
    } finally {
      setIsCreatingFlow(false);
    }
  };

  // --- NUEVO: Función para Invocar Flujo ---
  const handleInvokeFlow = async (event) => {
    event.preventDefault();
    if (!selectedFlowIdForInvoke) {
        setFlowInvokeError("Por favor, selecciona un flujo para invocar.");
        return;
    }
    if (!initialUserPromptForFlow.trim()) {
        setFlowInvokeError("El 'Prompt Inicial para el Flujo' no puede estar vacío.");
        return;
    }

    setIsFlowInvoking(true);
    setFlowInvokeResponse(null);
    setFlowInvokeError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/flows/${selectedFlowIdForInvoke}/invoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          initial_user_prompt: initialUserPromptForFlow,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }
      const data = await response.json();
      setFlowInvokeResponse(data); // Guardar el objeto completo con final_output y log
    } catch (err) {
      console.error("Error al invocar flujo:", err);
      setFlowInvokeError(err.message);
    } finally {
      setIsFlowInvoking(false);
    }
  };


  // --- Renderizado ---
  if (rootLoading) {
    return <div className="App-header"><h1>Cargando conexión con el backend...</h1></div>;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Gestor Multiagentes Avanzado</h1>
        {rootError ? (
          <p style={{ color: 'orange' }}>{rootError}</p>
        ) : (
          <p style={{ color: 'lightgreen', fontSize: 'small' }}>{rootMessage}</p>
        )}
      </header>

      <div className="main-layout">
        {/* --- Columna de Configuración (Agentes y Flujos) --- */}
        <div className="config-column">
          <section className="card">
            <h2>Crear Nuevo Agente</h2>
            <form onSubmit={handleCreateAgent} className="agent-form">
              {/* ... (Formulario de Crear Agente existente sin cambios) ... */}
              <div className="form-group">
                <label htmlFor="newAgentName">Nombre del Agente:</label>
                <input type="text" id="newAgentName" value={newAgentName} onChange={(e) => setNewAgentName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="newAgentSystemPrompt">System Prompt del Nuevo Agente:</label>
                <textarea id="newAgentSystemPrompt" value={newAgentSystemPrompt} onChange={(e) => setNewAgentSystemPrompt(e.target.value)} rows="4" required />
              </div>
              <div className="form-group">
                <label>Habilitar Herramientas para este Agente:</label>
                {isLoadingSystemTools ? <p>Cargando herramientas...</p> :
                 loadSystemToolsError ? <p className="error-message">Error al cargar herramientas: {loadSystemToolsError}</p> :
                 availableSystemTools.length === 0 ? <p>No hay herramientas disponibles en el sistema.</p> : (
                  <div className="tools-selection-list">
                    {availableSystemTools.map(tool => (
                      <div key={tool.name} className="tool-checkbox-item">
                        <input
                          type="checkbox"
                          id={`tool-${tool.name}`}
                          value={tool.name}
                          checked={newAgentEnabledTools.includes(tool.name)}
                          onChange={() => handleToolSelectionChange(tool.name)}
                        />
                        <label htmlFor={`tool-${tool.name}`} title={tool.description}>
                          {tool.name}
                        </label>
                        {/* Podríamos mostrar la descripción de la herramienta aquí también si quisiéramos */}
                         {/* <p className="tool-description-small">{tool.description}</p> */}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button type="submit" disabled={isCreatingAgent}>{isCreatingAgent ? 'Creando...' : 'Crear Agente'}</button>
              {createAgentError && <p className="error-message">{createAgentError}</p>}
              {createAgentSuccess && <p className="success-message">{createAgentSuccess}</p>}
            </form>
          </section>

          {/* NUEVO: Sección Crear Nuevo Flujo */}
          <section className="card">
            <h2>Crear Nuevo Flujo</h2>
            <form onSubmit={handleCreateFlow} className="agent-form">
              <div className="form-group">
                <label htmlFor="newFlowName">Nombre del Flujo:</label>
                <input type="text" id="newFlowName" value={newFlowName} onChange={(e) => setNewFlowName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="newFlowDescription">Descripción del Flujo (opcional):</label>
                <textarea id="newFlowDescription" value={newFlowDescription} onChange={(e) => setNewFlowDescription(e.target.value)} rows="2" />
              </div>
              <div className="form-group">
                <label htmlFor="newFlowAgentIds">IDs de Agentes en Secuencia (separados por coma):</label>
                <input type="text" id="newFlowAgentIds" value={newFlowAgentIds} onChange={(e) => setNewFlowAgentIds(e.target.value)} placeholder="ej: id_agente1,id_agente2" required />
                {isLoadingAgents ? <p>Cargando lista de agentes para referencia...</p> : (
                    <details className="agent-list-for-reference">
                        <summary>Ver IDs de Agentes Disponibles ({agentsList.length})</summary>
                        {agentsList.length > 0 ? (
                            <ul>{agentsList.map(agent => <li key={agent.id}><strong>{agent.name}:</strong> <code>{agent.id}</code></li>)}</ul>
                        ) : <p>No hay agentes creados.</p>}
                    </details>
                )}
              </div>
              <button type="submit" disabled={isCreatingFlow}>{isCreatingFlow ? 'Creando Flujo...' : 'Crear Flujo'}</button>
              {createFlowError && <p className="error-message">{createFlowError}</p>}
              {createFlowSuccess && <p className="success-message">{createFlowSuccess}</p>}
            </form>
          </section>
        </div>

        {/* --- Columna de Invocación (Agente Individual y Flujos) --- */}
        <div className="invoke-column">
          <section className="card">
            <h2>Interactuar con Agente Individual</h2>
            <form onSubmit={handleInvokeAgent} className="agent-form">
              {/* ... (Formulario de Invocar Agente Individual existente, usa selectedAgentIdForInvoke y userPromptForAgent) ... */}
              <div className="form-group">
                <label htmlFor="selectAgentForInvoke">Seleccionar Agente Existente:</label>
                <select id="selectAgentForInvoke" value={selectedAgentIdForInvoke} onChange={(e) => setSelectedAgentIdForInvoke(e.target.value)} disabled={isLoadingAgents}>
                  <option value="">-- Usar System Prompt Ad-hoc --</option>
                  {agentsList.map(agent => (<option key={agent.id} value={agent.id}>{agent.name}</option>))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="adhocSystemPrompt">System Prompt Ad-hoc (si no se selecciona agente):</label>
                <textarea id="adhocSystemPrompt" value={adhocSystemPrompt} onChange={(e) => setAdhocSystemPrompt(e.target.value)} rows="3" disabled={!!selectedAgentIdForInvoke} />
              </div>
              <div className="form-group">
                <label htmlFor="userPromptForAgent">Tu Mensaje (User Prompt):</label>
                <textarea id="userPromptForAgent" value={userPromptForAgent} onChange={(e) => setUserPromptForAgent(e.target.value)} rows="4" required />
              </div>
              <button type="submit" disabled={isAgentInvoking}>{isAgentInvoking ? 'Enviando...' : 'Invocar Agente'}</button>
            </form>
            {isAgentInvoking && <p className="loading-message">Esperando respuesta del agente...</p>}
            {agentInvokeError && <p className="error-message">{agentInvokeError}</p>}
            {agentInvokeResponse && (
              <div className="agent-response-container">
                <h3>Respuesta del Agente Individual:</h3>
                {usedSystemPromptInAgentResponse && (<details className="used-prompt-details"><summary>Ver System Prompt Usado</summary><pre className="system-prompt-display">{usedSystemPromptInAgentResponse}</pre></details>)}
                <pre className="agent-response-text">{agentInvokeResponse}</pre>
              </div>
            )}
          </section>

          {/* NUEVO: Sección Invocar Flujo */}
          <section className="card">
            <h2>Invocar Flujo Multiagente</h2>
            <form onSubmit={handleInvokeFlow} className="agent-form">
                <div className="form-group">
                    <label htmlFor="selectFlowForInvoke">Seleccionar Flujo Existente:</label>
                    <select 
                        id="selectFlowForInvoke" 
                        value={selectedFlowIdForInvoke} 
                        onChange={(e) => setSelectedFlowIdForInvoke(e.target.value)}
                        disabled={isLoadingFlows}
                    >
                        <option value="">-- Selecciona un Flujo --</option>
                        {flowsList.map(flow => (
                            <option key={flow.id} value={flow.id}>
                                {flow.name}
                            </option>
                        ))}
                    </select>
                    {isLoadingFlows && <p>Cargando flujos...</p>}
                    {loadFlowsError && <p className="error-message">Error al cargar flujos: {loadFlowsError}</p>}
                </div>
                <div className="form-group">
                    <label htmlFor="initialUserPromptForFlow">Prompt Inicial para el Flujo:</label>
                    <textarea 
                        id="initialUserPromptForFlow"
                        value={initialUserPromptForFlow}
                        onChange={(e) => setInitialUserPromptForFlow(e.target.value)}
                        rows="3"
                        placeholder="El mensaje para el primer agente del flujo..."
                        required
                        disabled={!selectedFlowIdForInvoke}
                    />
                </div>
                <button type="submit" disabled={isFlowInvoking || !selectedFlowIdForInvoke}>
                    {isFlowInvoking ? 'Invocando Flujo...' : 'Invocar Flujo'}
                </button>
            </form>
            {isFlowInvoking && <p className="loading-message">Ejecutando flujo, esto puede tardar...</p>}
            {flowInvokeError && <p className="error-message">{flowInvokeError}</p>}
            {flowInvokeResponse && (
                <div className="flow-response-container">
                    <h3>Resultado del Flujo: "{flowInvokeResponse.flow_name}"</h3>
                    <h4>Salida Final:</h4>
                    <pre className="agent-response-text">{flowInvokeResponse.final_output}</pre>
                    <h4>Log de Ejecución:</h4>
                    <div className="flow-log">
                        {flowInvokeResponse.log.map((step, index) => (
                            <details key={index} className="flow-log-step">
                                <summary>Paso {index + 1}: Agente "{step.agent_name}" (ID: {step.agent_id.substring(0,8)}...)</summary>
                                <div className="log-step-content">
                                    <p><strong>System Prompt Usado:</strong></p>
                                    <pre className="system-prompt-display small-text">{step.system_prompt_used}</pre>
                                    <p><strong>Entrada (User Prompt):</strong></p>
                                    <pre className="prompt-display small-text">{step.input_prompt}</pre>
                                    <p><strong>Salida (Respuesta del Agente):</strong></p>
                                    <pre className="prompt-display small-text">{step.output_response}</pre>
                                </div>
                            </details>
                        ))}
                    </div>
                </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
export default App;