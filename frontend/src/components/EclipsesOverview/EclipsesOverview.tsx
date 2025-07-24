import React from "react";
import css from "./EclipsesOverview.module.css";

const eclipses2025_2026 = [
  {
    date: "29 березня 2025",
    type: "Повне сонячне затемнення",
    visibility: "Західна Азія, Індія, частково Україна",
  },
  {
    date: "14 березня 2025",
    type: "Часткове місячне затемнення",
    visibility: "Європа, Азія, Африка",
  },
  {
    date: "21 вересня 2025",
    type: "Повне місячне затемнення",
    visibility: "Південна Америка, Європа, Африка",
  },
  {
    date: "7 жовтня 2025",
    type: "Кільцеподібне сонячне затемнення",
    visibility: "Америка, Атлантика, Африка",
  },
  {
    date: "3 березня 2026",
    type: "Повне сонячне затемнення",
    visibility: "Північна Америка, частково Європа",
  },
  {
    date: "17 серпня 2026",
    type: "Повне місячне затемнення",
    visibility: "Європа, Азія, Австралія",
  },
];

const EclipsesOverview = () => {
  return (
    <section className={css.eclipsesSection}>
      <h2 className={css.title}>🌒 Затемнення 2025–2026</h2>
      <div className={css.cardContainer}>
        {eclipses2025_2026.map((eclipse, index) => (
          <div key={index} className={css.card}>
            <h3>{eclipse.date}</h3>
            <p><strong>{eclipse.type}</strong></p>
            <p>🔭 Видимість: {eclipse.visibility}</p>
          </div>
        ))}
      </div>
    </section>
  );
};

export { EclipsesOverview };
