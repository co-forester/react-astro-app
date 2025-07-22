import React, { useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

import css from './Footer.module.css'
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHook';
import { themeActions } from '../../redux/slices/themeSlice';
// import { store } from '../../redux/store';
// import { themeActions } from '../../redux/slices/themeSlice';

const Footer = () => {

  const theme = useAppSelector(state => state.theme.theme);
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
  
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
    
      <footer className={theme ? css.FooterLight : css.FooterDark}>
        
        <nav className={css.nav}>
          <NavLink
            to="/App/home"
            className={({ isActive }) => isActive ? css.activeLink : undefined}
          >
            Головна
          </NavLink>
          <NavLink
            to="/App/natal_chart"
            className={({ isActive }) => isActive ? css.activeLink : undefined}
          >
            Натальна карта
          </NavLink>
          <NavLink
            to="/App/forecast_august_2025"
            className={({ isActive }) => isActive ? css.activeLink : undefined}
          >
            Прогноз на серпень
          </NavLink>
        </nav>

         <h2>Контакти</h2>
        <div className={theme ? css.contactsLight : css.contactsLightDark}>
          <a href="mailto:bluemystickfantasy@gmail.com">📧 Email</a>
          <a href="https://t.me/dar_albireo">📨 Telegram</a>
          <a href="viber://chat?number=+380938991998">📱 Viber</a>
          <a href="https://instagram.com/dar_albireo">📷 Instagram</a>
          <a href="https://tiktok.com/@dar_albireo">🎥 TikTok</a>
          <a href="https://signal.group/#midgart">🔐 Signal</a>
        </div>
      
         <p>© 2025 Albireo — Астрологічні Прогнози</p>

      </footer>
    
  );
}
export {Footer};