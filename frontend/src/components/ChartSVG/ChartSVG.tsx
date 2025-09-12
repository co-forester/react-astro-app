// src/components/ChartSVG/ChartSVG.tsx
import React, { useState } from 'react';
import { useAppSelector } from '../../hooks/reduxHook';
import css from './ChartSVG.module.css';

type Planet = {
    name: string;
    symbol: string;
    angle: number;
    sign?: string;
    degree?: number;
    house?: number;
};

type Aspect = {
    from: string;
    to: string;
    type: string;
};

type Props = {
    planets: Planet[];
    aspects: Aspect[];
};

const ChartSVG: React.FC<Props> = ({ planets, aspects }) => {
    const theme = useAppSelector(state => state.theme.theme);
    const [hoveredPlanet, setHoveredPlanet] = useState<string | null>(null);

    // --- адаптивні розміри ---
    const size = Math.min(window.innerWidth, 500);
    const radius = size * 0.42;
    const center = { x: size / 2, y: size / 2 };

    const getCoords = (angle: number, r: number = radius) => {
        const rad = ((angle - 90) * Math.PI) / 180;
        return {
            x: center.x + r * Math.cos(rad),
            y: center.y + r * Math.sin(rad),
        };
    };

    // --- кольори ---
    const houseColors = [
        "#ffe0e0", "#fff0d0", "#f0ffe0", "#e0fff7",
        "#e0f0ff", "#f0e0ff", "#ffe0f7", "#fff7d9",
        "#e6ffe0", "#e0fff0", "#e0f7ff", "#f0e0ff"
    ];
    const aspectColors: Record<string, string> = {
        conjunction: "#D62728",
        sextile: "#1F77B4",
        square: "#FF7F0E",
        trine: "#2CA02C",
        opposition: "#9467BD",
        semisextile: "#8C564B",
        semisquare: "#E377C2",
        quincunx: "#7F7F7F",
        quintile: "#17BECF",
        biquintile: "#BCBD22",
    };
    const zodiacSymbols = ["♈︎", "♉︎", "♊︎", "♋︎", "♌︎", "♍︎", "♎︎", "♏︎", "♐︎", "♑︎", "♒︎", "♓︎"];

    return (
        <div className={theme ? css.ChartLight : css.ChartDark}>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                {/* --- Сектори домів (крок 3) --- */}
                {[...Array(12)].map((_, i) => {
                    const startAngle = i * 30;
                    const endAngle = (i + 1) * 30;
                    const start = getCoords(startAngle, radius);
                    const end = getCoords(endAngle, radius);

                    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
                    const pathData = `
                        M ${center.x} ${center.y}
                        L ${start.x} ${start.y}
                        A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}
                        Z
                    `;
                    return (
                        <path
                            key={`house-segment-${i}`}
                            d={pathData}
                            fill={houseColors[i % houseColors.length]}
                            opacity={0.25}
                            stroke="none"
                        />
                    );
                })}

                {/* --- Лінії домів --- */}
                {[...Array(12)].map((_, i) => {
                    const angle = (i * 30) % 360;
                    const from = getCoords(angle, radius);
                    return (
                        <line
                            key={`house-line-${i}`}
                            x1={center.x}
                            y1={center.y}
                            x2={from.x}
                            y2={from.y}
                            className={css.HouseLine}
                        />
                    );
                })}

                {/* --- Номери домів --- */}
                {[...Array(12)].map((_, i) => {
                    const midAngle = i * 30 + 15;
                    const coords = getCoords(midAngle, radius * 0.75);
                    return (
                        <text
                            key={`house-num-${i}`}
                            x={coords.x}
                            y={coords.y}
                            textAnchor="middle"
                            fontSize={size * 0.045}
                            fill={theme ? "#333" : "#fff"}
                            fontWeight="bold"
                        >
                            {i + 1}
                        </text>
                    );
                })}

                {/* --- Зодіакальне кільце з символами --- */}
                <circle cx={center.x} cy={center.y} r={radius} className={css.ZodiacCircle} />
                {[...Array(12)].map((_, i) => {
                    const angle = i * 30 + 15;
                    const coords = getCoords(angle, radius + 18);
                    return (
                        <text
                            key={`zodiac-${i}`}
                            x={coords.x}
                            y={coords.y}
                            textAnchor="middle"
                            fontSize={size * 0.06}
                            fill={theme ? "#000" : "#fff"}
                        >
                            {zodiacSymbols[i]}
                        </text>
                    );
                })}

                {/* --- Аспекти (крок 5) --- */}
                {aspects.map((asp, idx) => {
                    const fromPlanet = planets.find(p => p.name === asp.from);
                    const toPlanet = planets.find(p => p.name === asp.to);
                    if (!fromPlanet || !toPlanet) return null;

                    const fromCoords = getCoords(fromPlanet.angle);
                    const toCoords = getCoords(toPlanet.angle);
                    const color = aspectColors[asp.type] || "#999";

                    return (
                        <line
                            key={idx}
                            x1={fromCoords.x}
                            y1={fromCoords.y}
                            x2={toCoords.x}
                            y2={toCoords.y}
                            stroke={color}
                            strokeWidth={1.3}
                            opacity={0.8}
                        />
                    );
                })}

                {/* --- Планети (крок 1) --- */}
                {planets.map((pl, idx) => {
                    const coords = getCoords(pl.angle, radius * 0.9);
                    const isHovered = hoveredPlanet === pl.name;
                    return (
                        <g
                            key={idx}
                            onMouseEnter={() => setHoveredPlanet(pl.name)}
                            onMouseLeave={() => setHoveredPlanet(null)}
                        >
                            <circle
                                cx={coords.x}
                                cy={coords.y}
                                r={size * 0.025}
                                className={isHovered ? css.PlanetHover : css.PlanetNormal}
                            />
                            <text
                                x={coords.x}
                                y={coords.y + 4}
                                textAnchor="middle"
                                className={theme ? css.PlanetTextLight : css.PlanetTextDark}
                                fontSize={size * 0.05}
                            >
                                {pl.symbol}
                            </text>

                            {/* Tooltip */}
                            {isHovered && (
                                <g>
                                    <rect
                                        x={coords.x + 15}
                                        y={coords.y - 30}
                                        width={110}
                                        height={32}
                                        rx={6}
                                        fill="black"
                                        opacity={0.75}
                                    />
                                    <text
                                        x={coords.x + 70}
                                        y={coords.y - 12}
                                        textAnchor="middle"
                                        fill="white"
                                        fontSize={12}
                                    >
                                        {pl.name} {pl.degree?.toFixed(1)}° {pl.sign} {pl.house ? `H${pl.house}` : ""}
                                    </text>
                                </g>
                            )}
                        </g>
                    );
                })}

                {/* --- Вісь ASC/MC/DSC/IC (крок 2) --- */}
                {["ASC", "MC", "DSC", "IC"].map((point, i) => {
                    const angle = i * 90;
                    const coords = getCoords(angle, radius + 40);
                    return (
                        <text
                            key={point}
                            x={coords.x}
                            y={coords.y}
                            textAnchor="middle"
                            fill="yellow"
                            fontSize={size * 0.05}
                            fontWeight="bold"
                        >
                            {point}
                        </text>
                    );
                })}

                {/* --- Центр карти з логотипом (крок 6) --- */}
                <circle cx={center.x} cy={center.y} r={size * 0.08} fill={theme ? "#f5f5f5" : "#222"} />
                <text
                    x={center.x}
                    y={center.y + 4}
                    textAnchor="middle"
                    fontSize={size * 0.06}
                    fontWeight="bold"
                    fill={theme ? "#111" : "#eee"}
                >
                    ☉
                </text>
            </svg>
        </div>
    );
};

export { ChartSVG };