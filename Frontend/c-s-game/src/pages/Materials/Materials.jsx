import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Materials.css';

const Materials = () => {
  const [materials] = useState([
    {
      id: 1,
      title: 'Введение в React.js',
      docLink: 'https://reactjs.org/docs/getting-started.html',
      publicationDate: '2024-01-15',
      content:
        'React - это JavaScript-библиотека для создания пользовательских интерфейсов. Она позволяет создавать сложные UI из небольших и изолированных частей кода, называемых «компонентами». В этом материале рассмотрим основные концепции: JSX, компоненты, пропсы, состояние и жизненный цикл компонентов.',
      relatedTests: [
        { id: 1, name: 'Основы React.js' },
        { id: 2, name: 'Компоненты и пропсы' },
      ],
    },
    {
      id: 2,
      title: 'JavaScript: современные возможности ES6+',
      docLink: 'https://developer.mozilla.org/ru/docs/Web/JavaScript',
      publicationDate: '2024-01-20',
      content:
        'ES6 (ECMAScript 2015) принес множество новых возможностей в JavaScript. Рассмотрим ключевые нововведения: стрелочные функции, деструктуризация, операторы spread/rest, классы, промисы, async/await, модули. Эти возможности делают код более читаемым и эффективным.',
      relatedTests: [
        { id: 3, name: 'ES6+ Syntax' },
        { id: 4, name: 'Асинхронный JavaScript' },
      ],
    },
    {
      id: 3,
      title: 'Основы CSS Grid и Flexbox',
      docLink: null,
      publicationDate: '2024-02-01',
      content:
        'CSS Grid и Flexbox - современные технологии верстки, которые решают задачи создания адаптивных макетов. Flexbox идеально подходит для одномерных макетов (строка или колонка), а Grid - для двумерных. Рассмотрим основные свойства и примеры использования.',
      relatedTests: [
        { id: 5, name: 'CSS Layout' },
        { id: 6, name: 'Адаптивная верстка' },
      ],
    },
    {
      id: 4,
      title: 'Основы Node.js и Express',
      docLink: 'https://nodejs.org/docs/latest/api/',
      publicationDate: '2024-02-10',
      content:
        'Node.js - среда выполнения JavaScript на стороне сервера. Express - минималистичный веб-фреймворк для Node.js. В этом материале рассмотрим создание REST API, работу с middleware, маршрутизацию и подключение к базам данных.',
      relatedTests: [
        { id: 7, name: 'Node.js основы' },
        { id: 8, name: 'REST API с Express' },
      ],
    },
  ]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const truncateText = (text, maxLength = 200) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="materials-page">
      <div className="materials-header">
        <h1>Материалы для обучения</h1>
        <p className="materials-subtitle">
          Изучайте материалы и проверяйте знания с помощью тестов
        </p>
      </div>

      <div className="materials-grid">
        {materials.map((material) => (
          <div key={material.id} className="material-card">
            <div className="material-header">
              <Link to={`/materials/${material.id}`} className="material-title-link">
                <h2 className="material-title">{material.title}</h2>
              </Link>
              <span className="material-date">{formatDate(material.publicationDate)}</span>
            </div>

            <div className="material-content">
              <p>{truncateText(material.content, 200)}</p>
            </div>

            <div className="material-footer">
              <div className="material-links">
                {material.docLink && (
                  <a
                    href={material.docLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="doc-link"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Документация
                  </a>
                )}

                {material.relatedTests && material.relatedTests.length > 0 && (
                  <div className="tests-section">
                    <h4>Связанные тесты:</h4>
                    <div className="tests-list">
                      {material.relatedTests.map((test) => (
                        <Link
                          key={test.id}
                          to={`/tests`}
                          className="test-link"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {test.name}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="materials-stats">
        <div className="stat-item">
          <div className="stat-number">{materials.length}</div>
          <div className="stat-label">Материалов доступно</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">
            {materials.reduce((acc, mat) => acc + (mat.relatedTests?.length || 0), 0)}
          </div>
          <div className="stat-label">Тестов доступно</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">{materials.filter((m) => m.docLink).length}</div>
          <div className="stat-label">С документацией</div>
        </div>
      </div>
    </div>
  );
};

export default Materials;
