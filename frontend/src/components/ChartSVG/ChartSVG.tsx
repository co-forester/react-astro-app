import React, { useState } from 'react';
import { useAppSelector } from '../../hooks/reduxHook';
import css from './ChartSVG.module.css';

type Planet = {
    name: string;
    symbol: string;
    angle: number; // градуси
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
    onHoverAspect?: (from: string, to: string) => void;
};

const ChartSVG: React.FC<Props> = ({ planets, aspects, onHoverPlanet, onHoverAspect }) => {
    const theme = useAppSelector(state => state.theme.theme); // <-- тепер беремо тут
    const [hoveredPlanet, setHoveredPlanet] = useState<string | null>(null);

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
        <div className={theme ? css.ChartLight : css.ChartDark}>
            <svg width={500} height={500}>
                {/* Коло зодіаку */}
                <circle cx={center.x} cy={center.y} r={radius} className={css.ZodiacCircle} />

                {/* Аспекти */}
                {aspects.map((asp, idx) => {
                    const fromPlanet = planets.find(p => p.name === asp.from);
                    const toPlanet = planets.find(p => p.name === asp.to);
                    if (!fromPlanet || !toPlanet) return null;

                    const fromCoords = getCoords(fromPlanet.angle);
                    const toCoords = getCoords(toPlanet.angle);

                    return (
                        <line
                            key={idx}
                            x1={fromCoords.x}
                            y1={fromCoords.y}
                            x2={toCoords.x}
                            y2={toCoords.y}
                            className={css.AspectLine}
                            onMouseEnter={() => onHoverAspect && onHoverAspect(fromPlanet.name, toPlanet.name)}
                            onMouseLeave={() => onHoverAspect && onHoverAspect('', '')}
                        />
                    );
                })}

                {/* Планети */}
                {planets.map((pl, idx) => {
                    const coords = getCoords(pl.angle);
                    return (
                        <g
                            key={idx}
                            className={css.Planet}
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
                                fill={hoveredPlanet === pl.name ? 'var(--accent-orange)' : 'var(--accent-blue)'}
                            />
                            <text
                                x={coords.x}
                                y={coords.y + 4}
                                textAnchor="middle"
                                fill={theme ? 'black' : 'white'}
                                fontSize="12"
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