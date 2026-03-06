import React from 'react';
import { Link } from 'react-router-dom';
import './ChangePassword.css';

const ChangePassword = () => {
  return (
    <div className="change-password-container">
      <div className="change-password-card">
        <h1>Смена пароля</h1>
        <p>Эта страница находится в разработке. Скоро здесь будет форма для смены пароля.</p>
        <Link to="/personal-account" className="back-link">
          Вернуться в личный кабинет
        </Link>
      </div>
    </div>
  );
};

export default ChangePassword;
