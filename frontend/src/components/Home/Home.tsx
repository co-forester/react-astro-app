// src/components/Home/Home.tsx
import React, { FC, useState } from 'react';
import css from './home.module.css';
import { GenerateChartForm, FormData } from '../GenerateChart/GenerateChartForm';
import { NatalChartDisplay } from '../NatalChartDisplay'; // Новий компонент
import { EclipsesOverview } from '../EclipsesOverview/EclipsesOverview';
import { HoroscopeJuly19 } from '../HoroscopeJuly19/HoroscopeJuly19';

// Тип для даних, які ми очікуємо від API
interface ChartData {
  chart_url: string;
  aspects_table: any[];
  ai_interpretation: string;
}

const Home: FC = () => {
  // Весь стан, пов'язаний з картою, тепер живе тут
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Функція для запиту даних, яку ми передамо у форму
  const handleGenerateChart = async (formData: FormData) => {
    setLoading(true);
    setError(null);
    setChartData(null);

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

      setChartData(data); // Зберігаємо всі дані в одному місці

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={css.mainDark}> {/* Або ваш css.mainLight */}
      <div className={css.gridContainer}>
        <aside className={css.leftBlock}>
          <EclipsesOverview />
        </aside>

        <main className={css.content}>
          <div className={css.intro}>
            <h2>Услуги</h2>
            <p>
              Предлагаю <span className="highlight">натальные карты</span>, гороскоп ребенка, аналіз натальної карты, индивидуальные прогнозы и астрологическое сопровождение.
            </p>
          </div>

          {/* Передаємо в форму лише функцію для сабміту та стан завантаження */}
          <GenerateChartForm onSubmit={handleGenerateChart} loading={loading} />

          {/* Відображаємо помилку, якщо вона є */}
          {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}

          {/* Відображаємо результати, коли вони завантажені */}
          {chartData && <NatalChartDisplay data={chartData} />}

        </main>

        <aside className={css.sidebar}>
          <HoroscopeJuly19 />
        </aside>
      </div>
    </div>
  );
};

export { Home };