import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { ChatInterface } from './components/ChatInterface';
import { DocumentManager } from './components/DocumentManager';
import { EvaluationDashboard } from './components/EvaluationDashboard';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'documents' | 'evaluation'>('chat');

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="flex-1">
        {activeTab === 'chat' && <ChatInterface />}
        {activeTab === 'documents' && <DocumentManager />}
        {activeTab === 'evaluation' && <EvaluationDashboard />}
      </main>
    </div>
  );
};

export default App;

