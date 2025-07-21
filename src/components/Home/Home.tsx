import React from 'react';

import css from './home.module.css';
import { useAppSelector } from '../../hooks/reduxHook';
import GenerateChartForm from '../GenerateChart/GenerateChartForm';


const Home = () => {
   const theme = useAppSelector(state => state.theme.theme);
  return (
    
    <div>

      <main  className={theme ? css.HomeLight : css.HomeDark}>

        <h2>Послуги</h2>
        <p>Пропоную <span className="highlight">натальні карти</span>, індивідуальні прогнози та астрологічний супровід.</p>
        <p>Звертайтесь для глибокого розуміння себе, вибору життєвого шляху та вирішення важливих питань.</p>
         <div>
      <h1>Створення натальної карти</h1>
      <GenerateChartForm />
    </div>
      </main>

    </div>
  );
};

export {Home};
