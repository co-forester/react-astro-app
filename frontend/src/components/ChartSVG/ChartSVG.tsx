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

    // --- Розміри карти ---
    const size = Math.min(window.innerWidth, 800);
    const radius = size * 0.4;
    const center = { x: size / 2, y: size / 2 };

    const getCoords = (angle: number, r: number = radius) => {
        const rad = ((angle - 90) * Math.PI) / 180;
        return {
            x: center.x + r * Math.cos(rad),
            y: center.y + r * Math.sin(rad),
        };
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

    return (
        <div className={`${css.Chart} ${theme ? css.ChartLight : css.ChartDark}`}>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
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

                    const fromCoords = getCoords(fromPlanet.angle, radius - 25);
                    const toCoords = getCoords(toPlanet.angle, radius - 25);
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
                            opacity={0.7}
                        />
                    );
                })}

                {/* --- Планети --- */}
                {planets.map((pl, idx) => {
                    const coords = getCoords(pl.angle, radius - 10);
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
                                y={coords.y + 2}
                                className={theme ? css.PlanetTextLight : css.PlanetTextDark}
                            >
                                {pl.symbol}
                            </text>

                            {isHovered && (
                                <g>
                                    <rect
                                        x={coords.x + 12}
                                        y={coords.y - 28}
                                        width={100}
                                        height={28}
                                        rx={6}
                                        fill="#000"
                                        opacity={0.7}
                                    />
                                    <text
                                        x={coords.x + 62}
                                        y={coords.y - 10}
                                        className={css.TooltipText}
                                    >
                                        {pl.name} {pl.degree?.toFixed(1)}° {pl.sign} {pl.house ? `H${pl.house}` : ""}
                                    </text>
                                </g>
                            )}
                        </g>
                    );
                })}

                {/* --- ASC / MC / DSC / IC --- */}
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