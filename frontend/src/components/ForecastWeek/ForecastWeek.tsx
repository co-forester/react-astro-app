import { useState, ReactNode } from "react";
import css from "../ForecastAugust2025/forecastAugust2025.module.css";

interface ForecastWeekProps {
  title: string;
  children: ReactNode;
  theme: boolean;
}

export const ForecastWeek = ({ title, children, theme }: ForecastWeekProps) => {
  const [open, setOpen] = useState(false);

  return (
    <div
      className={theme ? css.weekBlockLight : css.weekBlockDark}
      onClick={() => setOpen(!open)}
      style={{ cursor: "pointer" }}
    >
      <h3>{title}</h3>
      {open && <div>{children}</div>}
    </div>
  );
};