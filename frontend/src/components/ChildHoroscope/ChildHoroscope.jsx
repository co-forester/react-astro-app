// ChildHoroscope.jsx
import React from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHook';
import css from './ChildHoroscope.module.css';

const ChildHoroscope = () => {

  const theme = useAppSelector((state) => state.theme.theme);

  return (
    <div className={theme? css.containerLight : css.containerDark}>
      <h2 className={css.title}>Гороскоп дитини</h2>
      <p className={css.description}>Цей розділ присвячено аналізу натальної карти вашої дитини. Дізнайтеся більше про її характер, здібності та потенціал.</p>
    </div>
  );
};

export { ChildHoroscope };
