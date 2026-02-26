import React from 'react';
import { BrowserRouter, useLocation } from 'react-router-dom';
import AppRoutes from './Routes';
import Navbar from '../components/Navbar/Navbar';
import Footer from '../components/Footer/Footer';
import {
  LOGIN_ROUTE,
  REGISTER_ROUTE,
  AUTH_ROUTE,
  FORGOT_PASSWORD_ROUTE,
  RESET_PASSWORD_ROUTE,
} from './const';
import '../App.css';

const Layout = () => {
  const location = useLocation();

  const hideLayoutRoutes = [
    LOGIN_ROUTE,
    REGISTER_ROUTE,
    AUTH_ROUTE,
    FORGOT_PASSWORD_ROUTE,
    RESET_PASSWORD_ROUTE,
  ];

  const shouldHideLayout = hideLayoutRoutes.includes(location.pathname);

  return (
    <div className="App">
      {/* Навбар не показывается на страницах авторизации */}
      {!shouldHideLayout && <Navbar />}

      <div className="main-content">
        <AppRoutes />
      </div>

      {/* Футер тоже можно скрыть (опционально) */}
      {!shouldHideLayout && <Footer />}
    </div>
  );
};

const AppRouter = () => {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
};

export default AppRouter;
