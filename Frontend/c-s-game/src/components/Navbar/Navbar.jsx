import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  MAIN_ROUTE,
  MATERIALS_ROUTE,
  TESTS_ROUTE,
  PERSONAL_ACCOUNT_ROUTE,
} from '../../routing/const';
import './Navbar.css';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const NAV_ITEMS = [
    { path: MAIN_ROUTE, label: 'Главная' },
    { path: MATERIALS_ROUTE, label: 'Материалы' },
    { path: TESTS_ROUTE, label: 'Тесты' },
    { path: PERSONAL_ACCOUNT_ROUTE, label: 'Личный кабинет' },
  ];

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="Navbar">
      <div className="nav-container">
        <NavLink to="/" className="nav-brand">
          <div className="bank-logo">Т</div>
          <span>Т-Образование</span>
        </NavLink>

        <button className="mobile-menu-btn" onClick={toggleMenu}>
          {isMenuOpen ? '✕' : '☰'}
        </button>

        <div className={`nav-links ${isMenuOpen ? 'open' : ''}`}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
              onClick={() => setIsMenuOpen(false)}
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>

        <div className="nav-user">
          <div className="user-avatar">Д</div>
          <span className="user-name">Дмитрий</span>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
