// src/pages/Authorisation/EditProfile.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PERSONAL_ACCOUNT_ROUTE } from '../../routing/const';
import './EditProfile.css';

const EditProfile = () => {
  const navigate = useNavigate();
  const [name, setName] = useState(localStorage.getItem('userName') || 'Дмитрий Иванов');
  const [isSaving, setIsSaving] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsSaving(true);
    // Имитация сохранения (здесь можно добавить реальный запрос к API)
    setTimeout(() => {
      localStorage.setItem('userName', name);
      setIsSaving(false);
      navigate(PERSONAL_ACCOUNT_ROUTE);
    }, 500);
  };

  return (
    <div className="edit-profile-container">
      <div className="edit-profile-card">
        <h1>Редактирование профиля</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Имя</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Введите ваше имя"
              required
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="save-btn" disabled={isSaving}>
              {isSaving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button
              type="button"
              className="cancel-btn"
              onClick={() => navigate(PERSONAL_ACCOUNT_ROUTE)}
            >
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditProfile;
