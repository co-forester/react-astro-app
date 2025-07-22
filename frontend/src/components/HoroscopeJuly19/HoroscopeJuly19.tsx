
import React, { useEffect } from 'react';

import css from'./horoscopeJuly19.module.css';
import { themeActions } from '../../redux/slices/themeSlice';
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHook';

 

const HoroscopeJuly19 = () => {
  const theme = useAppSelector(state => state.theme.theme);
    const dispatch = useAppDispatch();
    
  
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
  <div>
  
  <main className={theme ? css.mainLight : css.mainDark}>
    <h2>Гороскоп на 19 липня 2025 року</h2>

    <h2>♈ Овен</h2>
    <p>Цей день ідеальний для прийняття рішень — інтуїція на висоті. Слухай серце.</p>

    <h2>♉ Телець</h2>
    <p>Фокус на фінансах. Утримайся від імпульсивних покупок, краще склади бюджет.</p>

    <h2>♊ Близнюки</h2>
    <p>Можливі нові знайомства або незвичні події. Будь відкритим — день обіцяє сюрпризи.</p>
    <h2>♋ Рак</h2>
    <p>Настав час подумати про себе. День сприятливий для творчості та відпочинку.</p>

    <h2>♌ Лев</h2>
    <p>Харизма на максимумі. Скористайся шансом виступити або проявити лідерство.</p>

    <h2>♍ Діва</h2>
    <p>Наведення порядку — як внутрішнього, так і зовнішнього — принесе задоволення.</p>

    <h2>♎ Терези</h2>
    <p>День гармонії. Успіх у переговорах, якщо збережеш баланс між словами й емоціями.</p>

    <h2>♏ Скорпіон</h2>
    <p>Висока емоційність. Варто стримувати імпульси, щоб не ускладнити ситуації.</p>

    <h2>♐ Стрілець</h2>
    <p>Новий погляд на стару ситуацію. Можливі приємні новини здалеку.</p>

    <h2>♑ Козеріг</h2>
    <p>Успіхи в роботі або проекті, якщо залишишся зосередженим. Вечір — для відновлення.</p>

    <h2>♒ Водолій</h2>
    <p>Ідеї просто фонтанують — запиши їх. День творчий, спілкуйся з однодумцями.</p>

    <h2>♓ Риби</h2>
    <p>Зверни увагу на сни або символи. Вони можуть нести підказку для важливого рішення.</p>
  </main>

 
  </div>
 );
};
export {HoroscopeJuly19};