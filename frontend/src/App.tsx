import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard/Dashboard';
import { ErrorList } from './pages/Errors/ErrorList';
import { AgentControl } from './pages/Agent/AgentControl';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/errors" element={<ErrorList />} />
          <Route path="/fixes" element={<div className="text-center py-12 text-gray-500">Fixes page coming soon...</div>} />
          <Route path="/agent" element={<AgentControl />} />
          <Route path="/audit" element={<div className="text-center py-12 text-gray-500">Audit log page coming soon...</div>} />
          <Route path="/settings" element={<div className="text-center py-12 text-gray-500">Settings page coming soon...</div>} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
