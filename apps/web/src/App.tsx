import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LandingPage } from './pages/LandingPage';
import { ContactPage } from './pages/ContactPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterCompanyPage } from './pages/RegisterCompanyPage';
import { RegisterCandidatePage } from './pages/RegisterCandidatePage';
import { DashboardPage } from './pages/DashboardPage';
import { SuperAdminPage } from './pages/SuperAdminPage';
import { AssessmentsListPage } from './pages/AssessmentsListPage';
import { AssessmentBuilderPage } from './pages/AssessmentBuilderPage';
import { QuestionBanksPage } from './pages/QuestionBanksPage';
import { AssessmentResultsPage } from './pages/AssessmentResultsPage';
import { ExamRunnerPage } from './pages/ExamRunnerPage';
import { CodingProblemsPage } from './pages/CodingProblemsPage';
import { SqlProblemsPage } from './pages/SqlProblemsPage';
import { AssessmentCopilotPage } from './pages/AssessmentCopilotPage';
import { AnalyticsDashboardPage } from './pages/AnalyticsDashboardPage';
import { CompanyPortalPage } from './pages/CompanyPortalPage';

const RootRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return null;
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LandingPage />;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
          <Navbar />
          <main style={{ flex: 1, paddingBottom: '3rem' }}>
            <Routes>
              {/* Public & Landing Routes */}
              <Route path="/" element={<RootRoute />} />
              <Route path="/contact" element={<ContactPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register-company" element={<RegisterCompanyPage />} />
              <Route path="/register-candidate" element={<RegisterCandidatePage />} />

              {/* Public / Token Exam Runner for Candidates */}
              <Route path="/exam/:token" element={<ExamRunnerPage />} />

              {/* Protected Workspace & Candidate Dashboard */}
              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/company/settings" element={<CompanyPortalPage />} />
                <Route path="/company/portal" element={<CompanyPortalPage />} />
                <Route path="/company/integrations" element={<CompanyPortalPage />} />
                <Route path="/assessments" element={<AssessmentsListPage />} />
                <Route path="/assessments/:id" element={<AssessmentBuilderPage />} />
                <Route path="/assessments/:id/results" element={<AssessmentResultsPage />} />
                <Route path="/questions" element={<QuestionBanksPage />} />
                <Route path="/coding" element={<CodingProblemsPage />} />
                <Route path="/sql" element={<SqlProblemsPage />} />
                <Route path="/copilot" element={<AssessmentCopilotPage />} />
                <Route path="/analytics" element={<AnalyticsDashboardPage />} />
              </Route>

              {/* Super Admin Platform Control */}
              <Route element={<ProtectedRoute allowedRoles={['SUPER_ADMIN']} />}>
                <Route path="/superadmin" element={<SuperAdminPage />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
};
