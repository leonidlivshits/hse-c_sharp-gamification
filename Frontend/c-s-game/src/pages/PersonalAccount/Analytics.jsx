import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Analytics.css';

const Analytics = () => {
  const [activeTab, setActiveTab] = useState('progress');
  const navigate = useNavigate();

  const learningData = {
    materialsStudied: 4,
    totalMaterials: 8,
    testsCompleted: 6,
    totalTests: 12,
    averageScore: 85,
    studyTime: '48ч 30м',
    lastActive: 'сегодня, 14:30'
  };

  const progressData = [
    { week: 'Неделя 1', progress: 70 },
    { week: 'Неделя 2', progress: 85 },
    { week: 'Неделя 3', progress: 78 },
    { week: 'Неделя 4', progress: 92 },
    { week: 'Неделя 5', progress: 88 },
    { week: 'Неделя 6', progress: 95 },
  ];

  const testResults = [
    { name: 'Основы React.js', score: 90, date: '15.01.2024' },
    { name: 'Компоненты и пропсы', score: 85, date: '18.01.2024' },
    { name: 'ES6+ Syntax', score: 92, date: '22.01.2024' },
    { name: 'CSS Layout', score: 78, date: '25.01.2024' },
    { name: 'Node.js основы', score: 88, date: '30.01.2024' },
  ];

  const renderProgressBar = (percentage) => (
    <div className="progress-bar">
      <div 
        className="progress-fill" 
        style={{ width: `${percentage}%` }}
      />
      <span className="progress-text">{percentage}%</span>
    </div>
  );

  const handleBack = () => {
    navigate('/personal-account');
  };

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <button className="back-button" onClick={handleBack}>
          Назад в личный кабинет
        </button>
        <h1>Аналитика обучения</h1>
        <p className="analytics-subtitle">Статистика вашего прогресса и результатов</p>
      </div>

      <div className="analytics-tabs">
        <button 
          className={`tab-btn ${activeTab === 'progress' ? 'active' : ''}`}
          onClick={() => setActiveTab('progress')}
        >
          Прогресс
        </button>
        <button 
          className={`tab-btn ${activeTab === 'tests' ? 'active' : ''}`}
          onClick={() => setActiveTab('tests')}
        >
          Тесты
        </button>
        <button 
          className={`tab-btn ${activeTab === 'time' ? 'active' : ''}`}
          onClick={() => setActiveTab('time')}
        >
          Время
        </button>
      </div>

      {activeTab === 'progress' && (
        <div className="analytics-content">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-header">
                <h3>Материалы</h3>
              </div>
              <div className="stat-numbers">
                <span className="stat-current">{learningData.materialsStudied}</span>
                <span className="stat-divider">/</span>
                <span className="stat-total">{learningData.totalMaterials}</span>
              </div>
              {renderProgressBar((learningData.materialsStudied / learningData.totalMaterials) * 100)}
            </div>

            <div className="stat-card">
              <div className="stat-header">
                <h3>Тесты</h3>
              </div>
              <div className="stat-numbers">
                <span className="stat-current">{learningData.testsCompleted}</span>
                <span className="stat-divider">/</span>
                <span className="stat-total">{learningData.totalTests}</span>
              </div>
              {renderProgressBar((learningData.testsCompleted / learningData.totalTests) * 100)}
            </div>

            <div className="stat-card">
              <div className="stat-header">
                <h3>Средний балл</h3>
              </div>
              <div className="stat-numbers">
                <span className="stat-score">{learningData.averageScore}%</span>
              </div>
              <div className="score-indicator">
                <div className="score-bar">
                  <div 
                    className="score-fill" 
                    style={{ width: `${learningData.averageScore}%` }}
                  />
                </div>
                <div className="score-labels">
                  <span>0</span>
                  <span>50</span>
                  <span>100</span>
                </div>
              </div>
            </div>
          </div>

          <div className="progress-chart">
            <h3>Прогресс по неделям</h3>
            <div className="chart-bars">
              {progressData.map((item) => (
                <div key={item.week} className="chart-bar-container">
                  <div className="chart-bar-label">{item.week}</div>
                  <div className="chart-bar-wrapper">
                    <div 
                      className="chart-bar" 
                      style={{ height: `${item.progress}%` }}
                    />
                  </div>
                  <div className="chart-bar-value">{item.progress}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'tests' && (
        <div className="analytics-content">
          <div className="test-results-table">
            <h3>Результаты тестов</h3>
            <table>
              <thead>
                <tr>
                  <th>Название теста</th>
                  <th>Результат</th>
                  <th>Дата прохождения</th>
                </tr>
              </thead>
              <tbody>
                {testResults.map((test) => (
                  <tr key={test.name}>
                    <td>{test.name}</td>
                    <td>
                      <div className="test-score-cell">
                        <span className="test-score">{test.score}%</span>
                        {renderProgressBar(test.score)}
                      </div>
                    </td>
                    <td>{test.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'time' && (
        <div className="analytics-content">
          <div className="time-stats">
            <div className="time-stat-card">
              <div className="time-stat-info">
                <div className="time-stat-value">{learningData.studyTime}</div>
                <div className="time-stat-label">Общее время обучения</div>
              </div>
            </div>
            
            <div className="time-stat-card">
              <div className="time-stat-info">
                <div className="time-stat-value">{learningData.lastActive}</div>
                <div className="time-stat-label">Последняя активность</div>
              </div>
            </div>
          </div>

          <div className="time-distribution">
            <h3>Распределение времени по темам</h3>
            <div className="distribution-list">
              <div className="distribution-item">
                <span className="distribution-topic">React.js</span>
                <span className="distribution-time">18ч 45м</span>
              </div>
              <div className="distribution-item">
                <span className="distribution-topic">JavaScript</span>
                <span className="distribution-time">15ч 20м</span>
              </div>
              <div className="distribution-item">
                <span className="distribution-topic">CSS</span>
                <span className="distribution-time">8ч 10м</span>
              </div>
              <div className="distribution-item">
                <span className="distribution-topic">Node.js</span>
                <span className="distribution-time">6ч 15м</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="analytics-footer">
        <button className="export-btn" onClick={() => alert('Экспорт данных...')}>
          Экспорт данных в PDF
        </button>
        <button className="share-btn" onClick={() => alert('Поделиться...')}>
          Поделиться результатами
        </button>
      </div>
    </div>
  );
};

export default Analytics;