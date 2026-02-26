import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Tests.css';

const Tests = () => {
  const [tests] = useState([
    {
      id: 1,
      title: 'Основы React.js',
      questions: [
        {
          id: 1,
          text: 'Что такое JSX?',
          options: ['JavaScript XML', 'Java Syntax Extension', 'JavaScript Extension'],
          correctAnswer: 0,
          points: 10,
          materials: null,
        },
        {
          id: 2,
          text: 'Какой метод жизненного цикла вызывается после рендеринга компонента?',
          options: ['componentDidMount', 'componentWillMount', 'shouldComponentUpdate'],
          correctAnswer: 0,
          points: 15,
          materials: null,
        },
        {
          id: 3,
          text: 'Что возвращает метод render()?',
          options: ['HTML', 'React элементы', 'Строку'],
          correctAnswer: 1,
          points: 10,
          materials: null,
        },
      ],
      openQuestions: [
        {
          id: 1,
          text: 'Опишите разницу между функциональными и классовыми компонентами',
          points: 25,
          materials: null,
          userAnswer: '',
        },
      ],
      deadline: '2024-03-15T23:59:59',
      publicationDate: '2024-02-15',
      relatedMaterials: [
        { id: 1, title: 'Введение в React.js', link: '/materials/1' },
        { id: 2, title: 'Компоненты и пропсы', link: '/materials/2' },
      ],
      userScore: 0,
      maxScore: 60,
      timeLimit: 60,
      status: 'not_started',
    },
    {
      id: 2,
      title: 'JavaScript ES6+',
      questions: [
        {
          id: 4,
          text: 'Что такое деструктуризация?',
          options: [
            'Разрушение объекта',
            'Извлечение значений из объектов/массивов',
            'Удаление свойств объекта',
          ],
          correctAnswer: 1,
          points: 10,
          materials: null,
        },
        {
          id: 5,
          text: 'Что делает оператор spread?',
          options: ['Копирует объект', 'Распространяет значения', 'Объединяет массивы'],
          correctAnswer: 1,
          points: 10,
          materials: null,
        },
      ],
      openQuestions: [
        {
          id: 2,
          text: 'Объясните разницу между let, const и var',
          points: 20,
          materials: null,
          userAnswer: '',
        },
        {
          id: 3,
          text: 'Напишите пример использования Promise.all()',
          points: 25,
          materials: null,
          userAnswer: '',
        },
      ],
      deadline: '2024-03-20T23:59:59',
      publicationDate: '2024-02-20',
      relatedMaterials: [
        { id: 3, title: 'JavaScript: современные возможности ES6+', link: '/materials/2' },
      ],
      userScore: 0,
      maxScore: 65,
      timeLimit: 45,
      status: 'not_started',
    },
    {
      id: 3,
      title: 'CSS Grid и Flexbox',
      questions: [
        {
          id: 6,
          text: 'Для чего используется flexbox?',
          options: ['Для одномерных макетов', 'Для двумерных макетов', 'Для анимаций'],
          correctAnswer: 0,
          points: 10,
          materials: null,
        },
        {
          id: 7,
          text: 'Какое свойство CSS Grid определяет колонки?',
          options: ['grid-template-columns', 'grid-columns', 'grid-col'],
          correctAnswer: 0,
          points: 10,
          materials: null,
        },
      ],
      openQuestions: [
        {
          id: 4,
          text: 'Создайте сетку из 3 колонок с равной шириной и промежутком 20px',
          points: 30,
          materials: 'Пример кода grid',
          userAnswer: '',
        },
      ],
      deadline: '2024-03-10T23:59:59',
      publicationDate: '2024-02-01',
      relatedMaterials: [{ id: 4, title: 'Основы CSS Grid и Flexbox', link: '/materials/3' }],
      userScore: 0,
      maxScore: 50,
      timeLimit: null,
      status: 'overdue',
    },
    {
      id: 4,
      title: 'Node.js основы',
      questions: [
        {
          id: 8,
          text: 'Что такое Node.js?',
          options: ['Среда выполнения JavaScript', 'Фреймворк', 'Библиотека'],
          correctAnswer: 0,
          points: 10,
          materials: null,
        },
        {
          id: 9,
          text: 'Какой модуль используется для создания HTTP сервера?',
          options: ['http', 'https', 'server'],
          correctAnswer: 0,
          points: 10,
          materials: null,
        },
      ],
      openQuestions: [
        {
          id: 5,
          text: 'Опишите архитектуру Event Loop в Node.js',
          points: 30,
          materials: null,
          userAnswer: '',
        },
        {
          id: 6,
          text: 'Напишите простой HTTP сервер на Express',
          points: 25,
          materials: 'Пример кода Express',
          userAnswer: '',
        },
      ],
      deadline: '2024-03-25T23:59:59',
      publicationDate: '2024-02-10',
      relatedMaterials: [{ id: 5, title: 'Основы Node.js и Express', link: '/materials/4' }],
      userScore: 65,
      maxScore: 85,
      timeLimit: 90,
      status: 'completed',
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

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status, deadline) => {
    const now = new Date();
    const deadlineDate = new Date(deadline);

    if (status === 'completed') return { text: 'Завершен', class: 'status-completed' };
    if (status === 'in_progress') return { text: 'В процессе', class: 'status-in-progress' };
    if (status === 'overdue' || (status === 'not_started' && now > deadlineDate))
      return { text: 'Просрочен', class: 'status-overdue' };
    return { text: 'Не начат', class: 'status-not-started' };
  };

  const getTotalQuestions = (test) => {
    return test.questions.length + test.openQuestions.length;
  };

  return (
    <div className="tests-page">
      <div className="tests-header">
        <h1>Тесты и проверка знаний</h1>
        <p className="tests-subtitle">Пройдите тесты для проверки усвоения материалов</p>
      </div>

      <div className="tests-stats">
        <div className="test-stat-card">
          <div className="test-stat-info">
            <div className="test-stat-value">{tests.length}</div>
            <div className="test-stat-label">Всего тестов</div>
          </div>
        </div>
        <div className="test-stat-card">
          <div className="test-stat-info">
            <div className="test-stat-value">
              {tests.filter((t) => t.status === 'completed').length}
            </div>
            <div className="test-stat-label">Завершено</div>
          </div>
        </div>
        <div className="test-stat-card">
          <div className="test-stat-info">
            <div className="test-stat-value">{tests.filter((t) => t.timeLimit).length}</div>
            <div className="test-stat-label">С ограничением времени</div>
          </div>
        </div>
      </div>

      <div className="tests-grid">
        {tests.map((test) => {
          const statusBadge = getStatusBadge(test.status, test.deadline);

          return (
            <div key={test.id} className="test-card">
              <div className="test-header">
                <div className="test-title-section">
                  <h2 className="test-title">{test.title}</h2>
                  <span className={`status-badge ${statusBadge.class}`}>{statusBadge.text}</span>
                </div>

                <div className="test-meta">
                  <div className="meta-item">
                    <span className="meta-label">Дедлайн:</span>
                    <span className="meta-value">{formatDateTime(test.deadline)}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Опубликован:</span>
                    <span className="meta-value">{formatDate(test.publicationDate)}</span>
                  </div>
                </div>
              </div>

              <div className="test-content">
                <div className="test-stats-details">
                  <div className="stat-detail">
                    <span className="stat-label">Вопросы:</span>
                    <span className="stat-value">{getTotalQuestions(test)}</span>
                  </div>
                  <div className="stat-detail">
                    <span className="stat-label">Макс. баллы:</span>
                    <span className="stat-value">{test.maxScore}</span>
                  </div>
                  {test.timeLimit && (
                    <div className="stat-detail">
                      <span className="stat-label">Время:</span>
                      <span className="stat-value">{test.timeLimit} мин.</span>
                    </div>
                  )}
                </div>

                {test.status === 'completed' && (
                  <div className="test-results">
                    <div className="score-display">
                      <span className="score-label">Ваш результат:</span>
                      <span className="score-value">
                        {test.userScore}/{test.maxScore}
                        <span className="score-percentage">
                          ({Math.round((test.userScore / test.maxScore) * 100)}%)
                        </span>
                      </span>
                    </div>

                    <div className="related-materials">
                      <h4>Связанные материалы:</h4>
                      <div className="materials-list">
                        {test.relatedMaterials.map((material) => (
                          <Link key={material.id} to={material.link} className="material-link">
                            {material.title}
                          </Link>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="test-footer">
                <div className="test-actions">
                  {test.status === 'completed' ? (
                    <>
                      <button className="action-btn view-results-btn">Посмотреть результаты</button>
                      <button className="action-btn retry-btn">Пройти заново</button>
                    </>
                  ) : test.status === 'in_progress' ? (
                    <Link to={`/test/${test.id}`} className="action-btn continue-btn">
                      Продолжить тест
                    </Link>
                  ) : (
                    <Link to={`/test/${test.id}`} className="action-btn start-btn">
                      Начать тест
                    </Link>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="tests-info">
        <h3>Информация о тестах</h3>
        <div className="info-grid">
          <div className="info-item">
            <div className="info-content">
              <h4>Вопросы с выбором ответа</h4>
              <p>Проверяются автоматически. Выберите один правильный вариант из предложенных.</p>
            </div>
          </div>
          <div className="info-item">
            <div className="info-content">
              <h4>Вопросы с открытым ответом</h4>
              <p>Проверяются учителем вручную. Требуют развернутого ответа.</p>
            </div>
          </div>
          <div className="info-item">
            <div className="info-content">
              <h4>Ограничение по времени</h4>
              <p>Некоторые тесты имеют ограничение по времени выполнения.</p>
            </div>
          </div>
          <div className="info-item">
            <div className="info-content">
              <h4>Связанные материалы</h4>
              <p>После завершения теста доступны материалы для углубленного изучения.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Tests;
