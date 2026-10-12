import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
  Legend,
} from 'recharts';
import type { Reading, Sensor } from '../types/domain';

interface TemperatureChartProps {
  readings: Reading[];
  sensors: Sensor[];
  lowerLimitC: number;
  upperLimitC: number;
  selectedSensorId?: string | null;
}

export const TemperatureChart: React.FC<TemperatureChartProps> = ({
  readings,
  sensors,
  lowerLimitC,
  upperLimitC,
  selectedSensorId,
}) => {
  // Aggregate readings by timestamp bucket for multi-line rendering
  const chartData = useMemo(() => {
    if (!readings || readings.length === 0) return [];

    // Chronological order (oldest to newest for charting left-to-right)
    const sorted = [...readings].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    // Group by timestamp (rounded to 1 sec)
    const timeMap = new Map<string, any>();

    sorted.forEach((r) => {
      const timeKey = r.timestamp.slice(11, 19); // HH:MM:SS
      if (!timeMap.has(timeKey)) {
        timeMap.set(timeKey, { time: timeKey });
      }
      const entry = timeMap.get(timeKey);
      if (r.temperature_c !== null && r.temperature_c !== undefined) {
        entry[r.sensor_id] = r.temperature_c;
      }
    });

    return Array.from(timeMap.values()).slice(-40); // keep last 40 points
  }, [readings]);

  // Color palette for sensor lines
  const sensorColors = [
    '#38bdf8', // sky
    '#10b981', // emerald
    '#a855f7', // purple
    '#f59e0b', // amber
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#6366f1', // indigo
    '#14b8a6', // teal
  ];

  if (!readings || readings.length === 0) {
    return (
      <div style={{
        height: '280px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(10, 19, 34, 0.4)',
        borderRadius: '12px',
        border: '1px dashed rgba(148, 163, 184, 0.2)',
        color: '#64748b',
        gap: '8px',
      }}>
        <span style={{ fontSize: '24px' }}>📈</span>
        <span style={{ fontSize: '13px', fontWeight: 500 }}>No telemetry stream recorded yet.</span>
        <span style={{ fontSize: '11px', color: '#475569' }}>Start the simulation to plot real-time sensor curves.</span>
      </div>
    );
  }

  // Calculate dynamic domain
  const temps: number[] = readings
    .map((r) => r.temperature_c)
    .filter((t): t is number => t !== null && t !== undefined);
  const minObserved = temps.length ? Math.min(...temps, lowerLimitC) : lowerLimitC;
  const maxObserved = temps.length ? Math.max(...temps, upperLimitC) : upperLimitC;
  const yPadding = Math.max(1, (maxObserved - minObserved) * 0.15);
  const yDomain = [
    Math.floor(minObserved - yPadding),
    Math.ceil(maxObserved + yPadding),
  ];

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
          <XAxis
            dataKey="time"
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
          />
          <YAxis
            stroke="#64748b"
            fontSize={11}
            domain={yDomain}
            unit="°C"
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(10, 19, 34, 0.95)',
              borderColor: 'rgba(148, 163, 184, 0.2)',
              borderRadius: '8px',
              boxShadow: '0 8px 20px rgba(0,0,0,0.5)',
              fontSize: '12px',
            }}
            formatter={(val: any, name: any) => {
              const sensor = sensors.find((s) => s.id === name);
              const label = sensor ? sensor.label.split(' ')[0] : name;
              return [`${Number(val).toFixed(2)} °C`, label];
            }}
          />
          <Legend
            verticalAlign="top"
            height={32}
            wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }}
            formatter={(value) => {
              const sensor = sensors.find((s) => s.id === value);
              return sensor ? sensor.label.split(' ')[0] : value;
            }}
          />

          {/* Upper Limit Reference Threshold */}
          <ReferenceLine
            y={upperLimitC}
            stroke="#f43f5e"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{
              value: `Upper Max: ${upperLimitC.toFixed(1)}°C`,
              fill: '#f43f5e',
              fontSize: 10,
              position: 'insideTopRight',
            }}
          />

          {/* Lower Limit Reference Threshold */}
          <ReferenceLine
            y={lowerLimitC}
            stroke="#38bdf8"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            label={{
              value: `Lower Min: ${lowerLimitC.toFixed(1)}°C`,
              fill: '#38bdf8',
              fontSize: 10,
              position: 'insideBottomRight',
            }}
          />

          {/* Sensor Lines */}
          {sensors.map((sensor, idx) => {
            const isHighlighted = !selectedSensorId || selectedSensorId === sensor.id;
            const strokeColor = sensorColors[idx % sensorColors.length];
            return (
              <Line
                key={sensor.id}
                type="monotone"
                dataKey={sensor.id}
                stroke={strokeColor}
                strokeWidth={selectedSensorId === sensor.id ? 3 : 1.8}
                strokeOpacity={isHighlighted ? 1 : 0.25}
                dot={false}
                activeDot={{ r: 5, stroke: '#fff', strokeWidth: 2 }}
                isAnimationActive={false}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
