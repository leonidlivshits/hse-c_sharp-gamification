import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './PersonalAccount.css';

const PersonalAccount = () => {
  const [userData, setUserData] = useState({
    username: 'Дмитрий Иванов',
    login: 'dmitry_ivanov',
    password: '********',
    registrationDate: '2024-01-15',
    isPasswordVisible: false
  });

  const togglePasswordVisibility = () => {
    setUserData(prev => ({
      ...prev,
      isPasswordVisible: !prev.isPasswordVisible
    }));
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  return (
    <div className="personal-account-page">
      <div className="account-header">
        <h1>Личный кабинет</h1>
        <p className="account-subtitle">Управление вашей учетной записью и данными</p>
      </div>

      <div className="account-content">
        <div className="main-content-wrapper">
          <div className="user-info-card">
            <div className="user-avatar-section">
              <div className="user-avatar-large">
                Д
              </div>
              <div className="user-name-display">
                <h2>{userData.username}</h2>
                <span className="user-status">Ученик</span>
              </div>
            </div>

            <div className="user-details">
              <div className="detail-item">
                <div className="detail-label">
                  Имя пользователя:
                </div>
                <div className="detail-value">{userData.username}</div>
              </div>

              <div className="detail-item">
                <div className="detail-label">
                  Логин:
                </div>
                <div className="detail-value">
                  <span className="login-value">@{userData.login}</span>
                </div>
              </div>

              <div className="detail-item">
                <div className="detail-label">
                  Пароль:
                </div>
                <div className="detail-value password-field">
                  <span className="password-value">
                    {userData.isPasswordVisible ? 'secret123' : userData.password}
                  </span>
                  <button 
                    className="password-toggle"
                    onClick={togglePasswordVisibility}
                    type="button"
                  >
                    {userData.isPasswordVisible ? 'Скрыть' : 'Показать'}
                  </button>
                </div>
              </div>

              <div className="detail-item">
                <div className="detail-label">
                  Дата регистрации:
                </div>
                <div className="detail-value">
                  <span className="date-value">{formatDate(userData.registrationDate)}</span>
                </div>
              </div>
            </div>

            <div className="account-actions">
              <button className="action-btn primary-btn">
                Редактировать профиль
              </button>
              <button className="action-btn secondary-btn">
                Сменить пароль
              </button>
              <button className="action-btn outline-btn">
                Экспорт данных
              </button>
            </div>
          </div>

          <div className="analytics-sidebar">
            <Link to="/analytics" className="analytics-link">
              <div className="analytics-preview-card">
                <div className="analytics-preview-header">
                  <h3>Аналитика обучения</h3>
                </div>
                <p className="analytics-preview-text">
                  Посмотрите подробную статистику вашего прогресса
                </p>
                
                <div className="analytics-stats-preview">
                  <div className="preview-stat">
                    <div className="preview-stat-value">85%</div>
                    <div className="preview-stat-label">Общий прогресс</div>
                  </div>
                  <div className="preview-stat">
                    <div className="preview-stat-value">4/8</div>
                    <div className="preview-stat-label">Материалы</div>
                  </div>
                  <div className="preview-stat">
                    <div className="preview-stat-value">6/12</div>
                    <div className="preview-stat-label">Тесты</div>
                  </div>
                </div>
                
                <div className="view-analytics-btn">
                  Подробная аналитика 
                </div>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PersonalAccount;