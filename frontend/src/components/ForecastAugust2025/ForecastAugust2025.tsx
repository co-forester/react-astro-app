import React, { useState } from "react";

interface GenerateChartResponse {
  chart_png?: string;
  chart_html?: string;
  warning?: string;
}

const ForecastAugust2025: React.FC = () => {
  const [chart, setChart] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8080/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}) // тут можна передати параметри прогнозу
      });
      const data: GenerateChartResponse = await res.json();
      if (data.chart_png) {
        setChart(`data:image/png;base64,${data.chart_png}`);
      } else if (data.chart_html) {
        setChart(data.chart_html);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Прогноз на серпень 2025</h2>
      <button onClick={handleGenerate} disabled={loading}>
        {loading ? "Завантаження..." : "Згенерувати карту"}
      </button>

      <div style={{ marginTop: "20px" }}>
        {chart && chart.startsWith("data:image") ? (
          <img src={chart} alt="Натальна карта" style={{ width: "400px" }} />
        ) : chart ? (
          <div dangerouslySetInnerHTML={{ __html: chart }} />
        ) : null}
      </div>
    </div>
  );
};

export {ForecastAugust2025};