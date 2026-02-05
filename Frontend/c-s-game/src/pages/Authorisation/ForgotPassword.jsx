import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { LOGIN_ROUTE } from '../../routing/const';
import './Authorisation.css';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email) {
      setError('Введите email');
      return;
    }
    
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('Введите корректный email');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setIsSubmitted(true);
    } catch (err) {
      setError('Произошла ошибка. Попробуйте снова.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        {!isSubmitted ? (
          <>
            <div className="auth-header">
              <h1>Восстановление пароля</h1>
              <p>Введите email, указанный при регистрации</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Введите ваш email"
                  className={error ? 'error' : ''}
                />
                {error && <span className="error-text">{error}</span>}
              </div>

              <button type="submit" className="auth-button" disabled={isLoading}>
                {isLoading ? 'Отправка...' : 'Отправить ссылку'}
              </button>
            </form>

            <div className="auth-switch">
              <p>
                Вспомнили пароль?{' '}
                <Link to={LOGIN_ROUTE} className="switch-link">
                  Войти
                </Link>
              </p>
            </div>
          </>
        ) : (
          <div className="success-message">
            <div className="success-icon">✓</div>
            <h2>Письмо отправлено!</h2>
            <p>Инструкции по восстановлению пароля отправлены на email {email}</p>
            <Link to={LOGIN_ROUTE} className="auth-button">
              Вернуться ко входу
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;