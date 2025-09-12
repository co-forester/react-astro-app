import React, { useState } from 'react';
import { useAppSelector } from '../../hooks/reduxHook';
import css from './ChartSVG.module.css';

type Planet = { name: string; symbol: string; angle: number; degree?: number; sign?: string; house?: number; };
type Aspect = { from: string; to: string; type: string; };

type Props = { planets: Planet[]; aspects: Aspect[]; housesColors?: string[]; };

const zodiacSymbols = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"];

const ChartSVG: React.FC<Props> = ({ planets, aspects, housesColors }) => {
    const theme = useAppSelector(s => s.theme.theme);
    const [hoveredPlanet, setHoveredPlanet] = useState<string | null>(null);

    const size = Math.min(window.innerWidth, 500);
    const radius = size * 0.4;
    const center = { x: size / 2, y: size / 2 };

    const getCoords = (angle: number, r: number = radius) => {
        const rad = (angle - 90) * Math.PI / 180;
        return { x: center.x + r * Math.cos(rad), y: center.y + r * Math.sin(rad) };
    };

    const aspectColors: Record<string, string> = {
        conjunction: "#D62728", sextile: "#1F77B4", square: "#FF7F0E",
        trine: "#2CA02C", opposition: "#9467BD", semisextile: "#8C564B",
        semisquare: "#E377C2", quincunx: "#7F7F7F", quintile: "#17BECF", biquintile: "#BCBD22"
    };

    return (
        <div className={theme ? css.ChartLight : css.ChartDark}>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>

                {/* --- Зодіакальне коло --- */}
                <circle cx={center.x} cy={center.y} r={radius} className={css.ZodiacCircle} />

                {/* --- Лінії секторів будинків --- */}
                {[...Array(12)].map((_, i) => {
                    const { x, y } = getCoords(i * 30);
                    return <line key={i} x1={center.x} y1={center.y} x2={x} y2={y} className={css.HouseLine} />;
                })}

                {/* --- Сектори будинків кольорові --- */}
                {housesColors && [...Array(12)].map((_, i) => {
                    const start = i * 30 - 90;
                    const end = (i + 1) * 30 - 90;
                    const largeArc = end - start > 180 ? 1 : 0;
                    const r = radius - 10;
                    const x1 = center.x + r * Math.cos(start * Math.PI / 180);
                    const y1 = center.y + r * Math.sin(start * Math.PI / 180);
                    const x2 = center.x + r * Math.cos(end * Math.PI / 180);
                    const y2 = center.y + r * Math.sin(end * Math.PI / 180);
                    return <path key={i} d={`M${center.x},${center.y} L${x1},${y1} A${r},${r} 0 ${largeArc} 1 ${x2},${y2} Z`} fill={housesColors[i]} className={css.HouseSector} />;
                })}

                {/* --- Градуси та знаки --- */}
                {[...Array(360)].map((_, deg) => {
                    if (deg % 10 !== 0) return null; // крок 10°
                    const { x, y } = getCoords(deg, radius + 15);
                    return (
                        <text key={deg} x={x} y={y} textAnchor="middle" dominantBaseline="middle"
                            fontSize={size * 0.025} fill={theme ? "#000" : "#fff"}>
                            {deg % 30 === 0 ? zodiacSymbols[(deg / 30) % 12] : deg}
                        </text>
                    )
                })}

                {/* --- Планети --- */}
                {planets.map((pl, i) => {
                    const { x, y } = getCoords(pl.angle);
                    const isHover = hoveredPlanet === pl.name;
                    return (
                        <g key={i} onMouseEnter={() => setHoveredPlanet(pl.name)} onMouseLeave={() => setHoveredPlanet(null)}>
                            <circle cx={x} cy={y} r={size * 0.025} className={isHover ? css.PlanetHover : css.PlanetNormal} />
                            <text x={x} y={y} className={theme ? css.PlanetTextLight : css.PlanetTextDark}>{pl.symbol}</text>
                            {isHover && (
                                <>
                                    <rect x={x + 15} y={y - 30} width={90} height={28} rx={6} fill="black" opacity={0.7} />
                                    <text x={x + 60} y={y - 12} className={css.TooltipText}>{pl.name} {pl.degree?.toFixed(1)}° {pl.sign} {pl.house ? `H${pl.house}` : ""}</text>
                                </>
                            )}
                        </g>
                    );
                })}

                {/* --- Аспекти --- */}
                {aspects.map((asp, i) => {
                    const fromP = planets.find(p => p.name === asp.from);
                    const toP = planets.find(p => p.name === asp.to);
                    if (!fromP || !toP) return null;
                    const { x: x1, y: y1 } = getCoords(fromP.angle);
                    const { x: x2, y: y2 } = getCoords(toP.angle);
                    return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={aspectColors[asp.type] || "#999"} strokeWidth={1.5} opacity={0.8} />;
                })}

                {/* --- ASC/MC/DSC/IC --- */}
                {["ASC", "MC", "DSC", "IC"].map((p, i) => {
                    const { x, y } = getCoords(i * 90, radius + 20);
                    return <text key={p} x={x} y={y} className={css.AscMcDscIc} textAnchor="middle">{p}</text>
                })}

            </svg>
        </div>
    );
};

export { ChartSVG };