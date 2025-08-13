import { useAppSelector } from '../../hooks/reduxHook';
import css from './forecastAugust2025.module.css';
import { ForecastWeek } from '../ForecastWeek/ForecastWeek';
import { useState } from 'react';

const ForecastAugust2025 = () => {
  const theme = useAppSelector(state => state.theme.theme);

  // Динамічна дата і знак
  const [birthDate, setBirthDate] = useState('1974-03-05');
  const [sign, setSign] = useState('Рыбы');

  return (
    <div className={theme ? css.containerLight : css.containerDark}>
      <h1>Прогноз на август 2025</h1>

      <div style={{ marginBottom: '1rem' }}>
        <label>
          Введите дату рождения: 
          <input
            type="date"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            style={{ marginLeft: '0.5rem' }}
          />
        </label>
        {/* Тут можна додати логіку автоматичного визначення знака */}
      </div>

      <h2>Индивидуальный прогноз на август 2025</h2>
      <p style={{ textAlign: 'center' }}>
        Дата рождения: <strong>{birthDate}</strong> | Знак: <strong>{sign}</strong>
      </p>

      <h2>Общая тенденция месяца</h2>
      <p>
        Август станет временем переоценки целей и укрепления внутренней устойчивости. 
        Завершайте старые дела и доверяйте интуиции.
      </p>

      <ForecastWeek title="1–7 августа" theme={theme}>
        Первая неделя месяца подарит ощущение обновления...
      </ForecastWeek>

      <ForecastWeek title="8–14 августа" theme={theme}>
        Внимание к финансам и бытовым вопросам...
      </ForecastWeek>

      <ForecastWeek title="15–21 августа" theme={theme}>
        Эмоциональная чувствительность, гармония с близкими...
      </ForecastWeek>

      <ForecastWeek title="22–31 августа" theme={theme}>
        Новые горизонты: поездки, обучение, творчество...
      </ForecastWeek>

      <h2>Совет месяца</h2>
      <p>Слушайте интуицию и отпускайте то, что тянет назад.</p>
    </div>
  );
};

export { ForecastAugust2025 };