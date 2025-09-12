import React, { useState } from 'react';
import { useAppSelector } from '../../hooks/reduxHook';
import css from './ChartSVG.module.css';

type Planet = {
    name: string;
    symbol: string;
    angle: number; // в градусах
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

    return (
        <div className={theme ? css.ChartLight : css.ChartDark + " " + css.Chart}>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>

                {/* --- Зодіак --- */}
                <circle cx={center.x} cy={center.y} r={radius} className={css.ZodiacCircle} />
                {[...Array(360)].map((_, i) => {
                    const angle = i;
                    const from = getCoords(angle, radius);
                    const len = i % 10 === 0 ? 8 : 4;
                    const to = getCoords(angle, radius - len);
                    return <line key={i} x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={css.ZodiacLine} strokeWidth={i % 10 === 0 ? 1.2 : 0.5} />;
                })}

                {/* --- Будинки --- */}
                {[...Array(12)].map((_, i) => {
                    const startAngle = i * 30;
                    const endAngle = (i + 1) * 30;
                    const start = getCoords(startAngle, radius);
                    const end = getCoords(endAngle, radius);
                    return (
                        <g key={i}>
                            <line x1={center.x} y1={center.y} x2={start.x} y2={start.y} className={css.HouseLine} />
                            <path d={`M${center.x},${center.y} L${start.x},${start.y} A${radius},${radius} 0 0,1 ${end.x},${end.y} Z`} fill={`hsla(${i * 30}, 70%, 50%, 0.1)`} stroke="none" />
                        </g>
                    );
                })}

                {/* --- Аспекти --- */}
                {aspects.map((asp, idx) => {
                    const fromP = planets.find(p => p.name === asp.from);
                    const toP = planets.find(p => p.name === asp.to);
                    if (!fromP || !toP) return null;
                    const fromCoords = getCoords(fromP.angle);
                    const toCoords = getCoords(toP.angle);
                    const color = aspectColors[asp.type] || "#999";
                    return <line key={idx} x1={fromCoords.x} y1={fromCoords.y} x2={toCoords.x} y2={toCoords.y} stroke={color} strokeWidth={1.5} opacity={0.8} />;
                })}

                {/* --- Планети --- */}
                {planets.map((pl, idx) => {
                    const coords = getCoords(pl.angle);
                    const isHovered = hoveredPlanet === pl.name;
                    const degText = `${pl.degree?.toFixed(0)}°${pl.minute?.toFixed(0) ?? 0}'${pl.second?.toFixed(0) ?? 0}"`;

                    return (
                        <g key={idx} onMouseEnter={() => setHoveredPlanet(pl.name)} onMouseLeave={() => setHoveredPlanet(null)}>
                            <circle cx={coords.x} cy={coords.y} r={size * 0.025} className={isHovered ? css.PlanetHover : css.PlanetNormal} />
                            <text x={coords.x} y={coords.y + 4} className={theme ? css.PlanetTextLight : css.PlanetTextDark} fontSize={size * 0.05}>
                                {pl.symbol}
                            </text>

                            {isHovered && (
                                <g>
                                    <rect x={coords.x + 15} y={coords.y - 30} width={110} height={28} rx={6} fill="black" opacity={0.7} />
                                    <text x={coords.x + 70} y={coords.y - 12} textAnchor="middle" fill="white" fontSize={12}>
                                        {pl.name} {degText} {pl.sign} {pl.house ? `H${pl.house}` : ""}
                                    </text>
                                </g>
                            )}
                        </g>
                    );
                })}

                {/* --- ASC/MC/DSC/IC --- */}
                {["ASC", "MC", "DSC", "IC"].map((point, i) => {
                    const coords = getCoords(i * 90, radius + 20);
                    return <text key={point} x={coords.x} y={coords.y} textAnchor="middle" fill="yellow" fontWeight="bold" fontSize={size * 0.05}>{point}</text>
                })}
            </svg>
        </div>
    );
};

export { ChartSVG };