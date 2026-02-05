import React from 'react';
import { BrowserRouter, useLocation } from 'react-router-dom';
import AppRoutes from './Routes';
import Navbar from '../components/Navbar/Navbar';
import Footer from '../components/Footer/Footer';
import '../App.css';

const Layout = () => {
  const location = useLocation();
  
  const hideFooterRoutes = ['/login', '/register', '/auth', '/forgot-password', '/reset-password'];
  const shouldHideFooter = hideFooterRoutes.includes(location.pathname);

  return (
    <div className="App">
      <Navbar />
      <div className="main-content">
        <AppRoutes />
      </div>
      {!shouldHideFooter && <Footer />}
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