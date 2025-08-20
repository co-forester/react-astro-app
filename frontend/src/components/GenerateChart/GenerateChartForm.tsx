// ChartGenerator.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import tzlookup from 'tz-lookup';
import './GenerateChartForm.module.css';

const BACKEND_URL = 'https://albireo-daria-96.fly.dev';
const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search';

const GenerateChartForm = () => {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [city, setCity] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [chartUrl, setChartUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [timezone, setTimezone] = useState('');

  // Завантажуємо останнє місто з localStorage
  useEffect(() => {
    const lastCity = localStorage.getItem('lastCity');
    if (lastCity) {
      selectCity(lastCity);
    }
  }, []);

  // Автопідказки для міста
  const fetchCitySuggestions = async (query: string) => {
    if (!query) {
      setSuggestions([]);
      return;
    }
    try {
      const res = await axios.get(NOMINATIM_URL, {
        params: { q: query, format: 'json', limit: 5 },
      });

      const places = res.data.map((p: any) => p.display_name);
      setSuggestions(places);

      // Автовибір першого варіанту
      if (places.length > 0) {
        selectCity(places[0]);
      }
    } catch (err) {
      console.error('Помилка автопідказки:', err);
    }
  };

  // Вибір міста
  const selectCity = async (selection: string) => {
    setCity(selection);
    setSuggestions([]);
    localStorage.setItem('lastCity', selection); // Запам’ятовуємо місто

    try {
      const res = await axios.get(NOMINATIM_URL, {
        params: { q: selection, format: 'json', limit: 1 },
      });

      if (res.data.length > 0) {
        const lat = parseFloat(res.data[0].lat);
        const lon = parseFloat(res.data[0].lon);
        setCoords({ lat, lon });

        const tz = tzlookup(lat, lon);
        setTimezone(tz);
      }
    } catch (err) {
      console.error('Помилка визначення координат/часової зони:', err);
    }
  };

  const generateChart = async () => {
    if (!date || !time || !coords || !timezone) {
      setError('Введіть дату, час та місто');
      return;
    }
    setLoading(true);
    setError('');
    setChartUrl('');

    try {
      const res = await axios.post(`${BACKEND_URL}/generate`, {
        date,
        time,
        place: city,
        latitude: coords.lat,
        longitude: coords.lon,
        timezone,
      });

      if (!res.data.chart_image_url) {
        setError('Не вдалося отримати картинку натальної карти');
      } else {
        setChartUrl(`${BACKEND_URL}${res.data.chart_image_url}`);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Помилка генерації карти');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="formContainer fadeInForm" style={{ maxWidth: '500px', margin: '2rem auto' }}>
      <h2 className="fadeInUpForm" style={{ animationDelay: '0.1s' }}>
        Генератор натальної карти
      </h2>

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
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            className="formInput fadeInUpForm"
            style={{ animationDelay: '0.4s' }}
            type="text"
            placeholder="Місто"
            value={city}
            onChange={(e) => {
              setCity(e.target.value);
              fetchCitySuggestions(e.target.value);
            }}
          />
          {suggestions.length > 0 && (
            <ul
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                background: '#fff',
                border: '1px solid #ccc',
                maxHeight: '150px',
                overflowY: 'auto',
                zIndex: 10,
                margin: 0,
                padding: 0,
                listStyle: 'none',
              }}
            >
              {suggestions.map((s, idx) => (
                <li
                  key={idx}
                  style={{ padding: '0.5rem', cursor: 'pointer' }}
                  onClick={() => selectCity(s)}
                >
                  {s}
                </li>
              ))}
            </ul>
          )}
        </div>
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
        <div
          className="fadeInUpForm"
          style={{
            animationDelay: '0.6s',
            marginTop: '2rem',
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: '300px',
              height: '300px',
              borderRadius: '50%',
              overflow: 'hidden',
              boxShadow: '0 8px 20px rgba(0,0,0,0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#fff',
              transition: 'transform 0.3s',
            }}
          >
            <img
              src={chartUrl}
              alt="Натальна карта"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export { GenerateChartForm };