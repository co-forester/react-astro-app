// src/components/GenerateChart/GenerateChartForm.tsx
import React, { useState } from "react";
import css from "./GenerateChartForm.module.css";

// Експортуємо тип, щоб Home.tsx міг його використовувати
export interface FormData {
  name: string;
  date: string;
  time: string;
  place: string;
}

// Типи для пропсів
interface GenerateChartFormProps {
  onSubmit: (formData: FormData) => void;
  loading: boolean;
}

const GenerateChartForm: React.FC<GenerateChartFormProps> = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState<FormData>({
    name: "Дар'я",
    date: "1996-11-09",
    time: "06:00",
    place: "Миколаїв",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData); // Просто викликаємо функцію, передану з батька
  };

  return (
    <div className={css.formContainer}>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className={css.formInput}
          placeholder="Ім'я"
          required
        />
        <input
          type="date"
          name="date"
          value={formData.date}
          onChange={handleChange}
          className={css.formInput}
          required
        />
        <input
          type="time"
          name="time"
          value={formData.time}
          onChange={handleChange}
          className={css.formInput}
          required
        />
        <input
          type="text"
          name="place"
          value={formData.place}
          onChange={handleChange}
          className={css.formInput}
          placeholder="Місто"
          required
        />
        <button type="submit" className={css.formButton} disabled={loading}>
          {loading ? "Аналізуємо космограму..." : "Побудувати та інтерпретувати"}
        </button>
      </form>
    </div>
  );
};

export { GenerateChartForm };