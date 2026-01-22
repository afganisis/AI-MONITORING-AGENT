import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Control } from './pages/Control/Control';
import { Activity } from './pages/Activity/Activity';
import { Results } from './pages/Results/Results';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Control />} />
          <Route path="/activity" element={<Activity />} />
          <Route path="/results" element={<Results />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
