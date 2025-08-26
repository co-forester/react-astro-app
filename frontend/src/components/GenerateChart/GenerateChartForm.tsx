import React, { useState } from "react";
import css from "./GenerateChartForm.module.css";

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
  const [aspectsHtml, setAspectsHtml] = useState<string | null>(null);
  const [rawResponse, setRawResponse] = useState<any>(null);
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
    setAspectsHtml(null);
    setRawResponse(null);

    try {
      const response = await fetch("https://albireo-daria-96.fly.dev/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      setRawResponse(data);

      if (!response.ok) {
        throw new Error(data.error || "Помилка генерації карти");
      }

      // Твій оригінальний URL без змін
      const url = `https://albireo-daria-96.fly.dev${data.chart_image_url}`;
      setChartUrl(url);

      if (data.aspects_table_html) {
        setAspectsHtml(data.aspects_table_html);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`${css.formContainer} ${css.fadeInForm}`}>
      <form onSubmit={handleSubmit} className={css.form}>
        <input
          type="text"
          name="firstName"
          value={formData.firstName}
          onChange={handleChange}
          className={css.formInput}
          placeholder="Ім'я"
          required
        />
        <input
          type="text"
          name="lastName"
          value={formData.lastName}
          onChange={handleChange}
          className={css.formInput}
          placeholder="Прізвище"
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
          {loading ? "Генерація..." : "Побудувати натальну карту"}
        </button>
      </form>

      {error && <p className={css.errorText}>{error}</p>}

      {chartUrl && (
        <div className={`${css.chartContainer} ${css.fadeInUpForm}`}>
          <img src={chartUrl} alt="Натальна карта" />
        </div>
      )}

      {aspectsHtml && (
        <div
          className={`${css.aspectsTable} ${css.fadeInUpForm}`}
          dangerouslySetInnerHTML={{ __html: aspectsHtml }}
        />
      )}

      {rawResponse && (
        <pre className={css.rawResponse}>
          {JSON.stringify(rawResponse, null, 2)}
        </pre>
      )}
    </div>
  );
};

export { GenerateChartForm };