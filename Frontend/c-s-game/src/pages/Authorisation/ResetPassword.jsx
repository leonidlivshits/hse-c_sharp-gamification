import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LOGIN_ROUTE } from '../../routing/const';
import './Authorisation.css';

const ResetPassword = () => {
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
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

    if (!formData.password) {
      newErrors.password = 'Введите новый пароль';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Пароль должен содержать минимум 6 символов';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Подтвердите пароль';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Пароли не совпадают';
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
      await new Promise(resolve => setTimeout(resolve, 1500));
      setIsSuccess(true);
      
      setTimeout(() => {
        navigate(LOGIN_ROUTE);
      }, 3000);
      
    } catch (error) {
      setErrors(prev => ({
        ...prev,
        submit: 'Произошла ошибка. Попробуйте снова.'
      }));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        {!isSuccess ? (
          <>
            <div className="auth-header">
              <h1>Создание нового пароля</h1>
              <p>Введите новый пароль для вашего аккаунта</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="password">Новый пароль</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Введите новый пароль"
                  className={errors.password ? 'error' : ''}
                />
                {errors.password && <span className="error-text">{errors.password}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Подтверждение пароля</label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Повторите новый пароль"
                  className={errors.confirmPassword ? 'error' : ''}
                />
                {errors.confirmPassword && (
                  <span className="error-text">{errors.confirmPassword}</span>
                )}
              </div>

              {errors.submit && (
                <div className="submit-error">{errors.submit}</div>
              )}

              <button type="submit" className="auth-button" disabled={isLoading}>
                {isLoading ? 'Сохранение...' : 'Сохранить пароль'}
              </button>
            </form>
          </>
        ) : (
          <div className="success-message">
            <div className="success-icon">✓</div>
            <h2>Пароль успешно изменен!</h2>
            <p>Теперь вы можете войти в систему с новым паролем</p>
            <p className="redirect-message">
              Перенаправление на страницу входа...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResetPassword;