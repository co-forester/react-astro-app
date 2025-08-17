import React, { useState, useEffect } from 'react';
import axios from 'axios';
import css from './forecastAugust2025.module.css';
import { useAppSelector, useAppDispatch } from '../../hooks/reduxHook';
import { themeActions } from '../../redux/slices/themeSlice';
import { ForecastWeek } from '../ForecastWeek';

interface FormState {
  date: string;
  time: string;
  place: string;
}

const ForecastAugust2025: React.FC = () => {
  const theme = useAppSelector((state) => state.theme.theme);
  const dispatch = useAppDispatch();

  const [form, setForm] = useState<FormState>({ date: '', time: '', place: '' });
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light' || savedTheme === 'dark') {
      dispatch(themeActions.setTheme(savedTheme === 'light'));
    } else {
      dispatch(themeActions.setTheme(true));
    }
  }, [dispatch]);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setImageUrl(null);

    if (!form.date || !form.time || !form.place) {
      setError('Заповніть усі поля!');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/generate`, form);
      if (response.data.status === 'success') {
        setImageUrl(`${API_URL}${response.data.chart_image_url}`);
      } else {
        setError('Не вдалося згенерувати карту');
      }
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Сталася помилка при запиті');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={theme ? css.containerLight : css.containerDark}>
      <h1>Прогноз на серпень 2025</h1>

      <div className={css.formBlock}>
        <h2>Введіть ваші дані для натальної карти</h2>
        <form onSubmit={handleSubmit} className={css.form}>
          <input
            type="date"
            name="date"
            value={form.date}
            onChange={handleChange}
            required
            className={css.input}
          />
          <input
            type="time"
            name="time"
            value={form.time}
            onChange={handleChange}
            required
            className={css.input}
          />
          <input
            type="text"
            name="place"
            value={form.place}
            onChange={handleChange}
            placeholder="Київ"
            required
            className={css.input}
          />
          <button type="submit" className={theme ? css.buttonLight : css.buttonDark} disabled={loading}>
            {loading ? 'Завантаження...' : 'Згенерувати карту'}
          </button>
        </form>
        {error && <p className={css.error}>{error}</p>}
      </div>

      {imageUrl && (
        <div className={css.result}>
          <h2>Ваша натальна карта</h2>
          <img src={imageUrl} alt="Натальна карта" className={css.image} />
        </div>
      )}

      <ForecastWeek title="Загальна тенденція місяця" theme={theme}>
        Серпень стане часом переоцінки цілей і зміцнення внутрішньої стійкості.
        Завершуйте старі справи, щоб звільнити місце для нового. Довіряйте інтуїції.
      </ForecastWeek>

      <ForecastWeek title="1–7 серпня" theme={theme}>
        Перша неділя подарує відчуття оновлення. Ідеї, що давно чекали реалізації, можуть з’явитися.
      </ForecastWeek>

      <ForecastWeek title="8–14 серпня" theme={theme}>
        Увага до фінансів та побутових питань. Можливі несподівані витрати, але для покращення життя.
      </ForecastWeek>

      <ForecastWeek title="15–21 серпня" theme={theme}>
        Час емоційної чутливості. Важливо зберігати гармонію у відносинах та уникати драми.
      </ForecastWeek>

      <ForecastWeek title="22–31 серпня" theme={theme}>
        Кінець місяця відкриє нові горизонти. Можливі пропозиції щодо поїздок або навчання.
      </ForecastWeek>
    </div>
  );
};

export { ForecastAugust2025 };