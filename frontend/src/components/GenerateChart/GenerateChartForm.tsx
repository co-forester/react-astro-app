import React, { useState } from "react";

interface GenerateChartResponse {
  chart_url?: string;
  warning?: string;
}

const GenerateChartForm: React.FC = () => {
  const [chartUrl, setChartUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://127.0.0.1:8080/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: "1972-12-06",
          time: "01:25",
          place: "Миколаїв, Україна"
        }),
      });

      if (!res.ok) {
        throw new Error(`Помилка сервера: ${res.status}`);
      }

      const data: GenerateChartResponse = await res.json();
      if (data.chart_url) {
        // напряму підвантажуємо картинку
        setChartUrl(`http://127.0.0.1:8080${data.chart_url}?t=${Date.now()}`);
      } else {
        setError("Не отримали URL до карти");
      }
    } catch (err: any) {
      setError(err.message || "Сталася невідома помилка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Генератор натальної карти</h2>
      <form onSubmit={handleSubmit}>
        <button type="submit" disabled={loading}>
          {loading ? "Завантаження..." : "Згенерувати карту"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ marginTop: "20px" }}>
        {chartUrl && (
          <img
            src={chartUrl}
            alt="Натальна карта"
            style={{ width: "400px", border: "1px solid #ccc" }}
          />
        )}
      </div>
    </div>
  );
};

export { GenerateChartForm };