/**
 * RAG Document Assistant
 * 
 * Main application component with document management and chat interface.
 */
import React, { useState, useEffect } from 'react';
import DocumentPanel from './components/DocumentPanel';
import ChatPanel from './components/ChatPanel';
import StatusBar from './components/StatusBar';
import { checkHealth } from './services/api';

function App() {
  const [health, setHealth] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [activePanel, setActivePanel] = useState('chat');

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: 'error', ollama_available: false }));
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-white">RAG Document Assistant</h1>
          <div className="flex items-center gap-4">
            {/* Panel Toggle */}
            <div className="flex bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setActivePanel('chat')}
                className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
                  activePanel === 'chat'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setActivePanel('documents')}
                className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
                  activePanel === 'documents'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Documents
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {activePanel === 'chat' ? (
          <ChatPanel documents={documents} />
        ) : (
          <DocumentPanel documents={documents} setDocuments={setDocuments} />
        )}
      </main>

      {/* Status Bar */}
      <StatusBar health={health} documentCount={documents.length} />
    </div>
  );
}

export default App;
