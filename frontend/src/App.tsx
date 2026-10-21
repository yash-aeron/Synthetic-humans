import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { ExperimentListPage } from './pages/ExperimentListPage';
import { NewExperimentPage } from './pages/NewExperimentPage';
import { ExperimentDetailPage } from './pages/ExperimentDetailPage';
import { UserListPage } from './pages/UserListPage';
import { UserDetailPage } from './pages/UserDetailPage';
import { ExperimentComparePage } from './pages/ExperimentComparePage';

export const App: React.FC = () => {
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/experiments" replace />} />
          <Route path="/experiments" element={<ExperimentListPage />} />
          <Route path="/experiments/new" element={<NewExperimentPage />} />
          <Route path="/experiments/:id" element={<ExperimentDetailPage />} />
          <Route path="/experiments/:id/users" element={<UserListPage />} />
          <Route path="/experiments/:id/users/:userId" element={<UserDetailPage />} />
          <Route path="/experiments/:id/compare" element={<ExperimentComparePage />} />
          <Route path="*" element={<Navigate to="/experiments" replace />} />
        </Routes>
      </main>
    </div>
  );
};
