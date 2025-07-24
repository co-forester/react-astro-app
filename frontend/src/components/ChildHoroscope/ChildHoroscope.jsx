// ChildHoroscope.jsx
import React from 'react';
import css from './ChildHoroscope.module.css';

const ChildHoroscope = () => {
  return (
    <div className={css.container}>
      <h2 className={css.title}>Гороскоп дитини</h2>
      <p className={css.description}>Цей розділ присвячено аналізу натальної карти вашої дитини. Дізнайтеся більше про її характер, здібності та потенціал.</p>
    </div>
  );
};

export { ChildHoroscope };