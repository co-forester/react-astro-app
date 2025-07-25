import React from 'react';

import css from './home.module.css';
import { useAppSelector } from '../../hooks/reduxHook';
import GenerateChartForm from '../GenerateChart/GenerateChartForm';
import { EclipsesOverview } from '../EclipsesOverview/EclipsesOverview';
import { HoroscopeJuly19 } from '../HoroscopeJuly19/HoroscopeJuly19';
import { ChildHoroscope } from '../ChildHoroscope/ChildHoroscope';
import { NatalChartAnalysis } from '../NatalChartAnalysis/NatalChartAnalysis';

const Home = () => {
  const theme = useAppSelector((state) => state.theme.theme);

  return (
    <div className={theme ? css.mainLight : css.mainDark}>
      <div className={css.gridContainer}>
        <aside className={css.leftBlock}>
          <EclipsesOverview />
        </aside>

        <main className={css.content}>
          <GenerateChartForm />
          <NatalChartAnalysis />
          <ChildHoroscope />
        </main>

        <aside className={css.sidebar}>
          <HoroscopeJuly19 />
        </aside>
      </div>
    </div>
  );
};

export { Home };