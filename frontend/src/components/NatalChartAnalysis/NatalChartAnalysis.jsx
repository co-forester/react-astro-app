// NatalChartAnalysis.jsx
import React from 'react';
import css from './NatalChartAnalysis.module.css';

const NatalChartAnalysis = () => {
  return (
    <div className={css.wrapper}>
      <h2 className={css.heading}>Аналіз натальної карти</h2>
      <p className={css.text}>У цьому розділі ви отримаєте розгорнуте тлумачення вашої натальної карти: вплив планет, основні аспекти та життєві напрямки.</p>
    </div>
  );
};

export { NatalChartAnalysis };
