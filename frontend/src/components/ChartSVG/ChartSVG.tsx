import React, { useState } from 'react';
import { useAppSelector } from '../../hooks/reduxHook';
import css from './ChartSVG.module.css';

type Planet = {
    name: string;
    symbol: string;
    angle: number; // 0–360
    sign?: string;
    degree?: number;
    minute?: number;
    second?: number;
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

    const size = Math.min(window.innerWidth, 500);
    const radius = size * 0.4;
    const center = { x: size / 2, y: size / 2 };

    const getCoords = (angle: number, r: number = radius) => {
        const rad = ((angle - 90) * Math.PI) / 180;
        return { x: center.x + r * Math.cos(rad), y: center.y + r * Math.sin(rad) };
    };

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

    // Кольори домів (приклад)
    const houseColors = [
        "#FFE5E5", "#FFF5E5", "#FFFFE5", "#E5FFE5", "#E5FFFF", "#E5E5FF",
        "#F5E5FF", "#FFE5F5", "#FFD9D9", "#FFF0D9", "#FFFFD9", "#D9FFD9"
    ];

    const formatDMS = (deg?: number, min?: number, sec?: number) => {
        if (deg === undefined) return "";
        return `${deg}°${min ?? 0}'${sec ?? 0}"`;
    };

    return (
        <div className={`${css.Chart} ${theme ? css.ChartLight : css.ChartDark}`}>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                {/* --- Дома кольорові сектори --- */}
                {[...Array(12)].map((_, i) => {
                    const startAngle = i * 30;
                    const endAngle = (i + 1) * 30;
                    const largeArc = endAngle - startAngle > 180 ? 1 : 0;

                    const start = getCoords(startAngle, radius);
                    const end = getCoords(endAngle, radius);

                    const path = `
                        M ${center.x} ${center.y}
                        L ${start.x} ${start.y}
                        A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}
                        Z
                    `;

                    return (
                        <path key={i} d={path} fill={houseColors[i]} opacity={0.2} />
                    );
                })}

                {/* --- Коло зодіаку --- */}
                <circle cx={center.x} cy={center.y} r={radius} className={css.ZodiacCircle} />

                {[...Array(12)].map((_, i) => {
                    const angle = i * 30;
                    const from = getCoords(angle, radius);
                    return (
                        <line
                            key={i}
                            x1={center.x}
                            y1={center.y}
                            x2={from.x}
                            y2={from.y}
                            className={css.ZodiacLine}
                        />
                    );
                })}

                {/* --- Коло домів --- */}
                <circle cx={center.x} cy={center.y} r={radius - 20} className={css.HousesCircle} />
                {[...Array(12)].map((_, i) => {
                    const angle = i * 30;
                    const from = getCoords(angle, radius - 20);
                    return (
                        <line
                            key={`house-${i}`}
                            x1={center.x}
                            y1={center.y}
                            x2={from.x}
                            y2={from.y}
                            className={css.HouseLine}
                        />
                    );
                })}

                {/* --- Аспекти --- */}
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
                            strokeWidth={1.5}
                            opacity={0.8}
                        />
                    );
                })}

                {/* --- Планети --- */}
                {planets.map((pl, idx) => {
                    const coords = getCoords(pl.angle);
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
                                className={theme ? css.PlanetTextLight : css.PlanetTextDark}
                            >
                                {pl.symbol}
                            </text>

                            {isHovered && (
                                <g>
                                    <rect
                                        x={coords.x + 15}
                                        y={coords.y - 30}
                                        width={120}
                                        height={30}
                                        rx={6}
                                        fill="black"
                                        opacity={0.7}
                                    />
                                    <text
                                        x={coords.x + 75}
                                        y={coords.y - 12}
                                        className={css.TooltipText}
                                    >
                                        {pl.name} {formatDMS(pl.degree, pl.minute, pl.second)} {pl.sign} {pl.house ? `H${pl.house}` : ""}
                                    </text>
                                </g>
                            )}
                        </g>
                    );
                })}

                {/* --- Вісь ASC/MC/DSC/IC --- */}
                {["ASC", "MC", "DSC", "IC"].map((point, i) => {
                    const angle = i * 90;
                    const coords = getCoords(angle, radius + 20);
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
            </svg>
        </div>
    );
};

export { ChartSVG };