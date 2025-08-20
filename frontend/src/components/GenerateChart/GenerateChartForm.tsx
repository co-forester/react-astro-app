// ChartGenerator.tsx
import React, { useState } from 'react';
import axios from 'axios';

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
    <div style={{ textAlign: 'center', padding: '2rem' }}>
      <h2>Генератор натальної карти</h2>
      <div style={{ margin: '1rem' }}>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          style={{ marginRight: '0.5rem' }}
        />
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          style={{ marginRight: '0.5rem' }}
        />
        <input
          type="text"
          placeholder="Місце"
          value={place}
          onChange={(e) => setPlace(e.target.value)}
        />
      </div>
      <button onClick={generateChart} disabled={loading}>
        {loading ? 'Генеруємо...' : 'Згенерувати'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {chartUrl && (
        <div style={{ marginTop: '2rem' }}>
          <img src={`http://localhost:8080${chartUrl}`} alt="Натальна карта" />
        </div>
      )}
    </div>
  );
};

export {GenerateChartForm};