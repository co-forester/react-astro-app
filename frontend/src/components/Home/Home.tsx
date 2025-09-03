import React, { FC, useEffect, useState } from 'react';
import css from './home.module.css';
import { useAppSelector } from '../../hooks/reduxHook';
import { GenerateChartForm } from '../GenerateChart/GenerateChartForm';
import { EclipsesOverview } from '../EclipsesOverview/EclipsesOverview';
import { HoroscopeJuly19 } from '../HoroscopeJuly19/HoroscopeJuly19';
import { ChildHoroscope } from '../ChildHoroscope/ChildHoroscope';
import { NatalChartAnalysis } from '../NatalChartAnalysis/NatalChartAnalysis';
import { ChartSVG } from '../ChartSVG';

interface RootState {
  theme: {
    theme: boolean;
  };
}

const Home: FC = () => {
  const theme = useAppSelector((state: RootState) => state.theme.theme);

  const [planets, setPlanets] = useState<any[]>([]);
  const [aspects, setAspects] = useState<any[]>([]);

  const handleChartData = (data: { planets: any[]; aspects: any[] }) => {
    setPlanets(data.planets);
    setAspects(data.aspects);
  };

  // Для анімації появи
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setLoaded(true), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={`${theme ? css.mainLight : css.mainDark} ${loaded ? css.fadeIn : ''}`}>
      <div className={css.gridContainer}>
        {/* Лівий блок */}
        <aside className={`${css.leftBlock} ${loaded ? css.fadeInUp : ''}`}>
          <EclipsesOverview />
        </aside>

        {/* Основний контент */}
        <main className={`${css.content} ${loaded ? css.fadeInUp : ''}`}>
          <div className={css.intro}>
            <h2>Услуги</h2>
            <p>
              Предлагаю <span className="highlight">натальные карты</span>, гороскоп ребенка, аналіз натальної карты, индивидуальные прогнозы и астрологическое сопровождение.
            </p>
            <p>
              Обращайтесь для глубокого понимания себя, выбора жизненного пути и решения важных вопросов.
            </p>
          </div>

          {/* Форма генерації карти */}
          <GenerateChartForm onDataReady={handleChartData} />

          {/* Натальная карта тільки якщо дані прийшли */}
          {planets.length > 0 && aspects.length > 0 && (
            <ChartSVG planets={planets} aspects={aspects} />
          )}

          <NatalChartAnalysis />
          <ChildHoroscope />
        </main>

        {/* Бокова панель */}
        <aside className={`${css.sidebar} ${loaded ? css.fadeInUp : ''}`}>
          <HoroscopeJuly19 />
        </aside>
      </div>
    </div>
  );
};

export { Home };