import React from 'react';
import './Footer.css';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="Footer">
      <div className="footer-links">
        <a href="/offer" className="footer-link">Оферта</a>
        <a href="/organization-info" className="footer-link">Сведения об образовательной организации</a>
        <a href="/privacy-policy" className="footer-link">Политика обработки персональных данных</a>
      </div>
      
      <p className="footer-text">
        По вопросам обращайтесь в чат поддержки
      </p>
      
      <p className="footer-copyright">
        © {currentYear}, АНО ДПО «Т-Образование»
      </p>
    </footer>
  );
};

export default Footer;