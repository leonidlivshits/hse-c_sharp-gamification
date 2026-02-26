import React from 'react';
import { useParams, Link } from 'react-router-dom';
import './MaterialsDetails.css';

const MaterialDetails = () => {
  const { id } = useParams();

  const materials = [
    {
      id: 1,
      title: 'Введение в React.js',
      docLink: 'https://reactjs.org/docs/getting-started.html',
      publicationDate: '2024-01-15',
      fullContent: `
        React - это JavaScript-библиотека для создания пользовательских интерфейсов. Она позволяет создавать сложные UI из небольших и изолированных частей кода, называемых «компонентами».
        
        **Основные концепции React:**
        
        1. **JSX** - расширение синтаксиса JavaScript, которое позволяет писать HTML-подобный код в JavaScript.
        2. **Компоненты** - строительные блоки React-приложений. Бывают функциональные и классовые компоненты.
        3. **Пропсы (props)** - данные, которые передаются от родительского компонента к дочернему.
        4. **Состояние (state)** - внутренние данные компонента, которые могут меняться со временем.
        5. **Жизненный цикл компонентов** - методы, которые вызываются в разные моменты жизни компонента.
        6. **Хуки (Hooks)** - функции, которые позволяют использовать состояние и другие возможности React в функциональных компонентах.
        
        React использует виртуальный DOM для оптимизации обновлений интерфейса, что делает приложения быстрыми и отзывчивыми.
      `,
      relatedTests: [
        { id: 1, name: 'Основы React.js' },
        { id: 2, name: 'Компоненты и пропсы' },
        { id: 3, name: 'Состояние и жизненный цикл' },
        { id: 4, name: 'React Hooks' },
      ],
    },
    {
      id: 2,
      title: 'JavaScript: современные возможности ES6+',
      docLink: 'https://developer.mozilla.org/ru/docs/Web/JavaScript',
      publicationDate: '2024-01-20',
      fullContent: `
        ES6 (ECMAScript 2015) принес множество новых возможностей в JavaScript, которые сделали язык более выразительным и удобным.
        
        **Ключевые нововведения ES6+:**

        **1. Стрелочные функции (Arrow functions)**
        \`\`\`javascript
        // ES5
        var multiply = function(x, y) { return x * y; };
        
        // ES6
        const multiply = (x, y) => x * y;
        \`\`\`

        **2. Деструктуризация (Destructuring)**
        \`\`\`javascript
        const person = { name: 'John', age: 30 };
        const { name, age } = person;
        \`\`\`

        **3. Операторы spread/rest**
        \`\`\`javascript
        // Spread
        const arr1 = [1, 2, 3];
        const arr2 = [...arr1, 4, 5];
        
        // Rest
        const sum = (...args) => args.reduce((acc, val) => acc + val, 0);
        \`\`\`

        **4. Классы (Classes)**
        \`\`\`javascript
        class Person {
          constructor(name) {
            this.name = name;
          }
          
          greet() {
            return \`Hello, \${this.name}!\`;
          }
        }
        \`\`\`

        **5. Промисы (Promises) и async/await**
        \`\`\`javascript
        // Promises
        fetch(url)
          .then(response => response.json())
          .then(data => console.log(data))
          .catch(error => console.error(error));
        
        // Async/await
        async function getData() {
          try {
            const response = await fetch(url);
            const data = await response.json();
            return data;
          } catch (error) {
            console.error(error);
          }
        }
        \`\`\`

        **6. Модули (Modules)**
        \`\`\`javascript
        // Импорт
        import { Component } from 'react';
        import React, { useState } from 'react';
        
        // Экспорт
        export const CONSTANT = 'value';
        export default function MyComponent() { ... }
        \`\`\`
      `,
      relatedTests: [
        { id: 5, name: 'ES6+ Syntax' },
        { id: 6, name: 'Асинхронный JavaScript' },
        { id: 7, name: 'Классы и наследование' },
      ],
    },
    {
      id: 3,
      title: 'Основы CSS Grid и Flexbox',
      docLink: null,
      publicationDate: '2024-02-01',
      fullContent: `
        CSS Grid и Flexbox - современные технологии верстки, которые решают задачи создания адаптивных макетов.
        
        **Flexbox (Flexible Box Layout)**

        Flexbox идеально подходит для одномерных макетов - расположения элементов по горизонтали или вертикали.
        
        **Основные свойства Flexbox:**
        - \`display: flex\` - создание flex-контейнера
        - \`flex-direction\` - направление основной оси (row, column)
        - \`justify-content\` - выравнивание по основной оси
        - \`align-items\` - выравнивание по поперечной оси
        - \`flex-wrap\` - перенос элементов на новую строку
        
        **Пример:**
        \`\`\`css
        .container {
          display: flex;
          flex-direction: row;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
        }
        \`\`\`

        **CSS Grid Layout**

        Grid предназначен для двумерных макетов - одновременного управления строками и колонками.
        
        **Основные свойства Grid:**
        - \`display: grid\` - создание grid-контейнера
        - \`grid-template-columns\` - определение колонок
        - \`grid-template-rows\` - определение строк
        - \`grid-gap\` - промежутки между элементами
        - \`grid-template-areas\` - именованные области
        
        **Пример:**
        \`\`\`css
        .container {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          grid-template-rows: auto;
          grid-gap: 20px;
          grid-template-areas:
            "header header header"
            "sidebar content content"
            "footer footer footer";
        }
        \`\`\`

        **Когда использовать:**
        - **Flexbox**: когда нужно выровнять элементы в одном направлении
        - **Grid**: когда нужен сложный двумерный макет
      `,
      relatedTests: [
        { id: 8, name: 'CSS Layout' },
        { id: 9, name: 'Адаптивная верстка' },
        { id: 10, name: 'Flexbox vs Grid' },
      ],
    },
    {
      id: 4,
      title: 'Основы Node.js и Express',
      docLink: 'https://nodejs.org/docs/latest/api/',
      publicationDate: '2024-02-10',
      fullContent: `
        Node.js - среда выполнения JavaScript на стороне сервера, построенная на движке V8. Express - минималистичный веб-фреймворк для Node.js.
        
        **Основы Node.js:**

        1. **Асинхронный ввод/вывод** - Node.js использует неблокирующую модель ввода/вывода
        2. **Event Loop** - механизм обработки асинхронных операций
        3. **Модули** - система модулей CommonJS
        4. **NPM (Node Package Manager)** - менеджер пакетов

        **Создание простого сервера на Node.js:**
        \`\`\`javascript
        const http = require('http');
        
        const server = http.createServer((req, res) => {
          res.statusCode = 200;
          res.setHeader('Content-Type', 'text/plain');
          res.end('Hello, World!\\n');
        });
        
        server.listen(3000, () => {
          console.log('Server running at http://localhost:3000/');
        });
        \`\`\`

        **Основы Express:**

        1. **Маршрутизация (Routing)** - определение конечных точек (endpoints)
        2. **Middleware** - промежуточные обработчики запросов
        3. **Шаблонизаторы (Templates)** - EJS, Pug, Handlebars
        4. **Работа с базами данных** - MongoDB, PostgreSQL, MySQL

        **Пример приложения на Express:**
        \`\`\`javascript
        const express = require('express');
        const app = express();
        const port = 3000;
        
        // Middleware для обработки JSON
        app.use(express.json());
        
        // Маршрут GET
        app.get('/', (req, res) => {
          res.send('Hello World!');
        });
        
        // Маршрут POST
        app.post('/api/users', (req, res) => {
          const user = req.body;
          // Сохранение пользователя в БД
          res.status(201).json(user);
        });
        
        // Middleware для обработки ошибок
        app.use((err, req, res, next) => {
          console.error(err.stack);
          res.status(500).send('Something broke!');
        });
        
        app.listen(port, () => {
          console.log(\`Server running at http://localhost:\${port}\`);
        });
        \`\`\`

        **REST API принципы:**
        - GET - получение данных
        - POST - создание новых данных
        - PUT/PATCH - обновление данных
        - DELETE - удаление данных
      `,
      relatedTests: [
        { id: 11, name: 'Node.js основы' },
        { id: 12, name: 'REST API с Express' },
        { id: 13, name: 'Middleware и маршрутизация' },
      ],
    },
  ];

  const material = materials.find((m) => m.id === parseInt(id));

  if (!material) {
    return (
      <div className="material-not-found">
        <h2>Материал не найден</h2>
        <p>Запрошенный материал не существует или был удален.</p>
        <Link to="/materials" className="back-link">
          Вернуться к материалам
        </Link>
      </div>
    );
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  return (
    <div className="material-details-page">
      <div className="material-details-header">
        <Link to="/materials" className="back-button">
          Назад к материалам
        </Link>
        <h1>{material.title}</h1>
        <div className="material-meta">
          <span className="material-date">{formatDate(material.publicationDate)}</span>
          {material.docLink && (
            <a
              href={material.docLink}
              target="_blank"
              rel="noopener noreferrer"
              className="doc-link-header"
            >
              Официальная документация
            </a>
          )}
        </div>
      </div>

      <div className="material-content-full">
        <div className="content-section">
          <h2>Полное содержание</h2>
          <div className="content-text">
            {material.fullContent.split('\n').map((paragraph, index) => {
              if (paragraph.startsWith('**') && paragraph.endsWith('**')) {
                return <h3 key={index}>{paragraph.replace(/\*\*/g, '')}</h3>;
              } else if (paragraph.includes('```')) {
                const code = paragraph.replace(/```.*/g, '').trim();
                if (code) {
                  return (
                    <pre key={index} className="code-block">
                      <code>{code}</code>
                    </pre>
                  );
                }
                return null;
              } else if (paragraph.trim() === '') {
                return <br key={index} />;
              } else {
                return <p key={index}>{paragraph}</p>;
              }
            })}
          </div>
        </div>

        <div className="material-sidebar">
          <div className="sidebar-section">
            <h3>Связанные тесты</h3>
            <div className="tests-list">
              {material.relatedTests.map((test) => (
                <div key={test.id} className="test-item">
                  <span className="test-bullet">•</span>
                  <span className="test-name">{test.name}</span>
                  <Link to={`/tests`} className="take-test-link">
                    Пройти тест
                  </Link>
                </div>
              ))}
            </div>
          </div>

          <div className="sidebar-section">
            <h3>Информация о материале</h3>
            <div className="material-info">
              <div className="info-item">
                <span className="info-label">ID материала:</span>
                <span className="info-value">#{material.id}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Дата публикации:</span>
                <span className="info-value">{formatDate(material.publicationDate)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Кол-во тестов:</span>
                <span className="info-value">{material.relatedTests.length}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Документация:</span>
                <span className="info-value">{material.docLink ? 'Доступна' : 'Не доступна'}</span>
              </div>
              <button className="action-btn save-btn save-btn-sidebar">
                Сохранить для изучения
              </button>
            </div>
          </div>

          {material.docLink && (
            <div className="sidebar-section">
              <h3>Полезные ссылки</h3>
              <a
                href={material.docLink}
                target="_blank"
                rel="noopener noreferrer"
                className="external-link"
              >
                Открыть документацию
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MaterialDetails;
