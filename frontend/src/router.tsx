import React from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

import { MainLayout } from "./layouts/MainLayout";
import { App } from "./components/App/App";
import { Home } from "./components/Home/Home";
import { NatalChart } from "./components/NatalChart/NatalChart";
import { ForecastAugust2025 } from "./components/ForecastAugust2025/ForecastAugust2025";
import { HoroscopeJuly19 } from "./components/HoroscopeJuly19/HoroscopeJuly19";
import { NatalChartAnalysis } from "./components/NatalChartAnalysis/NatalChartAnalysis";
import { ChildHoroscope } from "./components/ChildHoroscope/ChildHoroscope";

const router = createBrowserRouter([
  {
    path: "", element: <MainLayout />, children: [
      { index: true, element: <Navigate to={"App"}/> },
      {
        path: "App", element: <App />, children: [
          { index: true, element: <Navigate to={"home"}/> },
          { path: "home", element: <Home/> },
          { path: "natal_chart", element: <NatalChart/> },
          { path: "forecast_august_2025", element: <ForecastAugust2025/> },
          { path: "horoscope_july19", element: <HoroscopeJuly19/>}, 
          { path: "natal_chart_analysis", element: <NatalChartAnalysis/> },
          { path: "child_horoscope", element: <ChildHoroscope/> },      
         ]
      }
    ]
  }
]);

export { router };