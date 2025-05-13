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

  // --- Estados para Herramientas Disponibles ---
  const [availableSystemTools, setAvailableSystemTools] = useState([]);
  const [isLoadingSystemTools, setIsLoadingSystemTools] = useState(false);
  const [loadSystemToolsError, setLoadSystemToolsError] = useState(null);

  // --- Estados para la Invocación del Agente Individual ---
  const [selectedAgentIdForInvoke, setSelectedAgentIdForInvoke] = useState('');
  const [adhocSystemPrompt, setAdhocSystemPrompt] = useState('Eres un asistente virtual útil y conciso.');
  const [userPromptForAgent, setUserPromptForAgent] = useState('');
  const [agentInvokeResponse, setAgentInvokeResponse] = useState('');
  const [usedSystemPromptInAgentResponse, setUsedSystemPromptInAgentResponse] = useState('');
  const [isAgentInvoking, setIsAgentInvoking] = useState(false);
  const [agentInvokeError, setAgentInvokeError] = useState(null);

  // --- Estados para la Gestión de Agentes ---
  const [agentsList, setAgentsList] = useState([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [loadAgentsError, setLoadAgentsError] = useState(null);
  // Crear Agente
  const [newAgentName, setNewAgentName] = useState('');
  const [newAgentSystemPrompt, setNewAgentSystemPrompt] = useState('');
  const [newAgentEnabledTools, setNewAgentEnabledTools] = useState([]);
  const [isCreatingAgent, setIsCreatingAgent] = useState(false);
  const [createAgentError, setCreateAgentError] = useState(null);
  const [createAgentSuccess, setCreateAgentSuccess] = useState('');
  // Editar Agente
  const [isEditingAgent, setIsEditingAgent] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [editAgentName, setEditAgentName] = useState('');
  const [editAgentSystemPrompt, setEditAgentSystemPrompt] = useState('');
  const [editAgentEnabledTools, setEditAgentEnabledTools] = useState([]);
  const [isUpdatingAgent, setIsUpdatingAgent] = useState(false);
  const [updateAgentError, setUpdateAgentError] = useState(null);
  const [updateAgentSuccess, setUpdateAgentSuccess] = useState('');
  // Eliminar Agente
  const [isDeletingAgent, setIsDeletingAgent] = useState(false);
  const [deleteAgentError, setDeleteAgentError] = useState(null);
  const [deleteAgentSuccess, setDeleteAgentSuccess] = useState('');


  // --- Estados para la Gestión de Flujos ---
  const [flowsList, setFlowsList] = useState([]);
  const [isLoadingFlows, setIsLoadingFlows] = useState(false);
  const [loadFlowsError, setLoadFlowsError] = useState(null);
  // Crear Flujo
  const [newFlowName, setNewFlowName] = useState('');
  const [newFlowDescription, setNewFlowDescription] = useState('');
  const [newFlowAgentIds, setNewFlowAgentIds] = useState('');
  const [isCreatingFlow, setIsCreatingFlow] = useState(false);
  const [createFlowError, setCreateFlowError] = useState(null);
  const [createFlowSuccess, setCreateFlowSuccess] = useState('');
  // Editar Flujo
  const [isEditingFlow, setIsEditingFlow] = useState(false);
  const [editingFlow, setEditingFlow] = useState(null);
  const [editFlowName, setEditFlowName] = useState('');
  const [editFlowDescription, setEditFlowDescription] = useState('');
  const [editFlowAgentIds, setEditFlowAgentIds] = useState('');
  const [isUpdatingFlow, setIsUpdatingFlow] = useState(false);
  const [updateFlowError, setUpdateFlowError] = useState(null);
  const [updateFlowSuccess, setUpdateFlowSuccess] = useState('');
  // Eliminar Flujo
  const [isDeletingFlow, setIsDeletingFlow] = useState(false);
  const [deleteFlowError, setDeleteFlowError] = useState(null);
  const [deleteFlowSuccess, setDeleteFlowSuccess] = useState('');


  // --- Estados para la Invocación de Flujos ---
  const [selectedFlowIdForInvoke, setSelectedFlowIdForInvoke] = useState('');
  const [initialUserPromptForFlow, setInitialUserPromptForFlow] = useState('');
  const [flowInvokeResponse, setFlowInvokeResponse] = useState(null);
  const [isFlowInvoking, setIsFlowInvoking] = useState(false);
  const [flowInvokeError, setFlowInvokeError] = useState(null);


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
      setAgentsList([]);
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
          tools_enabled: newAgentEnabledTools,
        }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }
      const newAgent = await response.json();
      setCreateAgentSuccess(`¡Agente "${newAgent.name}" creado! ID: ${newAgent.id}`);
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

  const handleOpenEditAgentModal = (agent) => {
    setEditingAgent(agent);
    setEditAgentName(agent.name);
    setEditAgentSystemPrompt(agent.system_prompt);
    setEditAgentEnabledTools(agent.tools_enabled || []);
    setIsEditingAgent(true);
    setUpdateAgentError(null);
    setUpdateAgentSuccess('');
  };

  const handleCloseEditAgentModal = () => {
    setIsEditingAgent(false);
    setEditingAgent(null);
  };

  const handleUpdateAgent = async (event) => {
    event.preventDefault();
    if (!editingAgent) return;

    setIsUpdatingAgent(true);
    setUpdateAgentError(null);
    setUpdateAgentSuccess('');

    const agentDataToUpdate = {
        name: editAgentName,
        system_prompt: editAgentSystemPrompt,
        tools_enabled: editAgentEnabledTools,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/agents/${editingAgent.id}`, {
        method: 'PUT', // o 'PATCH' si tu backend lo soporta para actualizaciones parciales
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(agentDataToUpdate),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }
      const updatedAgent = await response.json();
      setUpdateAgentSuccess(`¡Agente "${updatedAgent.name}" actualizado!`);
      fetchAgentsList();
      handleCloseEditAgentModal();
    } catch (err) {
      console.error("Error al actualizar agente:", err);
      setUpdateAgentError(err.message);
    } finally {
      setIsUpdatingAgent(false);
    }
  };

  const handleDeleteAgent = async (agentId, agentName) => {
    if (window.confirm(`¿Estás seguro de que quieres eliminar el agente "${agentName}" (ID: ${agentId})?`)) {
      setIsDeletingAgent(true);
      setDeleteAgentError(null);
      setDeleteAgentSuccess('');
      try {
        const response = await fetch(`${API_BASE_URL}/agents/${agentId}`, { method: 'DELETE' });
        if (!response.ok) {
          // Si la respuesta no es 204 No Content, intenta parsear el error
          if (response.status !== 204) {
            const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
            throw new Error(errorData.detail || `Error HTTP: ${response.statusText}`);
          }
        }
        setDeleteAgentSuccess(`Agente "${agentName}" eliminado.`);
        fetchAgentsList();
         if (selectedAgentIdForInvoke === agentId) { // Deseleccionar si era el agente invocado
            setSelectedAgentIdForInvoke('');
        }
      } catch (err) {
        console.error("Error al eliminar agente:", err);
        setDeleteAgentError(err.message);
      } finally {
        setIsDeletingAgent(false);
      }
    }
  };
  
  const handleNewToolSelectionChange = (toolName) => {
    setNewAgentEnabledTools(prev => prev.includes(toolName) ? prev.filter(t => t !== toolName) : [...prev, toolName]);
  };

  const handleEditToolSelectionChange = (toolName) => {
    setEditAgentEnabledTools(prev => prev.includes(toolName) ? prev.filter(t => t !== toolName) : [...prev, toolName]);
  };


  const fetchAvailableSystemTools = async () => {
    setIsLoadingSystemTools(true);
    setLoadSystemToolsError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/tools/available`);
      if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
      const data = await response.json();
      setAvailableSystemTools(data.map(tool => tool.function));
    } catch (err) {
      console.error("Error al cargar herramientas del sistema:", err);
      setLoadSystemToolsError(err.message);
      setAvailableSystemTools([]);
    } finally {
      setIsLoadingSystemTools(false);
    }
  };

  const handleInvokeAgent = async (event) => {
    event.preventDefault();
    setIsAgentInvoking(true);
    setAgentInvokeResponse('');
    setUsedSystemPromptInAgentResponse('');
    setAgentInvokeError(null);

    let requestBody = { user_prompt: userPromptForAgent };
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
      fetchFlowsList();
    } catch (err) {
      console.error("Error al crear flujo:", err);
      setCreateFlowError(err.message);
    } finally {
      setIsCreatingFlow(false);
    }
  };

  const handleOpenEditFlowModal = (flow) => {
    setEditingFlow(flow);
    setEditFlowName(flow.name);
    setEditFlowDescription(flow.description || '');
    setEditFlowAgentIds(Array.isArray(flow.agent_ids) ? flow.agent_ids.join(', ') : '');
    setIsEditingFlow(true);
    setUpdateFlowError(null);
    setUpdateFlowSuccess('');
  };

  const handleCloseEditFlowModal = () => {
    setIsEditingFlow(false);
    setEditingFlow(null);
  };

  const handleUpdateFlow = async (event) => {
    event.preventDefault();
    if (!editingFlow) return;

    setIsUpdatingFlow(true);
    setUpdateFlowError(null);
    setUpdateFlowSuccess('');
    
    const agentIdsArray = editFlowAgentIds.split(',').map(id => id.trim()).filter(id => id);
    if (agentIdsArray.length === 0) {
        setUpdateFlowError("El flujo debe tener al menos un ID de agente.");
        setIsUpdatingFlow(false);
        return;
    }

    const flowDataToUpdate = {
        name: editFlowName,
        description: editFlowDescription,
        agent_ids: agentIdsArray,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/flows/${editingFlow.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(flowDataToUpdate),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }
      const updatedFlow = await response.json();
      setUpdateFlowSuccess(`¡Flujo "${updatedFlow.name}" actualizado!`);
      fetchFlowsList();
      handleCloseEditFlowModal();
    } catch (err) {
      console.error("Error al actualizar flujo:", err);
      setUpdateFlowError(err.message);
    } finally {
      setIsUpdatingFlow(false);
    }
  };

  const handleDeleteFlow = async (flowId, flowName) => {
    if (window.confirm(`¿Estás seguro de que quieres eliminar el flujo "${flowName}" (ID: ${flowId})?`)) {
      setIsDeletingFlow(true);
      setDeleteFlowError(null);
      setDeleteFlowSuccess('');
      try {
        const response = await fetch(`${API_BASE_URL}/flows/${flowId}`, { method: 'DELETE' });
        if (!response.ok) {
            if (response.status !== 204) {
                 const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
                throw new Error(errorData.detail || `Error HTTP: ${response.statusText}`);
            }
        }
        setDeleteFlowSuccess(`Flujo "${flowName}" eliminado.`);
        fetchFlowsList();
        if (selectedFlowIdForInvoke === flowId) {
            setSelectedFlowIdForInvoke('');
        }
      } catch (err) {
        console.error("Error al eliminar flujo:", err);
        setDeleteFlowError(err.message);
      } finally {
        setIsDeletingFlow(false);
      }
    }
  };


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
        body: JSON.stringify({ initial_user_prompt: initialUserPromptForFlow }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error HTTP: ${response.status}` }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }
      const data = await response.json();
      setFlowInvokeResponse(data);
    } catch (err) {
      console.error("Error al invocar flujo:", err);
      setFlowInvokeError(err.message);
    } finally {
      setIsFlowInvoking(false);
    }
  };

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
        <div className="config-column">
          {/* Crear Nuevo Agente */}
          <section className="card">
            <h2>Crear Nuevo Agente</h2>
            {createAgentSuccess && <p className="success-message">{createAgentSuccess}</p>}
            {createAgentError && <p className="error-message">{createAgentError}</p>}
            <form onSubmit={handleCreateAgent} className="agent-form">
              <div className="form-group">
                <label htmlFor="newAgentName">Nombre del Agente:</label>
                <input type="text" id="newAgentName" value={newAgentName} onChange={(e) => setNewAgentName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="newAgentSystemPrompt">System Prompt:</label>
                <textarea id="newAgentSystemPrompt" value={newAgentSystemPrompt} onChange={(e) => setNewAgentSystemPrompt(e.target.value)} rows="4" required />
              </div>
              <div className="form-group">
                <label>Habilitar Herramientas:</label>
                {isLoadingSystemTools ? <p>Cargando herramientas...</p> :
                 loadSystemToolsError ? <p className="error-message">Error: {loadSystemToolsError}</p> :
                 availableSystemTools.length === 0 ? <p>No hay herramientas disponibles.</p> : (
                  <div className="tools-selection-list">
                    {availableSystemTools.map(tool => (
                      <div key={`new-${tool.name}`} className="tool-checkbox-item">
                        <input type="checkbox" id={`new-tool-${tool.name}`} value={tool.name}
                               checked={newAgentEnabledTools.includes(tool.name)}
                               onChange={() => handleNewToolSelectionChange(tool.name)} />
                        <label htmlFor={`new-tool-${tool.name}`} title={tool.description}>{tool.name}</label>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button type="submit" disabled={isCreatingAgent}>{isCreatingAgent ? 'Creando...' : 'Crear Agente'}</button>
            </form>
          </section>

          {/* Listado de Agentes */}
          <section className="card">
            <h2>Agentes Existentes</h2>
            {deleteAgentSuccess && <p className="success-message">{deleteAgentSuccess}</p>}
            {deleteAgentError && <p className="error-message">{deleteAgentError}</p>}
            {isLoadingAgents ? <p>Cargando agentes...</p> :
             loadAgentsError ? <p className="error-message">Error: {loadAgentsError}</p> :
             agentsList.length === 0 ? <p>No hay agentes creados.</p> : (
                <ul className="entity-list">
                    {agentsList.map(agent => (
                    <li key={agent.id} className="entity-list-item">
                        <span><strong>{agent.name}</strong> (ID: <code>{agent.id.substring(0,8)}...</code>)</span>
                        <div>
                            <button className="button-edit" onClick={() => handleOpenEditAgentModal(agent)}>Editar</button>
                            <button className="button-delete" onClick={() => handleDeleteAgent(agent.id, agent.name)} disabled={isDeletingAgent}>
                                {isDeletingAgent ? 'Eliminando...' : 'Eliminar'}
                            </button>
                        </div>
                    </li>
                    ))}
                </ul>
            )}
          </section>


          {/* Crear Nuevo Flujo */}
          <section className="card">
            <h2>Crear Nuevo Flujo</h2>
            {createFlowSuccess && <p className="success-message">{createFlowSuccess}</p>}
            {createFlowError && <p className="error-message">{createFlowError}</p>}
            <form onSubmit={handleCreateFlow} className="agent-form">
              <div className="form-group">
                <label htmlFor="newFlowName">Nombre del Flujo:</label>
                <input type="text" id="newFlowName" value={newFlowName} onChange={(e) => setNewFlowName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="newFlowDescription">Descripción:</label>
                <textarea id="newFlowDescription" value={newFlowDescription} onChange={(e) => setNewFlowDescription(e.target.value)} rows="2" />
              </div>
              <div className="form-group">
                <label htmlFor="newFlowAgentIds">IDs de Agentes (separados por coma):</label>
                <input type="text" id="newFlowAgentIds" value={newFlowAgentIds} onChange={(e) => setNewFlowAgentIds(e.target.value)} placeholder="ej: id1,id2" required />
                {isLoadingAgents ? <p>Cargando agentes...</p> : (
                    <details className="agent-list-for-reference">
                        <summary>Ver IDs de Agentes ({agentsList.length})</summary>
                        {agentsList.length > 0 ? (
                            <ul>{agentsList.map(agent => <li key={agent.id}><strong>{agent.name}:</strong> <code>{agent.id}</code></li>)}</ul>
                        ) : <p>No hay agentes.</p>}
                    </details>
                )}
              </div>
              <button type="submit" disabled={isCreatingFlow}>{isCreatingFlow ? 'Creando...' : 'Crear Flujo'}</button>
            </form>
          </section>

          {/* Listado de Flujos */}
           <section className="card">
            <h2>Flujos Existentes</h2>
            {deleteFlowSuccess && <p className="success-message">{deleteFlowSuccess}</p>}
            {deleteFlowError && <p className="error-message">{deleteFlowError}</p>}
            {isLoadingFlows ? <p>Cargando flujos...</p> :
             loadFlowsError ? <p className="error-message">Error: {loadFlowsError}</p> :
             flowsList.length === 0 ? <p>No hay flujos creados.</p> : (
                <ul className="entity-list">
                    {flowsList.map(flow => (
                    <li key={flow.id} className="entity-list-item">
                        <span><strong>{flow.name}</strong> (ID: <code>{flow.id.substring(0,8)}...</code>)</span>
                        <div>
                            <button className="button-edit" onClick={() => handleOpenEditFlowModal(flow)}>Editar</button>
                            <button className="button-delete" onClick={() => handleDeleteFlow(flow.id, flow.name)} disabled={isDeletingFlow}>
                                {isDeletingFlow ? 'Eliminando...' : 'Eliminar'}
                            </button>
                        </div>
                    </li>
                    ))}
                </ul>
            )}
          </section>

        </div>

        {/* Columna de Invocación */}
        <div className="invoke-column">
            {/* Interactuar con Agente Individual */}
            <section className="card">
                <h2>Interactuar con Agente Individual</h2>
                 {agentInvokeError && <p className="error-message">{agentInvokeError}</p>}
                <form onSubmit={handleInvokeAgent} className="agent-form">
                <div className="form-group">
                    <label htmlFor="selectAgentForInvoke">Seleccionar Agente Existente:</label>
                    <select id="selectAgentForInvoke" value={selectedAgentIdForInvoke} onChange={(e) => setSelectedAgentIdForInvoke(e.target.value)} disabled={isLoadingAgents || agentsList.length === 0}>
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
                {agentInvokeResponse && (
                <div className="agent-response-container">
                    <h3>Respuesta del Agente Individual:</h3>
                    {usedSystemPromptInAgentResponse && (<details className="used-prompt-details"><summary>Ver System Prompt Usado</summary><pre className="system-prompt-display">{usedSystemPromptInAgentResponse}</pre></details>)}
                    <pre className="agent-response-text">{agentInvokeResponse}</pre>
                </div>
                )}
            </section>

            {/* Invocar Flujo Multiagente */}
            <section className="card">
                <h2>Invocar Flujo Multiagente</h2>
                {flowInvokeError && <p className="error-message">{flowInvokeError}</p>}
                <form onSubmit={handleInvokeFlow} className="agent-form">
                    <div className="form-group">
                        <label htmlFor="selectFlowForInvoke">Seleccionar Flujo Existente:</label>
                        <select 
                            id="selectFlowForInvoke" 
                            value={selectedFlowIdForInvoke} 
                            onChange={(e) => setSelectedFlowIdForInvoke(e.target.value)}
                            disabled={isLoadingFlows || flowsList.length === 0}
                        >
                            <option value="">-- Selecciona un Flujo --</option>
                            {flowsList.map(flow => (
                                <option key={flow.id} value={flow.id}>{flow.name}</option>
                            ))}
                        </select>
                        {isLoadingFlows && <p>Cargando flujos...</p>}
                        {loadFlowsError && <p className="error-message">Error: {loadFlowsError}</p>}
                    </div>
                    <div className="form-group">
                        <label htmlFor="initialUserPromptForFlow">Prompt Inicial para el Flujo:</label>
                        <textarea id="initialUserPromptForFlow" value={initialUserPromptForFlow}
                                onChange={(e) => setInitialUserPromptForFlow(e.target.value)}
                                rows="3" placeholder="Mensaje para el primer agente..." required
                                disabled={!selectedFlowIdForInvoke} />
                    </div>
                    <button type="submit" disabled={isFlowInvoking || !selectedFlowIdForInvoke}>
                        {isFlowInvoking ? 'Invocando Flujo...' : 'Invocar Flujo'}
                    </button>
                </form>
                {isFlowInvoking && <p className="loading-message">Ejecutando flujo...</p>}
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
                                        <p><strong>System Prompt:</strong></p><pre className="system-prompt-display small-text">{step.system_prompt_used}</pre>
                                        <p><strong>Entrada:</strong></p><pre className="prompt-display small-text">{step.input_prompt}</pre>
                                        <p><strong>Salida:</strong></p><pre className="prompt-display small-text">{step.output_response}</pre>
                                    </div>
                                </details>
                            ))}
                        </div>
                    </div>
                )}
            </section>
        </div>
      </div>

      {/* Modal de Edición de Agente */}
      {isEditingAgent && editingAgent && (
        <div className="modal-overlay">
          <div className="modal-content card">
            <h2>Editando Agente: {editingAgent.name}</h2>
            {updateAgentSuccess && <p className="success-message">{updateAgentSuccess}</p>}
            {updateAgentError && <p className="error-message">{updateAgentError}</p>}
            <form onSubmit={handleUpdateAgent} className="agent-form">
              <div className="form-group">
                <label htmlFor="editAgentName">Nombre del Agente:</label>
                <input type="text" id="editAgentName" value={editAgentName} onChange={(e) => setEditAgentName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="editAgentSystemPrompt">System Prompt:</label>
                <textarea id="editAgentSystemPrompt" value={editAgentSystemPrompt} onChange={(e) => setEditAgentSystemPrompt(e.target.value)} rows="4" required />
              </div>
              <div className="form-group">
                <label>Habilitar Herramientas:</label>
                 {isLoadingSystemTools ? <p>Cargando...</p> : (
                  <div className="tools-selection-list">
                    {availableSystemTools.map(tool => (
                      <div key={`edit-${tool.name}`} className="tool-checkbox-item">
                        <input type="checkbox" id={`edit-tool-${tool.name}`} value={tool.name}
                               checked={editAgentEnabledTools.includes(tool.name)}
                               onChange={() => handleEditToolSelectionChange(tool.name)} />
                        <label htmlFor={`edit-tool-${tool.name}`} title={tool.description}>{tool.name}</label>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="modal-actions">
                <button type="submit" disabled={isUpdatingAgent}>{isUpdatingAgent ? 'Guardando...' : 'Guardar Cambios'}</button>
                <button type="button" onClick={handleCloseEditAgentModal} disabled={isUpdatingAgent}>Cancelar</button>
              </div>
            </form>
          </div>
        </div>
      )}

    {/* Modal de Edición de Flujo */}
    {isEditingFlow && editingFlow && (
        <div className="modal-overlay">
            <div className="modal-content card">
                <h2>Editando Flujo: {editingFlow.name}</h2>
                {updateFlowSuccess && <p className="success-message">{updateFlowSuccess}</p>}
                {updateFlowError && <p className="error-message">{updateFlowError}</p>}
                <form onSubmit={handleUpdateFlow} className="agent-form">
                    <div className="form-group">
                        <label htmlFor="editFlowName">Nombre del Flujo:</label>
                        <input type="text" id="editFlowName" value={editFlowName} onChange={e => setEditFlowName(e.target.value)} required />
                    </div>
                    <div className="form-group">
                        <label htmlFor="editFlowDescription">Descripción:</label>
                        <textarea id="editFlowDescription" value={editFlowDescription} onChange={e => setEditFlowDescription(e.target.value)} rows="2" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="editFlowAgentIds">IDs de Agentes (separados por coma):</label>
                        <input type="text" id="editFlowAgentIds" value={editFlowAgentIds} onChange={e => setEditFlowAgentIds(e.target.value)} required />
                         {isLoadingAgents ? <p>Cargando agentes...</p> : (
                            <details className="agent-list-for-reference">
                                <summary>Ver IDs de Agentes ({agentsList.length})</summary>
                                {agentsList.length > 0 ? (
                                    <ul>{agentsList.map(agent => <li key={`ref-${agent.id}`}><strong>{agent.name}:</strong> <code>{agent.id}</code></li>)}</ul>
                                ) : <p>No hay agentes.</p>}
                            </details>
                        )}
                    </div>
                    <div className="modal-actions">
                        <button type="submit" disabled={isUpdatingFlow}>{isUpdatingFlow ? 'Guardando...' : 'Guardar Cambios'}</button>
                        <button type="button" onClick={handleCloseEditFlowModal} disabled={isUpdatingFlow}>Cancelar</button>
                    </div>
                </form>
            </div>
        </div>
    )}

    </div>
  );
}
export default App;