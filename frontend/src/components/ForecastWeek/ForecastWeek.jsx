import { useState } from "react";
import css from "./forecastAugust2025.module.css";

const ForecastWeek = ({ title, children, theme }) => {
  const [open, setOpen] = useState(false);

  return (
    <div
      className={theme ? css.weekBlockLight : css.weekBlockDark}
      onClick={() => setOpen(!open)}
    >
      <h3 style={{ cursor: "pointer" }}>{title}</h3>
      {open && <div className={css.weekContent}>{children}</div>}
    </div>
  );
};

export { ForecastWeek };