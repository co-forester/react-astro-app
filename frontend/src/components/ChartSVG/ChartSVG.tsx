import React, { useState } from 'react';
import { useAppSelector } from '../../hooks/reduxHook';

type Planet = {
    name: string;
    symbol: string;
    angle: number;
};

type Aspect = {
    from: string;
    to: string;
    type: string;
};

type Props = {
    planets: Planet[];
    aspects: Aspect[];
    onHoverPlanet?: (name: string | null) => void;
    onHoverAspect?: (asp: Aspect | null) => void;
};

const ChartSVG: React.FC<Props> = ({ planets, aspects, onHoverPlanet, onHoverAspect }) => {
    const theme = useAppSelector(state => state.theme.theme);
    const [hoveredPlanet, setHoveredPlanet] = useState<string | null>(null);
    const [hoveredAspect, setHoveredAspect] = useState<Aspect | null>(null);

    const radius = 200;
    const center = { x: 250, y: 250 };

    const getCoords = (angle: number) => {
        const rad = ((angle - 90) * Math.PI) / 180;
        return {
            x: center.x + radius * Math.cos(rad),
            y: center.y + radius * Math.sin(rad),
        };
    };

    return (
        <div style={{ background: theme ? '#f5f5f5' : '#4a4949', padding: 10 }}>
            <svg width={500} height={500}>
                {/* Коло зодіаку */}
                <circle
                    cx={center.x}
                    cy={center.y}
                    r={radius}
                    stroke="blue"
                    strokeWidth={2}
                    fill="none"
                />

                {/* Аспекти */}
                {aspects.map((asp, idx) => {
                    const fromPlanet = planets.find(p => p.name === asp.from);
                    const toPlanet = planets.find(p => p.name === asp.to);
                    if (!fromPlanet || !toPlanet) return null;

                    const fromCoords = getCoords(fromPlanet.angle);
                    const toCoords = getCoords(toPlanet.angle);

                    const isHovered =
                        hoveredAspect?.from === asp.from && hoveredAspect?.to === asp.to;

                    return (
                        <line
                            key={idx}
                            x1={fromCoords.x}
                            y1={fromCoords.y}
                            x2={toCoords.x}
                            y2={toCoords.y}
                            stroke={isHovered ? "orange" : "pink"}
                            strokeWidth={2}
                            onMouseEnter={() => {
                                setHoveredAspect(asp);
                                onHoverAspect && onHoverAspect(asp);
                            }}
                            onMouseLeave={() => {
                                setHoveredAspect(null);
                                onHoverAspect && onHoverAspect(null);
                            }}
                        />
                    );
                })}

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
                            }}
                            onMouseLeave={() => {
                                setHoveredPlanet(null);
                                onHoverPlanet && onHoverPlanet(null);
                            }}
                        >
                            <circle
                                cx={coords.x}
                                cy={coords.y}
                                r={12}
                                fill={isHovered ? "yellow" : "blue"}
                            />
                            <text
                                x={coords.x}
                                y={coords.y + 4}
                                textAnchor="middle"
                                fill={theme ? "#1a1a1a" : "#ffffff"}
                                fontSize={12}
                                fontFamily="Segoe UI, sans-serif"
                            >
                                {pl.symbol}
                            </text>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
};

export { ChartSVG };