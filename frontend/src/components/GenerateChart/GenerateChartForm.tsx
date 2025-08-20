import React, { useState, useEffect } from 'react';
import axios from 'axios';
import css from './GenerateChartForm.module.css';
import { themeActions } from '../../redux/slices/themeSlice';
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHook';

interface FormData {
  date: string;
  time: string;
  place: string;
}

const GenerateChartForm: React.FC = () => {
  const theme = useAppSelector((state) => state.theme.theme);
  const [form, setForm] = useState<FormData>({ date: '', time: '', place: '' });
  const [chartImg, setChartImg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dispatch = useAppDispatch();

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    dispatch(themeActions.setTheme(savedTheme === 'light'));
  }, [dispatch]);

  const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8080';

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setChartImg(null);
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/generate`, form, { responseType: 'blob' });
      const imageUrl = URL.createObjectURL(response.data);
      setChartImg(imageUrl);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Помилка генерації карти');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={theme ? css.wrapperLight : css.wrapperDark}>
      <h1>Натальна карта Abireo Daria</h1>

      <form onSubmit={handleSubmit} className={css.form}>
        <input name="date" type="date" value={form.date} onChange={handleChange} required className={css.input} />
        <input name="time" type="time" value={form.time} onChange={handleChange} required className={css.input} />
        <input name="place" type="text" value={form.place} onChange={handleChange} placeholder="Місто" required className={css.input} />
        <button type="submit" className={theme ? css.buttonLight : css.buttonDark}>
          {loading ? 'Генерація...' : 'Згенерувати карту'}
        </button>
      </form>

      {error && <p className={css.error}>{error}</p>}

      {chartImg && (
        <div className={css.chartWrapper}>
          <div className={css.chartCircle}>
            <img src={chartImg} alt="Натальна карта" className={css.chartImage} />
            <div className={theme ? `${css.logoCircle} ${css.logoLight}` : `${css.logoCircle} ${css.logoDark}`}>
                       Abireo Daria
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export { GenerateChartForm };