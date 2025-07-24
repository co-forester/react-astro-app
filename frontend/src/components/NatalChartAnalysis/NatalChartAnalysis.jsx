import React from 'react';
import css from './NatalChartAnalysis.module.css';
import { useAppSelector } from '../../hooks/reduxHook';

const NatalChartAnalysis = () => {
  const theme = useAppSelector(state => state.theme.theme);

  return (
    <div className={theme ? css.analysisLight : css.analysisDark}>
      <h2>🔍 Аналіз Натальної Карти</h2>
      <p>
        Тут буде представлений глибокий астрологічний аналіз натальної карти: вплив планет,
        аспекти, елементи, стихії, та інші астрологічні фактори, які формують вашу особистість.
      </p>
      <p>
        🔸 Сонце: воля, его, життєва сила. <br/>
        🔸 Місяць: емоції, підсвідомість, спогади. <br/>
        🔸 Асцендент: зовнішнє проявлення, перше враження. <br/>
        🔸 Аспекти: взаємодія планет між собою.
      </p>
    </div>
  );
};

export { NatalChartAnalysis };