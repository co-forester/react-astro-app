import React from 'react';
import css from './ChildHoroscope.module.css';

const ChildHoroscope = () => {
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Гороскоп дитини</h1>
      <p className={styles.description}>
        Цей розділ допоможе краще зрозуміти природні схильності, характер та потенціал дитини.
      </p>
    </div>
  );
};

export default ChildHoroscope;