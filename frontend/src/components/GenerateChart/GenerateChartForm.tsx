import React, { useState } from "react";

const GenerateChartForm: React.FC = () => {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [place, setPlace] = useState("");
  const [chartUrl, setChartUrl] = useState("");
  const [chartData, setChartData] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const response = await fetch("http://albireo-daria-96.fly.dev/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date, time, place }),
    });

    const data = await response.json();
    setChartUrl("http://albireo-daria-96.fly.dev/chart.png?ts=" + new Date().getTime());
    setChartData(data);
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <label>
          Date:
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </label>
        <br />
        <label>
          Time:
          <input type="time" value={time} onChange={(e) => setTime(e.target.value)} required />
        </label>
        <br />
        <label>
          Place:
          <input type="text" value={place} onChange={(e) => setPlace(e.target.value)} required />
        </label>
        <br />
        <button type="submit">Generate Chart</button>
      </form>

      {chartUrl && (
        <div>
          <h2>Natal Chart</h2>
          <img src={chartUrl} alt="Natal Chart" style={{ maxWidth: "500px" }} />
        </div>
      )}

      {chartData && (
        <div>
          <h3>Chart Data</h3>
          <pre>{JSON.stringify(chartData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export {GenerateChartForm};