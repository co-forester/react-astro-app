import React, { useState } from "react";
import css from "./ChartSVG.module.css";

type Planet = {
    name: string;
    symbol: string;
    angle: number; // у градусах
};

type Props = {
    planets: Planet[];
    theme: boolean; // true = light, false = dark
    onHoverPlanet?: (planet: string | null) => void;
};

const RADIUS = 200; // радіус кола карти
const CENTER = 250; // центр SVG (ширина/висота = 500)

export default function ChartSVG({ planets, theme, onHoverPlanet }: Props) {
    const [hoveredPlanet, setHoveredPlanet] = useState<string | null>(null);
    const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);

    const getCoords = (angle: number) => {
        const rad = ((90 - angle) * Math.PI) / 180; // 0° = на сході
        const x = CENTER + RADIUS * Math.cos(rad);
        const y = CENTER - RADIUS * Math.sin(rad);
        return { x, y };
    };

    return (
        <svg width={500} height={500} className={css.Chart}>
            {/* Зодіакальне коло */}
            <circle
                cx={CENTER}
                cy={CENTER}
                r={RADIUS}
                className={theme ? css.CircleLight : css.CircleDark}
            />

            {/* Планети */}
            {planets.map((pl, idx) => {
                const coords = getCoords(pl.angle);
                const isHovered = hoveredPlanet === pl.name;

                return (
                    <g
                        key={idx}
                        onMouseEnter={() => {
                            setHoveredPlanet(pl.name);
                            onHoverPlanet && onHoverPlanet(pl.name);

                            setTooltip({
                                x: coords.x + 15,
                                y: coords.y - 15,
                                text: `${pl.name} ${pl.angle.toFixed(1)}°`,
                            });
                        }}
                        onMouseLeave={() => {
                            setHoveredPlanet(null);
                            onHoverPlanet && onHoverPlanet(null);
                            setTooltip(null);
                        }}
                    >
                        <circle
                            cx={coords.x}
                            cy={coords.y}
                            r={12}
                            className={isHovered ? css.PlanetHover : css.PlanetNormal}
                        />
                        <text
                            x={coords.x}
                            y={coords.y + 4}
                            textAnchor="middle"
                            className={theme ? css.PlanetTextLight : css.PlanetTextDark}
                        >
                            {pl.symbol}
                        </text>
                    </g>
                );
            })}

            {/* Tooltip (підказка) */}
            {tooltip && (
                <text
                    x={tooltip.x}
                    y={tooltip.y}
                    className={css.TooltipText}
                    fontSize={12}
                    fill="yellow"
                >
                    {tooltip.text}
                </text>
            )}
        </svg>
    );
}