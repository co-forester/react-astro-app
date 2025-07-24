
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
    <h2>Гороскоп на 28 августа 2025 года</h2>

    <h2>♈ Овен</h2>
    <p>Интуиция поможет принять важные решения. Следуйте внутреннему голосу.</p>

    <h2>♉ Телец</h2>
    <p>Финансовые вопросы потребуют внимания. Избегайте необдуманных трат.</p>

    <h2>♊ Близнецы</h2>
    <p>День общения и новостей. Возможны интересные предложения или встречи.</p>

    <h2>♋ Рак</h2>
    <p>Время сосредоточиться на себе. Займитесь творчеством или отдохните душой.</p>

    <h2>♌ Лев</h2>
    <p>Ваша энергия и уверенность привлекут внимание. Подходящий день для выступлений.</p>

    <h2>♍ Дева</h2>
    <p>Организованность принесёт плоды. Наведите порядок в делах и мыслях.</p>

    <h2>♎ Весы</h2>
    <p>Благоприятный день для переговоров и поиска баланса в отношениях.</p>

    <h2>♏ Скорпион</h2>
    <p>Эмоции на подъёме. Постарайтесь держать их под контролем и не принимать решений в порыве.</p>

    <h2>♐ Стрелец</h2>
    <p>Откроются новые горизонты. День подходит для планирования путешествий и новых начинаний.</p>

    <h2>♑ Козерог</h2>
    <p>Плодотворный день для работы. Главное — не упустить детали и сохранить фокус.</p>

    <h2>♒ Водолей</h2>
    <p>Творческие идеи требуют реализации. Окружите себя вдохновляющими людьми.</p>

    <h2>♓ Рыбы</h2>
    <p>Обратите внимание на подсказки судьбы. Сны или знаки могут указать верный путь.</p>
  </main>

</div>
 );
};
export {HoroscopeJuly19};