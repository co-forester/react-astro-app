import React, { useState } from "react";
// ⚡ Можна додати react-markdown для красивого рендерингу
// import ReactMarkdown from "react-markdown";
import css from "./GenerateChartForm.module.css";

interface FormData {
  name: string;
  date: string;
  time: string;
  place: string;
}

type GenerateChartFormProps = {
  onDataReady?: (data: { planets: any[]; aspects: any[] }) => void;
};

const GenerateChartForm: React.FC<GenerateChartFormProps> = ({ onDataReady }) => {
  const [formData, setFormData] = useState<FormData>({
    name: "",
    date: "",
    time: "",
    place: "",
  });
  const [chartUrl, setChartUrl] = useState<string | null>(null);
  const [aspectsJson, setAspectsJson] = useState<any>(null);
  
  // --- НОВИЙ КОД ---
  const [aiInterpretation, setAiInterpretation] = useState<string | null>(null);
  // --- КІНЕЦЬ НОВОГО КОДУ ---

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
    
    // --- НОВИЙ КОД ---
    setAiInterpretation(null); // Очищуємо попередню інтерпретацію
    // --- КІНЕЦЬ НОВОГО КОДУ ---

    try {
      const response = await fetch("https://albireo-daria-96.fly.dev/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Помилка генерації карти");

      setChartUrl(data.chart_url);
      setAspectsJson(data.aspects_json);
      
      // --- НОВИЙ КОД ---
      setAiInterpretation(data.ai_interpretation); // Зберігаємо інтерпретацію
      // --- КІНЕЦЬ НОВОГО КОДУ ---

      if (onDataReady) {
        onDataReady({
          planets: data.planets || [],
          aspects: data.aspects_json || [],
        });
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`${css.formContainer} fadeInForm`}>
      <form onSubmit={handleSubmit}>
        {/* ... ваші інпути залишаються без змін ... */}
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

      {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}

      {/* --- НОВИЙ КОД: Блок для відображення інтерпретації --- */}
      {aiInterpretation && (
        <div className={css.aiInterpretationContainer}>
            <h3>✨ Астрологічний аналіз від Дарії Альбірео</h3>
            {/* Для простоти використовуємо <pre>, щоб зберегти форматування.
                Для кращого вигляду можна встановити `react-markdown`
                і замінити <pre> на <ReactMarkdown>{aiInterpretation}</ReactMarkdown> */}
            <pre className={css.aiText}>{aiInterpretation}</pre>
        </div>
      )}
      {/* --- КІНЕЦЬ НОВОГО КОДУ --- */}

      {chartUrl && (
        <div className={css.chartContainer}>
          <h3>Натальна карта</h3>
          <img src={chartUrl} alt="Натальна карта" style={{ maxWidth: "100%", height: "auto" }} />
        </div>
      )}

      {aspectsJson && (
        <div className={css.aspectsContainer}>
          {/* ... ваша таблиця аспектів залишається без змін ... */}
        </div>
      )}
    </div>
  );
};

export { GenerateChartForm };
      setAspectsJson(data.aspects_json);

      // ⚡ передаємо наверх
      if (onDataReady) {
        onDataReady({
          planets: data.planets || [],
          aspects: data.aspects_json || [],
        });
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`${css.formContainer} fadeInForm`}>
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
        <div className={css.chartContainer}>
          <h3>Натальна карта</h3>
          <img src={chartUrl} alt="Натальна карта" style={{ maxWidth: "100%", height: "auto" }} />
        </div>
      )}

      {aspectsJson && (
        <div className={css.aspectsContainer}>
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
                <tr key={idx} style={{ color: asp.color }}>
                  <td>{asp.planet1}</td>
                  <td>{asp.planet2}</td>
                  <td>{asp.type}</td>
                  <td>{asp.angle_dms}</td>
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
