import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import AppRoutes from './Routes';
import Navbar from '../components/Navbar/Navbar';
import Footer from '../components/Footer/Footer';
import '../App.css';

const AppRouter = () => {
  return (
    <BrowserRouter>
      <div className="App">
        <Navbar />
        <div className="main-content">
          <AppRoutes />
        </div>
        <Footer />
      </div>
    </BrowserRouter>
  );
};

export default AppRouter;