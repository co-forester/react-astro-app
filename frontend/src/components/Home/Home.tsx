import React from 'react';

import css from './home.module.css';
import { useAppSelector } from '../../hooks/reduxHook';
import GenerateChartForm from '../GenerateChart/GenerateChartForm';
import { EclipsesOverview } from '../EclipsesOverview/EclipsesOverview';

const Home = () => {
  const theme = useAppSelector(state => state.theme.theme);

  return (
    <div className={theme ? css.wrapperLight : css.wrapperDark}>
      <aside className={css.eclipsesBlock}>
        <EclipsesOverview />
      </aside>

      <main className={theme ? css.HomeLight : css.HomeDark}>
        <h2>Услуги</h2>
        <p>
          Предлагаю <span className="highlight">натальные карты</span>, гороскоп ребенка, аналіз натальной карти, индивидуальные прогнозы и астрологическое сопровождение.
        </p>
        <p>
          Обращайтесь для глубокого понимания себя, выбора жизненного пути и решения важных вопросов.
        </p>
        <div>
          <h1>Создание натальной карты</h1>
          <GenerateChartForm />
        </div>
      </main>
    </div>
  );
};

export { Home };