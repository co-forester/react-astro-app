// src/components/NatalChartDisplay/NatalChartDisplay.tsx
import React from 'react';
// Стилі можна взяти з GenerateChartForm.module.css або створити нові
import css from '../GenerateChart/GenerateChartForm.module.css';

interface ChartData {
    chart_url: string;
    aspects_table: any[];
    ai_interpretation: string;
}

interface NatalChartDisplayProps {
    data: ChartData;
}

const NatalChartDisplay: React.FC<NatalChartDisplayProps> = ({ data }) => {
    return (
        <>
            {/* Блок для інтерпретації ШІ */}
            <div className={css.aiInterpretationContainer}>
                <h3>✨ Астрологічний аналіз</h3>
                <pre className={css.aiText}>{data.ai_interpretation}</pre>
            </div>

            {/* Блок для зображення карти */}
            <div className={css.chartContainer}>
                <h3>Натальна карта</h3>
                <img src={data.chart_url} alt="Натальна карта" style={{ maxWidth: "100%", height: "auto" }} />
            </div>

            {/* Блок для таблиці аспектів */}
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
                        {data.aspects_table.map((asp: any, idx: number) => (
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
        </>
    );
};

export { NatalChartDisplay };