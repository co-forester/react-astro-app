import React, { useState } from 'react';
import axios from 'axios';
import css from './GenerateChartForm.module.css';

const GenerateChartForm = () => {
  const [form, setForm] = useState({ date: '', time: '', place: '' });
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.REACT_APP_API_URL || '';
  if (!API_URL) {
    console.warn("⚠️ REACT_APP_API_URL is not set!");
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setImageUrl(null);

    try {
      const response = await axios.post(`${API_URL}/generate`, form);
      const imageUrl = `${API_URL}${response.data.chart_image_url}`;
      setImageUrl(imageUrl);
    } catch (err: any) {
      const message = err?.response?.data?.error || 'Помилка запиту';
      setError(message);
    }
  };

  return (
    <div className={css.wrapper}>
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
        <input
          name="place"
          type="text"
          value={form.place}
          onChange={handleChange}
          placeholder="Київ"
          required
          className={css.input}
        />
        <button type="submit" className={css.button}>
          Згенерувати карту
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