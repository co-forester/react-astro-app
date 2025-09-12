import React, { useState } from 'react';
import { useAppSelector } from '../../hooks/reduxHook';
import css from './ChartSVG.module.css';

type Planet = {
    name: string;
    symbol: string;
    angle: number;
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
    houses?: number[];
};

const ChartSVG: React.FC<Props> = ({ planets, aspects, houses }) => {
    const theme = useAppSelector(state => state.theme.theme);
    const [hoveredPlanet, setHoveredPlanet] = useState<string | null>(null);

    const size = Math.min(window.innerWidth, 800);
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

    const houseColors = [
        "#FFDDC1", "#FFE4E1", "#FFFACD", "#E0FFFF", "#E6E6FA", "#F0FFF0",
        "#F5F5DC", "#FFF0F5", "#F0F8FF", "#FAFAD2", "#F0E68C", "#FFE4B5"
    ];

    return (
        <div className={`${css.Chart} ${theme ? css.ChartLight : css.ChartDark}`}>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                {/* Кольорові сектори будинків */}
                {houses && houses.map((deg, i) => {
                    const startAngle = deg;
                    const endAngle = houses[(i + 1) % 12];
                    const start = getCoords(startAngle);
                    const end = getCoords(endAngle);
                    return (
                        <path
                            key={`house-sector-${i}`}
                            d={`M${center.x},${center.y} 
                               L${start.x},${start.y} 
                               A${radius},${radius} 0 0,1 ${end.x},${end.y} Z`}
                            fill={houseColors[i % houseColors.length]}
                            opacity={0.2}
                        />
                    )
                })}

                {/* Zodiac & Houses Circle */}
                <circle cx={center.x} cy={center.y} r={radius} className={css.ZodiacCircle} />
                <circle cx={center.x} cy={center.y} r={radius - 20} className={css.HousesCircle} />

                {/* Лінії Zodiac та Houses */}
                {[...Array(12)].map((_, i) => {
                    const angle = i * 30;
                    const fromZ = getCoords(angle, radius);
                    const fromH = getCoords(angle, radius - 20);
                    return (
                        <g key={i}>
                            <line x1={center.x} y1={center.y} x2={fromZ.x} y2={fromZ.y} className={css.ZodiacLine} />
                            <line x1={center.x} y1={center.y} x2={fromH.x} y2={fromH.y} className={css.HouseLine} />
                        </g>
                    )
                })}

                {/* Аспекти */}
                {aspects.map((asp, idx) => {
                    const fromP = planets.find(p => p.name === asp.from);
                    const toP = planets.find(p => p.name === asp.to);
                    if (!fromP || !toP) return null;
                    const fromC = getCoords(fromP.angle, radius - 40);
                    const toC = getCoords(toP.angle, radius - 40);
                    return <line key={idx} x1={fromC.x} y1={fromC.y} x2={toC.x} y2={toC.y} stroke={aspectColors[asp.type] || "#999"} strokeWidth={1.5} opacity={0.7} />
                })}

                {/* Планети */}
                {planets.map((pl, idx) => {
                    const coords = getCoords(pl.angle, radius - 40);
                    const isHovered = hoveredPlanet === pl.name;
                    return (
                        <g key={idx} onMouseEnter={() => setHoveredPlanet(pl.name)} onMouseLeave={() => setHoveredPlanet(null)}>
                            <circle cx={coords.x} cy={coords.y} r={size * 0.025} className={isHovered ? css.PlanetHover : css.PlanetNormal} />
                            <text x={coords.x} y={coords.y + 4} className={theme ? css.PlanetTextLight : css.PlanetTextDark} fontSize={size * 0.05}>
                                {pl.symbol}
                            </text>
                            {isHovered && (
                                <g>
                                    <rect x={coords.x + 15} y={coords.y - 30} width={120} height={32} rx={6} fill="black" opacity={0.7} />
                                    <text x={coords.x + 75} y={coords.y - 12} textAnchor="middle" fill="white" fontSize={12}>
                                        {pl.name} {pl.degree}° {pl.minute}' {pl.second}" {pl.sign} {pl.house ? `H${pl.house}` : ""}
                                    </text>
                                </g>
                            )}
                        </g>
                    )
                })}

                {/* ASC/MC/DSC/IC */}
                {["ASC", "MC", "DSC", "IC"].map((point, i) => {
                    const angle = i * 90;
                    const coords = getCoords(angle, radius + 20);
                    return <text key={point} x={coords.x} y={coords.y} textAnchor="middle" fill="yellow" fontSize={size * 0.05} fontWeight="bold">{point}</text>
                })}

            </svg>
        </div>
    )
}

export { ChartSVG };