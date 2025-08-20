// ChartGenerator.tsx
import React, { useState } from 'react';
import axios from 'axios';
import './ChartForm.css'; // сюди вставляєш CSS, який ти дав (fadeInForm, fadeInUpForm, formContainer, etc.)

const GenerateChartForm = () => {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [place, setPlace] = useState('');
  const [chartUrl, setChartUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateChart = async () => {
    if (!date || !time || !place) {
      setError('Введіть дату, час та місце');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:8080/generate', {
        date,
        time,
        place
      });
      setChartUrl(res.data.chart_image_url);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Помилка генерації карти');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="formContainer fadeInForm" style={{ maxWidth: '500px', margin: '2rem auto' }}>
      <h2 className="fadeInUpForm" style={{ animationDelay: '0.1s' }}>Генератор натальної карти</h2>
      <div style={{ margin: '1rem 0', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <input
          className="formInput fadeInUpForm"
          style={{ animationDelay: '0.2s' }}
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <input
          className="formInput fadeInUpForm"
          style={{ animationDelay: '0.3s' }}
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
        />
        <input
          className="formInput fadeInUpForm"
          style={{ animationDelay: '0.4s' }}
          type="text"
          placeholder="Місце"
          value={place}
          onChange={(e) => setPlace(e.target.value)}
        />
      </div>
      <button
        className="formButton fadeInUpForm"
        style={{ animationDelay: '0.5s' }}
        onClick={generateChart}
        disabled={loading}
      >
        {loading ? 'Генеруємо...' : 'Згенерувати'}
      </button>
      {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}
      {chartUrl && (
        <div className="fadeInUpForm" style={{ animationDelay: '0.6s', marginTop: '2rem' }}>
          <img src={`http://localhost:8080${chartUrl}`} alt="Натальна карта" style={{ width: '100%' }} />
        </div>
      )}
    </div>
  );
};

export { GenerateChartForm };