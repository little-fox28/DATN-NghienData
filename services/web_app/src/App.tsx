import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AppProvider } from './contexts/AppProvider';
import { MainLayout } from './layouts/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { LoanApplicationPage } from './pages/LoanApplicationPage';

export const App: React.FC = () => {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="apply" element={<LoanApplicationPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
};
