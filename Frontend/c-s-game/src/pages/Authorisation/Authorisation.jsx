import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LOGIN_ROUTE, REGISTER_ROUTE, MAIN_ROUTE } from '../../routing/const';
import './Authorisation.css';

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    rememberMe: false,
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: '',
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

    if (!isLogin) {
      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Подтвердите пароль';
      } else if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Пароли не совпадают';
      }
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
      await new Promise((resolve) => setTimeout(resolve, 1500));

      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('userEmail', formData.email);

      navigate(MAIN_ROUTE);
    } catch (error) {
      console.error('Ошибка авторизации:', error);
      setErrors((prev) => ({
        ...prev,
        submit: 'Ошибка авторизации. Проверьте данные и попробуйте снова.',
      }));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>{isLogin ? 'Вход в аккаунт' : 'Регистрация'}</h1>
          <p>{isLogin ? 'Введите ваши учетные данные' : 'Создайте новый аккаунт'}</p>
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
            />
            {errors.password && <span className="error-text">{errors.password}</span>}
          </div>

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="confirmPassword">Подтверждение пароля</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Повторите пароль"
                className={errors.confirmPassword ? 'error' : ''}
              />
              {errors.confirmPassword && (
                <span className="error-text">{errors.confirmPassword}</span>
              )}
            </div>
          )}

          {isLogin && (
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
              <Link to="/forgot-password" className="forgot-link">
                Забыли пароль?
              </Link>
            </div>
          )}

          {errors.submit && <div className="submit-error">{errors.submit}</div>}

          <button type="submit" className="auth-button" disabled={isLoading}>
            {isLoading ? 'Загрузка...' : isLogin ? 'Войти' : 'Зарегистрироваться'}
          </button>
        </form>

        <div className="auth-switch">
          <p>
            {isLogin ? 'Нет аккаунта?' : 'Уже есть аккаунт?'}
            <button type="button" onClick={() => setIsLogin(!isLogin)} className="switch-button">
              {isLogin ? ' Зарегистрироваться' : ' Войти'}
            </button>
          </p>
        </div>

        <div className="auth-terms">
          <p>
            Нажимая кнопку, вы соглашаетесь с <Link to="/terms">Условиями использования</Link> и{' '}
            <Link to="/privacy">Политикой конфиденциальности</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Auth;
