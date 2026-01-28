import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import './TestDetails.css';

const TestDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [testData, setTestData] = useState(null);
  const [userAnswers, setUserAnswers] = useState({});
  const [openAnswers, setOpenAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [testSubmitted, setTestSubmitted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  useEffect(() => {
    const test = {
      id: parseInt(id),
      title: "Основы React.js",
      questions: [
        {
          id: 1,
          text: "Что такое JSX в React?",
          options: [
            "JavaScript XML - расширение синтаксиса JavaScript",
            "Java Syntax Extension - расширение Java для React",
            "JavaScript Extension - специальное расширение для JS",
            "JQuery XML - аналог XML для JQuery"
          ],
          correctAnswer: 0,
          points: 10,
          materials: null
        },
        {
          id: 2,
          text: "Какой метод жизненного цикла вызывается после первого рендеринга компонента?",
          options: [
            "componentDidMount",
            "componentWillMount",
            "shouldComponentUpdate",
            "componentWillUnmount"
          ],
          correctAnswer: 0,
          points: 15,
          materials: "Пример кода жизненного цикла компонента"
        },
        {
          id: 3,
          text: "Что такое состояние (state) в React?",
          options: [
            "Внутренние данные компонента, которые могут меняться",
            "Статические данные компонента",
            "Глобальные переменные приложения",
            "Параметры, передаваемые в компонент"
          ],
          correctAnswer: 0,
          points: 10,
          materials: null
        },
        {
          id: 4,
          text: "Как передаются данные от родительского компонента к дочернему?",
          options: [
            "Через props",
            "Через state",
            "Через context API",
            "Через refs"
          ],
          correctAnswer: 0,
          points: 12,
          materials: null
        },
        {
          id: 5,
          text: "Что делает метод setState()?",
          options: [
            "Обновляет состояние компонента и вызывает ререндер",
            "Изменяет props компонента",
            "Удаляет компонент из DOM",
            "Создает новый экземпляр компонента"
          ],
          correctAnswer: 0,
          points: 15,
          materials: null
        }
      ],
      openQuestions: [
        {
          id: 6,
          text: "Опишите разницу между функциональными и классовыми компонентами в React. Приведите примеры использования.",
          points: 25,
          materials: "Примеры кода компонентов",
          correctAnswer: "Функциональные компоненты используют хуки, классовые - методы жизненного цикла. Функциональные компоненты проще в написании и тестировании."
        },
        {
          id: 7,
          text: "Объясните концепцию подъема состояния (state lifting) в React. Приведите практический пример.",
          points: 30,
          materials: "Диаграмма подъема состояния",
          correctAnswer: "Подъем состояния - это перемещение состояния к ближайшему общему предку компонентов, которые нуждаются в общих данных."
        }
      ],
      deadline: "2024-03-15T23:59:59",
      publicationDate: "2024-02-15",
      relatedMaterials: [
        { id: 1, title: "Введение в React.js", link: "/materials/1" },
        { id: 2, title: "Компоненты и пропсы", link: "/materials/2" },
        { id: 3, title: "Состояние и жизненный цикл", link: "/materials/3" }
      ],
      maxScore: 117,
      timeLimit: 60,
      status: "in_progress",
      passedBy: 245
    };

    setTestData(test);
    
    if (test.timeLimit) {
      setTimeLeft(test.timeLimit * 60);
    }

    const initialAnswers = {};
    test.questions.forEach(q => {
      initialAnswers[q.id] = null;
    });
    setUserAnswers(initialAnswers);

    const initialOpenAnswers = {};
    test.openQuestions.forEach(q => {
      initialOpenAnswers[q.id] = '';
    });
    setOpenAnswers(initialOpenAnswers);
  }, [id]);

  useEffect(() => {
    let timer;
    if (timeLeft > 0 && testData?.timeLimit && !testSubmitted) {
      timer = setInterval(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      handleSubmitTest();
    }
    return () => clearInterval(timer);
  }, [timeLeft, testSubmitted, testData]);

  const handleAnswerChange = (questionId, answerIndex) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answerIndex
    }));
  };

  const handleOpenAnswerChange = (questionId, value) => {
    setOpenAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleSubmitTest = () => {
    setIsSubmitting(true);
    
    setTimeout(() => {
      setIsSubmitting(false);
      setTestSubmitted(true);
      
      const calculatedScore = 85;
      if (testData) {
        const updatedTest = {
          ...testData,
          userScore: calculatedScore,
          status: 'completed'
        };
        setTestData(updatedTest);
      }
    }, 1500);
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateProgress = () => {
    if (!testData) return 0;
    
    const totalQuestions = testData.questions.length + testData.openQuestions.length;
    const answeredQuestions = 
      Object.values(userAnswers).filter(a => a !== null).length +
      Object.values(openAnswers).filter(a => a.trim() !== '').length;
    
    return Math.round((answeredQuestions / totalQuestions) * 100);
  };

  if (!testData) {
    return (
      <div className="test-loading">
        <div className="loading-spinner"></div>
        <p>Загрузка теста...</p>
      </div>
    );
  }

  const totalQuestions = testData.questions.length + testData.openQuestions.length;

  return (
    <div className="test-details-page">
      <div className="test-header">
        <div className="header-top">
          <Link to="/tests" className="back-button">
            ← Назад к тестам
          </Link>
          {testData.timeLimit && !testSubmitted && (
            <div className={`timer ${timeLeft < 300 ? 'timer-warning' : ''}`}>
              {formatTime(timeLeft)}
            </div>
          )}
        </div>
        
        <h1>{testData.title}</h1>
        
        <div className="test-meta-info">
          <div className="meta-item">
            <span className="meta-label">Дедлайн:</span>
            <span className="meta-value">{formatDate(testData.deadline)}</span>
          </div>
          <div className="meta-item">
            <span className="meta-label">Макс. баллы:</span>
            <span className="meta-value">{testData.maxScore}</span>
          </div>
          <div className="meta-item">
            <span className="meta-label">Вопросов:</span>
            <span className="meta-value">{totalQuestions}</span>
          </div>
          {testData.timeLimit && (
            <div className="meta-item">
              <span className="meta-label">Лимит времени:</span>
              <span className="meta-value">{testData.timeLimit} минут</span>
            </div>
          )}
        </div>
      </div>

      {!testSubmitted ? (
        <>
          <div className="test-progress">
            <div className="progress-info">
              <span>Прогресс: {calculateProgress()}%</span>
              <span>Вопрос {currentQuestion + 1} из {totalQuestions}</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${calculateProgress()}%` }}
              />
            </div>
          </div>

          <div className="test-content">
            <div className="questions-navigation">
              <h3>Навигация по вопросам</h3>
              <div className="question-dots">
                {[...Array(testData.questions.length + testData.openQuestions.length)].map((_, index) => (
                  <button
                    key={index}
                    className={`question-dot ${index === currentQuestion ? 'active' : ''} ${
                      (index < testData.questions.length && userAnswers[testData.questions[index].id] !== null) ||
                      (index >= testData.questions.length && openAnswers[testData.openQuestions[index - testData.questions.length].id] !== '') 
                        ? 'answered' : ''
                    }`}
                    onClick={() => setCurrentQuestion(index)}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
            </div>

            <div className="questions-container">
              {currentQuestion < testData.questions.length ? (
                <div className="question-card">
                  <div className="question-header">
                    <h3>Вопрос {currentQuestion + 1} (с выбором ответа)</h3>
                    <span className="question-points">
                      Баллы: {testData.questions[currentQuestion].points}
                    </span>
                  </div>
                  
                  <div className="question-text">
                    <p>{testData.questions[currentQuestion].text}</p>
                  </div>
                  
                  {testData.questions[currentQuestion].materials && (
                    <div className="question-materials">
                      <h4>📎 Материалы к вопросу:</h4>
                      <p>{testData.questions[currentQuestion].materials}</p>
                    </div>
                  )}
                  
                  <div className="answer-options">
                    {testData.questions[currentQuestion].options.map((option, index) => (
                      <div key={index} className="option-item">
                        <input
                          type="radio"
                          id={`q${testData.questions[currentQuestion].id}_opt${index}`}
                          name={`question_${testData.questions[currentQuestion].id}`}
                          checked={userAnswers[testData.questions[currentQuestion].id] === index}
                          onChange={() => handleAnswerChange(testData.questions[currentQuestion].id, index)}
                        />
                        <label htmlFor={`q${testData.questions[currentQuestion].id}_opt${index}`}>
                          {option}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="question-card open-question">
                  <div className="question-header">
                    <h3>Вопрос {currentQuestion + 1} (открытый ответ)</h3>
                    <span className="question-points">
                      Баллы: {testData.openQuestions[currentQuestion - testData.questions.length].points}
                    </span>
                  </div>
                  
                  <div className="question-text">
                    <p>{testData.openQuestions[currentQuestion - testData.questions.length].text}</p>
                  </div>
                  
                  {testData.openQuestions[currentQuestion - testData.questions.length].materials && (
                    <div className="question-materials">
                      <h4>Материалы к вопросу:</h4>
                      <p>{testData.openQuestions[currentQuestion - testData.questions.length].materials}</p>
                    </div>
                  )}
                  
                  <div className="open-answer">
                    <textarea
                      value={openAnswers[testData.openQuestions[currentQuestion - testData.questions.length].id] || ''}
                      onChange={(e) => handleOpenAnswerChange(
                        testData.openQuestions[currentQuestion - testData.questions.length].id,
                        e.target.value
                      )}
                      placeholder="Введите ваш ответ здесь..."
                      rows={8}
                    />
                    <div className="answer-hint">
      <span className="hint-text">
        Этот ответ будет проверен учителем вручную. Постарайтесь дать развернутый ответ.
      </span>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="navigation-buttons">
                <button
                  className="nav-btn prev-btn"
                  onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                  disabled={currentQuestion === 0}
                >
                  ← Предыдущий вопрос
                </button>
                
                <button
                  className="nav-btn next-btn"
                  onClick={() => setCurrentQuestion(prev => Math.min(totalQuestions - 1, prev + 1))}
                  disabled={currentQuestion === totalQuestions - 1}
                >
                  Следующий вопрос →
                </button>
              </div>
            </div>
          </div>

          <div className="test-footer">
            <div className="submit-section">
              <div className="answers-summary">
                <div className="summary-item">
                  <span className="summary-label">Отвечено:</span>
                  <span className="summary-value">
                    {Object.values(userAnswers).filter(a => a !== null).length + 
                     Object.values(openAnswers).filter(a => a.trim() !== '').length} / {totalQuestions}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Прогресс:</span>
                  <span className="summary-value">{calculateProgress()}%</span>
                </div>
              </div>
              
              <button
                className="submit-btn"
                onClick={handleSubmitTest}
                disabled={isSubmitting || calculateProgress() === 0}
              >
                {isSubmitting ? (
                  <>
                    <span className="spinner"></span>
                    Отправка...
                  </>
                ) : (
                  'Отправить тест на проверку'
                )}
              </button>
              
              <div className="submit-warning">
                После отправки вы не сможете изменить ответы.
                {testData.timeLimit && ` Осталось времени: ${formatTime(timeLeft)}`}
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="test-results">
          <div className="results-header">
            <h2>🎉 Тест завершен!</h2>
            <p>Ваши ответы отправлены на проверку.</p>
          </div>
          
          <div className="score-card">
            <div className="score-display">
              <div className="score-info">
                <div className="score-text">Предварительный результат</div>
                <div className="score-value">
                  {testData.userScore} / {testData.maxScore} 
                  <span className="score-percentage">
                    ({Math.round((testData.userScore / testData.maxScore) * 100)}%)
                  </span>
                </div>
              </div>
            </div>
            
            <div className="score-details">
              <div className="detail-item">
                <span className="detail-label">Вопросов с выбором:</span>
                <span className="detail-value">{testData.questions.length}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Открытых вопросов:</span>
                <span className="detail-value">{testData.openQuestions.length}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Максимальный балл:</span>
                <span className="detail-value">{testData.maxScore}</span>
              </div>
            </div>
          </div>
          
          <div className="results-info">
            <div className="info-card">
              <h3>Что дальше?</h3>
              <ul>
                <li>Вопросы с выбором проверены автоматически</li>
                <li>Открытые вопросы будут проверены учителем в течение 3-5 дней</li>
                <li>Окончательный результат будет доступен в личном кабинете</li>
                <li>Вы получите уведомление о результатах проверки</li>
              </ul>
            </div>
            
            <div className="info-card">
              <h3>Рекомендуемые материалы</h3>
              <p>Для улучшения понимания темы рекомендуем изучить:</p>
              <div className="materials-list">
                {testData.relatedMaterials.map((material) => (
                  <Link 
                    key={material.id} 
                    to={material.link}
                    className="material-link"
                  >
                    {material.title}
                  </Link>
                ))}
              </div>
            </div>
          </div>
          
          <div className="results-actions">
            <button className="action-btn" onClick={() => navigate('/tests')}>
              ← Вернуться к списку тестов
            </button>
            <button className="action-btn secondary" onClick={() => window.print()}>
              Распечатать результаты
            </button>
            <button className="action-btn primary" onClick={() => navigate('/analytics')}>
              Смотреть аналитику
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TestDetails;