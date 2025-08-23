import React, { useState } from 'react';
import './GenerateChartForm.module.css';

const GenerateChartForm: React.FC = () => {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [place, setPlace] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!date || !time || !place) {
      alert('Будь ласка, заповніть всі поля');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('https://<твоє-доменне-ім’я>/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, time, place }),
      });

      if (!response.ok) {
        const err = await response.json();
        alert(err.error || 'Помилка на сервері');
        setLoading(false);
        return;
      }

      const data = await response.json();
      setResult(data.chart_image_url);
    } catch (error) {
      alert('Помилка з’єднання з сервером');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="formContainer fadeInForm" onSubmit={handleSubmit}>
      <input
        className="formInput"
        type="date"
        value={date}
        onChange={(e) => setDate(e.target.value)}
        placeholder="Дата народження"
        required
      />
      <input
        className="formInput"
        type="time"
        value={time}
        onChange={(e) => setTime(e.target.value)}
        placeholder="Час народження"
        required
      />
      <input
        className="formInput"
        type="text"
        value={place}
        onChange={(e) => setPlace(e.target.value)}
        placeholder="Місто народження"
        required
      />
      <button className="formButton" type="submit" disabled={loading}>
        {loading ? 'Генеруємо...' : 'Згенерувати карту'}
      </button>

      {result && (
        <div style={{ marginTop: '1rem', textAlign: 'center' }}>
          <img src={result} alt="Натальна карта" style={{ maxWidth: '100%' }} />
        </div>
      )}
    </form>
  );
};

export {GenerateChartForm};