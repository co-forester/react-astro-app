import React, { useState, useEffect } from 'react';
import axios from 'axios';
import tzlookup from 'tz-lookup';
import './GenerateChartForm.module.css';

const BACKEND_URL = 'https://albireo-daria-96.fly.dev';

interface Suggestion {
  display_name: string;
  lat: number;
  lon: number;
}

const GenerateChartForm: React.FC = () => {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [city, setCity] = useState('');
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [timezone, setTimezone] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  // Автопідказки міст
  useEffect(() => {
    if (city.length > 2) {
      axios
        .get(`https://nominatim.openstreetmap.org/search?format=json&q=${city}`)
        .then((res) => {
          const data = res.data.map((item: any) => ({
            display_name: item.display_name,
            lat: parseFloat(item.lat),
            lon: parseFloat(item.lon),
          }));
          setSuggestions(data);
        })
        .catch((err) => console.error('Помилка пошуку міста:', err));
    } else {
      setSuggestions([]);
    }
  }, [city]);

  const handleSuggestionClick = (suggestion: Suggestion) => {
    setCity(suggestion.display_name);
    setLatitude(suggestion.lat);
    setLongitude(suggestion.lon);
    setTimezone(tzlookup(suggestion.lat, suggestion.lon));
    setSuggestions([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    let finalLatitude = latitude;
    let finalLongitude = longitude;
    let finalTimezone = timezone;

    // Якщо користувач нічого не обрав — беремо перший варіант
    if ((!latitude || !longitude || !timezone) && suggestions.length > 0) {
      const first = suggestions[0];
      finalLatitude = first.lat;
      finalLongitude = first.lon;
      finalTimezone = tzlookup(first.lat, first.lon);
      setLatitude(first.lat);
      setLongitude(first.lon);
      setTimezone(finalTimezone);
      setCity(first.display_name);
    }

    if (!finalLatitude || !finalLongitude || !finalTimezone) {
      alert('Будь ласка, оберіть місто зі списку підказок');
      return;
    }

    try {
      const res = await axios.post(`${BACKEND_URL}/generate`, {
        date,
        time,
        city,
        latitude: finalLatitude,
        longitude: finalLongitude,
        timezone: finalTimezone,
      });
      console.log('Відповідь сервера:', res.data);
    } catch (err) {
      console.error('Помилка генерації карти:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form">
      <div>
        <label>Дата:</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
        />
      </div>

      <div>
        <label>Час:</label>
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          required
        />
      </div>

      <div style={{ position: 'relative' }}>
        <label>Місто:</label>
        <input
          type="text"
          value={city}
          onChange={(e) => {
            setCity(e.target.value);
            setLatitude(null);
            setLongitude(null);
            setTimezone(null);
          }}
          required
        />
        {suggestions.length > 0 && (
          <ul className="suggestions">
            {suggestions.map((s, index) => (
              <li key={index} onClick={() => handleSuggestionClick(s)}>
                {s.display_name}
              </li>
            ))}
          </ul>
        )}
      </div>

      <button type="submit">Згенерувати карту</button>
    </form>
  );
};

export {GenerateChartForm};