import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MAIN_ROUTE, REGISTER_ROUTE, FORGOT_PASSWORD_ROUTE } from '../../routing/const';
import './Authorisation.css';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Введите email';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Введите корректный email';
    }

    if (!formData.password) {
      newErrors.password = 'Введите пароль';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Пароль должен содержать минимум 6 символов';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('userEmail', formData.email);
      if (formData.rememberMe) {
        localStorage.setItem('rememberMe', 'true');
      }
      
      navigate(MAIN_ROUTE, { replace: true });
      
    } catch (error) {
      console.error('Ошибка входа:', error);
      setErrors(prev => ({
        ...prev,
        submit: 'Ошибка входа. Проверьте данные и попробуйте снова.'
      }));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Вход в систему</h1>
          <p>Введите ваши учетные данные для доступа к платформе</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Введите ваш email"
              className={errors.email ? 'error' : ''}
              autoComplete="email"
            />
            {errors.email && <span className="error-text">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Введите пароль"
              className={errors.password ? 'error' : ''}
              autoComplete="current-password"
            />
            {errors.password && <span className="error-text">{errors.password}</span>}
          </div>

          <div className="form-options">
            <div className="checkbox-group">
              <input
                type="checkbox"
                id="rememberMe"
                name="rememberMe"
                checked={formData.rememberMe}
                onChange={handleChange}
              />
              <label htmlFor="rememberMe">Запомнить меня</label>
            </div>
            <Link to={FORGOT_PASSWORD_ROUTE} className="forgot-link">
              Забыли пароль?
            </Link>
          </div>

          {errors.submit && (
            <div className="submit-error">{errors.submit}</div>
          )}

          <button type="submit" className="auth-button" disabled={isLoading}>
            {isLoading ? 'Вход...' : 'Войти'}
          </button>
        </form>

        <div className="auth-switch">
          <p>
            Нет аккаунта?{' '}
            <Link to={REGISTER_ROUTE} className="switch-link">
              Зарегистрироваться
            </Link>
          </p>
        </div>

        <div className="auth-terms">
          <p>
            Нажимая кнопку, вы соглашаетесь с{' '}
            <Link to="/terms">Условиями использования</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;