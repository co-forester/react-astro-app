import React, { useState } from "react";
import css from "./GenerateChartForm.module.css"; // <- змінено

interface FormData {
  name: string;
  date: string;
  time: string;
  place: string;
}

const GenerateChartForm: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    name: "",
    date: "",
    time: "",
    place: "",
  });

  const ASPECT_ROW_COLORS: Record<string, string> = {
    trine: "#d4a5a5",       // світлий бордо
    square: "#8b8b8b",      // сірий
    opposition: "#4a0f1f",  // темний бордо
    sextile: "#f7eaea"      // білий/світлий бордо
  };

  const [chartUrl, setChartUrl] = useState<string | null>(null);
  const [aspectsJson, setAspectsJson] = useState<any>(null);
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
    setAspectsJson(null);

    try {
      const response = await fetch("https://albireo-daria-96.fly.dev/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Помилка генерації карти");
      }

      setChartUrl(data.chart_url);
      setAspectsJson(data.aspects_json);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`${css.formContainer} ${css.fadeInForm}`}>
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
          {loading ? "Генерація..." : "Побудувати натальну карту"}
        </button>
      </form>

      {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}

      {chartUrl && (
        <div className={`${css.chartContainer} ${css.fadeInUpForm}`}>
          <h3>Натальна карта</h3>
          <img src={chartUrl} alt="Натальна карта" />
        </div>
      )}

      {aspectsJson && (
        <div className={`${css.aspectsContainer} ${css.fadeInUpForm}`}>
          <h3>Аспекти</h3>
          <table>
            <thead>
              <tr>
                <th>Об’єкт 1</th>
                <th>Об’єкт 2</th>
                <th>Тип</th>
                <th>Кут</th>
              </tr>
            </thead>
            <tbody>
              {aspectsJson.map((asp: any, idx: number) => (
                <tr key={idx} style={{ backgroundColor: ASPECT_ROW_COLORS[asp.type] || "transparent" }}>
                  <td>{asp.object1}</td>
                  <td>{asp.object2}</td>
                  <td>{asp.type}</td>
                  <td>{asp.angle}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export { GenerateChartForm };