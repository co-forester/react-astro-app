import React, { useState } from "react";
import "./GenerateChartForm.module.css";

interface FormData {
  firstName: string;
  lastName: string;
  date: string;
  time: string;
  place: string;
}

const GenerateChartForm: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    firstName: "",
    lastName: "",
    date: "",
    time: "",
    place: "",
  });
  const [chartUrl, setChartUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setChartUrl(null);

    try {
      const response = await fetch("https://albireo-daria-96.fly.dev/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: `${formData.firstName} ${formData.lastName}`,
          date: formData.date,
          time: formData.time,
          place: formData.place,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Помилка генерації карти");
      }

      // ✅ Беремо готовий унікальний URL з бекенду
      setChartUrl(data.chart_url);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="formContainer fadeInForm">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="firstName"
          value={formData.firstName}
          onChange={handleChange}
          className="formInput"
          placeholder="Ім'я"
          required
        />
        <input
          type="text"
          name="lastName"
          value={formData.lastName}
          onChange={handleChange}
          className="formInput"
          placeholder="Прізвище"
          required
        />
        <input
          type="date"
          name="date"
          value={formData.date}
          onChange={handleChange}
          className="formInput"
          required
        />
        <input
          type="time"
          name="time"
          value={formData.time}
          onChange={handleChange}
          className="formInput"
          required
        />
        <input
          type="text"
          name="place"
          value={formData.place}
          onChange={handleChange}
          className="formInput"
          placeholder="Місто"
          required
        />
        <button type="submit" className="formButton" disabled={loading}>
          {loading ? "Генерація..." : "Побудувати натальну карту"}
        </button>
      </form>

      {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}

      {chartUrl && (
        <div className="chartContainer fadeInUpForm">
          <h3>Натальна карта</h3>
          <img src={chartUrl} alt="Натальна карта" />
        </div>
      )}
    </div>
  );
};

export { GenerateChartForm };