/**
 * Status Bar
 * 
 * Displays system health and document count.
 */
import React from 'react';
import { Database, Cpu, FileText } from 'lucide-react';

function StatusBar({ health, documentCount }) {
  const ollamaStatus = health?.ollama_available;
  
  return (
    <footer className="bg-gray-800 border-t border-gray-700 px-6 py-2">
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-6">
          {/* Ollama Status */}
          <div className="flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5" />
            <span>LLM:</span>
            <span className={`flex items-center gap-1 ${ollamaStatus ? 'text-green-400' : 'text-red-400'}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${ollamaStatus ? 'bg-green-400' : 'bg-red-400'}`} />
              {ollamaStatus ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Model Info */}
          {health?.available_models?.length > 0 && (
            <div className="flex items-center gap-2">
              <span>Model:</span>
              <span className="text-gray-400">{health.available_models[0]}</span>
            </div>
          )}

          {/* Document Count */}
          <div className="flex items-center gap-2">
            <FileText className="w-3.5 h-3.5" />
            <span>{documentCount} document{documentCount !== 1 ? 's' : ''}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Database className="w-3.5 h-3.5" />
          <span>ChromaDB + Ollama</span>
        </div>
      </div>
    </footer>
  );
}

export default StatusBar;
