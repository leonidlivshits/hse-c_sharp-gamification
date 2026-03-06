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
import ChangePassword from '../components/ChangePassword/ChangePassword'; // страница смены пароля (заглушка)
import EditProfile from '../components/EditProfile/EditProfile'; // страница редактирования профиля

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
  CHANGE_PASSWORD_ROUTE,
  EDIT_PROFILE_ROUTE,
} from './const.js';

// Проверка авторизации (используем localStorage)
const isAuthenticated = () => localStorage.getItem('isAuthenticated') === 'true';

const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to={LOGIN_ROUTE} replace />;
  }
  return children;
};

const PublicRoute = ({ children }) => {
  if (isAuthenticated()) {
    return <Navigate to={MAIN_ROUTE} replace />;
  }
  return children;
};

const AppRoutes = () => {
  const location = useLocation();

  return (
    <Routes location={location}>
      {/* Публичные маршруты (доступны без авторизации) */}
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

      {/* Защищенные маршруты (только для авторизованных) */}
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

      {/* Страница смены пароля */}
      <Route
        path={CHANGE_PASSWORD_ROUTE}
        element={
          <ProtectedRoute>
            <ChangePassword />
          </ProtectedRoute>
        }
      />

      {/* Страница редактирования профиля */}
      <Route
        path={EDIT_PROFILE_ROUTE}
        element={
          <ProtectedRoute>
            <EditProfile />
          </ProtectedRoute>
        }
      />

      {/* Перенаправление корневого пути */}
      <Route
        path="/"
        element={<Navigate to={isAuthenticated() ? MAIN_ROUTE : LOGIN_ROUTE} replace />}
      />

      {/* Перенаправление для неизвестных маршрутов */}
      <Route path="*" element={<Navigate to={NO_PAGE_ROUTE} replace />} />
    </Routes>
  );
};

export default AppRoutes;
