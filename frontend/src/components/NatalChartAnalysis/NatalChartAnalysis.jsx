// NatalChartAnalysis.jsx
import React from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHook';
import css from './NatalChartAnalysis.module.css';

const NatalChartAnalysis = () => {

  const theme = useAppSelector((state) => state.theme.theme);

  return (
    <div className={theme ? css.wrapperLight : css.wrapperDark}>
      <h2 className={css.heading}>Аналіз натальної карти</h2>
      <p className={css.text}>У цьому розділі ви отримаєте розгорнуте тлумачення вашої натальної карти: вплив планет, основні аспекти та життєві напрямки.</p>
    </div>
  );
};

export { NatalChartAnalysis };
