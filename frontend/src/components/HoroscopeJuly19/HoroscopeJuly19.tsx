
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
    <h2>Гороскоп на август 2025 года</h2>

    <h2>♈ Овен</h2>
    <p>Месяц для действий. Ваша энергия на пике — используйте её для новых начинаний.</p>

    <h2>♉ Телец</h2>
    <p>Финансовые вопросы выйдут на первый план. Будьте осмотрительны и не рискуйте зря.</p>

    <h2>♊ Близнецы</h2>
    <p>Много общения и идей. Подходящее время для обучения и кратких поездок.</p>

    <h2>♋ Рак</h2>
    <p>Сосредоточьтесь на доме и семье. Эмоциональная поддержка будет особенно важной.</p>

    <h2>♌ Лев</h2>
    <p>Вы в центре внимания. Отличное время для самовыражения и признания ваших заслуг.</p>

    <h2>♍ Дева</h2>
    <p>Подходит для наведения порядка — как в делах, так и в мыслях. Уделите время деталям.</p>

    <h2>♎ Весы</h2>
    <p>Партнёрские отношения на первом месте. Ищите компромиссы и будьте дипломатичны.</p>

    <h2>♏ Скорпион</h2>
    <p>Интуиция усилится. Следуйте внутреннему голосу, особенно в вопросах карьеры.</p>

    <h2>♐ Стрелец</h2>
    <p>Желание перемен нарастает. Путешествия и новые идеи принесут вдохновение.</p>

    <h2>♑ Козерог</h2>
    <p>Хорошее время для профессионального роста. Будьте настойчивы — результат не заставит ждать.</p>

    <h2>♒ Водолей</h2>
    <p>Необычные события и новые знакомства откроют перед вами неожиданные перспективы.</p>

    <h2>♓ Рыбы</h2>
    <p>Месяц глубоких ощущений. Сны и интуиция подскажут верное направление.</p>
  </main>

</div>
 );
};
export {HoroscopeJuly19};