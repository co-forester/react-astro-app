import React, { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHook';
import { themeActions } from '../../redux/slices/themeSlice';
import css from './Header.module.css';
import logo from '../../images/image.png';

const Header = () => {
  const theme = useAppSelector(state => state.theme.theme);
  const dispatch = useAppDispatch();

  const switchTheme = () => {
    dispatch(themeActions.themeChange());
  };

  // Автоматичне завантаження теми з localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      dispatch(themeActions.setTheme(savedTheme === 'light'));
    }
  }, [dispatch]);

  // Збереження теми у localStorage
  useEffect(() => {
    localStorage.setItem('theme', theme ? 'light' : 'dark');
  }, [theme]);

  return (
    <header className={theme ? css.HeaderLight : css.HeaderDark}>
       <img
        src={logo}
        alt="Логотип Альбірео"
        className={css.logo}
        onClick={switchTheme}
       />

        <div className={css.logoTitleWrapper}>
          <h1>Дарья Альбирео</h1>
          <h5> астрологические прогнозы </h5>

          <nav className={css.nav}>
           <NavLink to="/App/home" className={({ isActive }) => isActive ? css.activeLink : undefined}>Услуги</NavLink>
           <NavLink to="/App/natal_chart" className={({ isActive }) => isActive ? css.activeLink : undefined}>Натальная карта</NavLink>
           <NavLink to="/App/forecast_august_2025" className={({ isActive }) => isActive ? css.activeLink : undefined}>Прогноз на август</NavLink>
           <NavLink to="/App/natal_chart_analysis" className={({ isActive }) => isActive ? css.activeLink : undefined}>Анализ натальной карты</NavLink>
           <NavLink to="/App/child_horoscope" className={({ isActive }) => isActive ? css.activeLink : undefined}>гороскоп ребенка</NavLink>
          </nav>

        </div>

      <div className={css.ButtonBox}>
        {/* <button
          className={theme ? css.buttonLight : css.buttonDark}
          onClick={switchTheme}
        >
          {theme ? 'Theme dark' : 'Theme light'}
        </button> */}

        <div className={css.specialLinkContainer}>
          <NavLink
            to="/App/horoscope_july19"
            className={({ isActive }) => isActive ? css.activeLink : undefined}
          >
            🟢 Прогноз на 28 августа
          </NavLink>
        </div>
      </div>
    </header>
  );
};

export { Header };