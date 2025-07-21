import React, { useState } from 'react';
import axios from 'axios';

const GenerateChartForm = () => {
  const [form, setForm] = useState({ date: '', time: '', place: '' });
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setImageUrl(null);

    try {
      const response = await axios.post(
        'http://127.0.0.1:5000/generate',
        form,
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], { type: 'image/png' });
      const url = URL.createObjectURL(blob);
      setImageUrl(url);
    } catch (err: any) {
      const message = err?.response?.data?.error || 'Помилка запиту';
      setError(message);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input name="date" type="date" value={form.date} onChange={handleChange} required />
        <input name="time" type="time" value={form.time} onChange={handleChange} required />
        <input name="place" type="text" value={form.place} onChange={handleChange} placeholder="Київ" required />
        <button type="submit">Згенерувати карту</button>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}
      {imageUrl && (
        <div>
          <h2>Натальна карта</h2>
          <img src={imageUrl} alt="Натальна карта" />
        </div>
      )}
    </div>
  );
};

export default GenerateChartForm;