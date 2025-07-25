import React, { useEffect } from 'react';
import css from './EclipsesOverview.module.css';
import { themeActions } from '../../redux/slices/themeSlice';
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHook';

interface Eclipse {
  date: string;
  type: string;
  visibility: string;
}

const eclipses: Eclipse[] = [
  { date: '2025-03-14', type: 'Часткове Сонячне 🌒', visibility: 'Північна Європа, Азія' },
  { date: '2025-03-29', type: 'Повне Місячне 🌕', visibility: 'Азія, Австралія, Америка' },
  { date: '2025-09-07', type: 'Повне Сонячне 🌞', visibility: 'Африка, Атлантика' },
  { date: '2025-09-21', type: 'Часткове Місячне 🌓', visibility: 'Європа, Азія' },
  { date: '2026-02-17', type: 'Повне Місячне 🌕', visibility: 'Америка, Африка, Європа' },
  { date: '2026-03-03', type: 'Повне Сонячне 🌞', visibility: 'Південна Америка, Атлантика' },
  { date: '2026-08-12', type: 'Часткове Місячне 🌓', visibility: 'Європа, Азія, Австралія' },
  { date: '2026-08-26', type: 'Повне Сонячне 🌞', visibility: 'Гренландія, Ісландія, Європа' }
];

export const EclipsesOverview = () => {

const theme = useAppSelector(state => state.theme.theme);
  const dispatch = useAppDispatch();

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light' || savedTheme === 'dark') {
      dispatch(themeActions.setTheme(savedTheme === 'light'));
    } else {
      dispatch(themeActions.setTheme(true));
    }
  }, [dispatch]);


  return (
    <div className={theme ? css.containerBlockLight : css.containerBlockDark}>
      <h3 className={css.title}>Затемнення 2025–2026</h3>
      <ul className={css.list}>
        {eclipses.map((eclipse, index) => (
          <li key={index} className={css.item}>
            <span className={css.date}>{eclipse.date}</span>
            <span className={css.type}>{eclipse.type}</span>
            <span className={css.visibility}>({eclipse.visibility})</span>
          </li>
        ))}
      </ul>
    </div>
  );
};