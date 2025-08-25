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
          <img src={chartUrl} alt="Натальна карта" />
        </div>
      )}

      {aspectsHtml && (
        <div
          className="aspectsTable fadeInUpForm"
          dangerouslySetInnerHTML={{ __html: aspectsHtml }}
        />
      )}

      {rawResponse && (
        <pre style={{ marginTop: "1rem", fontSize: "0.8rem", color: "#aaa" }}>
          {JSON.stringify(rawResponse, null, 2)}
        </pre>
      )}
    </div>
  );
};

export { GenerateChartForm };