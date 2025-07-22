import React from 'react';


import {  useAppSelector } from '../../hooks/reduxHook';
// import { themeActions } from '../../redux/slices/themeSlice';
import css from './natalChart.module.css'; 
import logo from '../../images/astro_w2gw_serhii_kolesnyk.68459.2485561.png'; // якщо використовується імпорт логотипу

const NatalChart = () => {

  const theme = useAppSelector(state => state.theme.theme);
  
  

  return (
    <div className={theme ? css.NatalChartLight : css.NatalChartDark}>
      <div className="chart">
      <img src={logo} alt="Логотип Альбірео" className={css.logo} />
     </div>

    <h2>Загальна інформація</h2>
    <p>
      <strong>Ім’я:</strong> Serhii Kolesnyk<br />
      <strong>Дата народження:</strong> 6 грудня 1972<br />
      <strong>Час:</strong> 01:25<br />
      <strong>Місце:</strong> Миколаїв, Україна<br />
      <strong>Сонце:</strong> Стрілець ♐<br />
      <strong>Місяць:</strong> Скорпіон ♏<br />
      <strong>Асцендент:</strong> Діва ♍
    </p>

    <div className="aspect">
      <h3>☉ Сонце в Стрільці</h3>
      <p>Оптиміст, шукач істини. Людина з відкритим поглядом на світ, філософським мисленням, захоплена подорожами й ідеями.</p>
    </div>

    <div className="aspect">
      <h3>☽ Місяць у Скорпіоні</h3>
      <p>Глибока емоційність, інтенсивність, інтуїція. Людина часто приховує справжні почуття, але переживає глибоко і пристрасно.</p>
    </div>

    <div className="aspect">
      <h3>↑ Асцендент у Діві</h3>
      <p>Зовнішній вигляд стриманий і організований. Людина здається уважною до деталей, розумною, з раціональним підходом до життя.</p>
    </div>

    <h2>Короткий аналіз</h2>
    <p>
      Комбінація Сонця в Стрільці та Місяця в Скорпіоні формує особистість із сильним внутрішнім світом і відкритим мисленням.
      Асцендент у Діві додає аналітичності, що робить цю людину глибокою, але логічною — здатною бачити суть речей і прагнути до істини.
    </p>
    </div>
  );
};
export {NatalChart};
