import React, { useState, useEffect } from 'react';
import axios from 'axios';

import css from './GenerateChartForm.module.css';
import { themeActions } from '../../redux/slices/themeSlice';
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHook';

const GenerateChartForm = () => {
  const theme = useAppSelector((state) => state.theme.theme);
  const [form, setForm] = useState({ date: '', time: '', place: '' });
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const dispatch = useAppDispatch();

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light' || savedTheme === 'dark') {
      dispatch(themeActions.setTheme(savedTheme === 'light'));
    } else {
      dispatch(themeActions.setTheme(true));
    }
  }, [dispatch]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const API_URL = process.env.REACT_APP_API_URL || '';
  if (!API_URL) {
    console.warn("⚠️ REACT_APP_API_URL is not set!");
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setImageUrl(null);
    setError(null);

    if (e.target.name === 'place' && e.target.value.length > 1) {
      fetchPlaceSuggestions(e.target.value);
    } else {
      setSuggestions([]);
    }
  };

  const fetchPlaceSuggestions = async (query: string) => {
    try {
      const res = await axios.get('https://nominatim.openstreetmap.org/search', {
        params: { q: query, format: 'json', addressdetails: 1, limit: 5 },
      });
      const places = res.data.map((item: any) => item.display_name);
      setSuggestions(places);
    } catch (err) {
      console.warn('Помилка отримання підказок місця', err);
      setSuggestions([]);
    }
  };

  const selectSuggestion = (place: string) => {
    setForm({ ...form, place });
    setSuggestions([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setImageUrl(null);
    setLoading(true);

    if (!form.place) {
      setError('Будь ласка, введіть місто');
      setLoading(false);
      return;
    }

    try {
      const [year, month, day] = form.date.split('-').map(Number);
      const [hour, minute] = form.time.split(':').map(Number);

      const payload = { year, month, day, hour, minute, place: form.place };
      const response = await axios.post(`${API_URL}/generate`, payload);

      if (response.data?.chart) {
        setImageUrl(`${API_URL}${response.data.chart}`);
      } else {
        setError('Сервер не повернув зображення карти');
      }
    } catch (err: any) {
      const message =
        err?.response?.data?.error ||
        err?.message ||
        'Невідома помилка під час генерації карти';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={css.wrapper}>
      <h1>Створення натальної карти</h1>

      <form onSubmit={handleSubmit} className={css.form}>
        <input
          name="date"
          type="date"
          value={form.date}
          onChange={handleChange}
          required
          className={css.input}
        />
        <input
          name="time"
          type="time"
          value={form.time}
          onChange={handleChange}
          required
          className={css.input}
        />
        <div className={css.autocompleteWrapper}>
          <input
            name="place"
            type="text"
            value={form.place}
            onChange={handleChange}
            placeholder="Київ"
            required
            className={css.input}
            autoComplete="off"
          />
          {suggestions.length > 0 && (
            <ul className={css.suggestions}>
              {suggestions.map((place, i) => (
                <li key={i} onClick={() => selectSuggestion(place)}>
                  {place}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button
          type="submit"
          className={theme ? css.buttonLight : css.buttonDark}
          disabled={loading}
        >
          {loading ? 'Генеруємо...' : 'Згенерувати карту'}
        </button>
      </form>

      {error && <p className={css.error}>{error}</p>}

      {imageUrl && (
        <div className={css.result}>
          <h2 className={css.title}>Натальна карта</h2>
          <img src={imageUrl} alt="Натальна карта" className={css.image} />
        </div>
      )}
    </div>
  );
};

export default GenerateChartForm;