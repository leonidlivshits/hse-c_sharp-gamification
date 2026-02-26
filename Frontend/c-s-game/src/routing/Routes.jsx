import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';

import Home from '../pages/HomePage/HomePage';
import Materials from '../pages/Materials/Materials';
import Tests from '../pages/Tests/Tests';
import PersonalAccount from '../pages/PersonalAccount/PersonalAccount';
import NoPage from '../pages/NoPage/NoPage';
import MaterialDetails from '../pages/Materials/MaterialsDetails';
import Analytics from '../pages/PersonalAccount/Analytics';
import TestDetails from '../pages/Tests/TestDetails';
import Auth from '../pages/Authorisation/Authorisation';
import Login from '../pages/Authorisation/Login';
import Register from '../pages/Authorisation/Register';
import ForgotPassword from '../pages/Authorisation/ForgotPassword';
import ResetPassword from '../pages/Authorisation/ResetPassword';

import {
  MAIN_ROUTE,
  MATERIALS_ROUTE,
  TESTS_ROUTE,
  PERSONAL_ACCOUNT_ROUTE,
  NO_PAGE_ROUTE,
  MATERIAL_DETAILS_ROUTE,
  ANALYTICS_ROUTE,
  TEST_DETAILS_ROUTE,
  AUTH_ROUTE,
  LOGIN_ROUTE,
  REGISTER_ROUTE,
  FORGOT_PASSWORD_ROUTE,
  RESET_PASSWORD_ROUTE,
} from './const.js';

const ProtectedRoute = ({ children }) => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';

  if (!isAuthenticated) {
    return <Navigate to={LOGIN_ROUTE} replace />;
  }

  return children;
};

const PublicRoute = ({ children }) => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';

  if (isAuthenticated) {
    return <Navigate to={MAIN_ROUTE} replace />;
  }

  return children;
};

const AppRoutes = () => {
  const location = useLocation();

  return (
    <Routes location={location}>
      <Route
        path={LOGIN_ROUTE}
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path={REGISTER_ROUTE}
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />
      <Route
        path={AUTH_ROUTE}
        element={
          <PublicRoute>
            <Auth />
          </PublicRoute>
        }
      />
      <Route
        path={FORGOT_PASSWORD_ROUTE}
        element={
          <PublicRoute>
            <ForgotPassword />
          </PublicRoute>
        }
      />
      <Route
        path={RESET_PASSWORD_ROUTE}
        element={
          <PublicRoute>
            <ResetPassword />
          </PublicRoute>
        }
      />
      <Route path={NO_PAGE_ROUTE} element={<NoPage />} />

      <Route
        path={MAIN_ROUTE}
        element={
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        }
      />
      <Route
        path={MATERIALS_ROUTE}
        element={
          <ProtectedRoute>
            <Materials />
          </ProtectedRoute>
        }
      />
      <Route
        path={TESTS_ROUTE}
        element={
          <ProtectedRoute>
            <Tests />
          </ProtectedRoute>
        }
      />
      <Route
        path={PERSONAL_ACCOUNT_ROUTE}
        element={
          <ProtectedRoute>
            <PersonalAccount />
          </ProtectedRoute>
        }
      />
      <Route
        path={ANALYTICS_ROUTE}
        element={
          <ProtectedRoute>
            <Analytics />
          </ProtectedRoute>
        }
      />
      <Route
        path={TEST_DETAILS_ROUTE}
        element={
          <ProtectedRoute>
            <TestDetails />
          </ProtectedRoute>
        }
      />
      <Route
        path={MATERIAL_DETAILS_ROUTE}
        element={
          <ProtectedRoute>
            <MaterialDetails />
          </ProtectedRoute>
        }
      />

      <Route
        path="/"
        element={
          <Navigate
            to={localStorage.getItem('isAuthenticated') === 'true' ? MAIN_ROUTE : LOGIN_ROUTE}
            replace
          />
        }
      />

      <Route path="*" element={<Navigate to={NO_PAGE_ROUTE} replace />} />
    </Routes>
  );
};

export default AppRoutes;
