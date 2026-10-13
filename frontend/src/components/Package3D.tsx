import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, Line } from '@react-three/drei';
import * as THREE from 'three';
import type { Sensor } from '../types/domain';

interface Package3DProps {
  vialCount: number;
  sensors: Sensor[];
  selectedSensorId?: string | null;
  onSelectSensor?: (sensorId: string) => void;
  lowerLimitC: number;
  upperLimitC: number;
}

// Single Biologic Vial in 3x3 grid
function BiologicVial({ position, index }: { position: [number, number, number]; index: number }) {
  const meshRef = useRef<THREE.Group>(null);

  // Subtle floating micro-animation
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 1.5 + index * 0.4) * 0.015;
    }
  });

  return (
    <group ref={meshRef} position={position}>
      {/* Glass Body */}
      <mesh position={[0, 0.35, 0]}>
        <cylinderGeometry args={[0.22, 0.22, 0.7, 24]} />
        <meshPhysicalMaterial
          color="#bae6fd"
          transparent
          opacity={0.7}
          roughness={0.1}
          metalness={0.1}
          transmission={0.65}
          ior={1.45}
        />
      </mesh>

      {/* Cryogenic Biologic Liquid */}
      <mesh position={[0, 0.25, 0]}>
        <cylinderGeometry args={[0.2, 0.2, 0.45, 24]} />
        <meshStandardMaterial
          color="#0284c7"
          roughness={0.3}
          metalness={0.2}
          emissive="#0369a1"
          emissiveIntensity={0.25}
        />
      </mesh>

      {/* Rubber Stopper & Crimped Seal */}
      <mesh position={[0, 0.72, 0]}>
        <cylinderGeometry args={[0.15, 0.15, 0.08, 24]} />
        <meshStandardMaterial color="#64748b" metalness={0.7} roughness={0.3} />
      </mesh>
      {/* Flip-off Cap */}
      <mesh position={[0, 0.78, 0]}>
        <cylinderGeometry args={[0.17, 0.17, 0.06, 24]} />
        <meshStandardMaterial color="#0ea5e9" roughness={0.4} />
      </mesh>

      {/* Vial Label Pill */}
      <Html position={[0, 0.0, 0.28]} center distanceFactor={6.5}>
        <div style={{
          fontSize: '9px',
          fontWeight: 700,
          background: 'rgba(15, 23, 42, 0.9)',
          color: '#38bdf8',
          padding: '1px 5px',
          borderRadius: '3px',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          whiteSpace: 'nowrap',
          pointerEvents: 'none',
          boxShadow: '0 2px 5px rgba(0,0,0,0.5)',
        }}>
          Vial {index + 1}
        </div>
      </Html>
    </group>
  );
}

// Independent Sensor Marker with Clean Outboard Label Callout & Connecting Line
function SensorMarker3D({
  sensor,
  index,
  totalSensors,
  isSelected,
  onClick,
  lowerLimitC,
  upperLimitC,
}: {
  sensor: Sensor;
  index: number;
  totalSensors: number;
  isSelected: boolean;
  onClick: () => void;
  lowerLimitC: number;
  upperLimitC: number;
}) {
  const [hovered, setHovered] = useState(false);
  const temp = sensor.last_valid_temperature_c;

  // Determine indicator color
  let probeColor = '#06b6d4'; // default cyan
  let emissiveColor = '#0891b2';
  let statusBadge = 'NORMAL';

  if (sensor.health_status !== 'healthy') {
    probeColor = '#f59e0b'; // amber warning
    emissiveColor = '#d97706';
    statusBadge = sensor.health_status.toUpperCase();
  } else if (temp !== null && temp !== undefined) {
    if (temp > upperLimitC) {
      probeColor = '#f43f5e'; // red breach
      emissiveColor = '#e11d48';
      statusBadge = 'HIGH';
    } else if (temp < lowerLimitC) {
      probeColor = '#38bdf8'; // deep cold blue
      emissiveColor = '#0284c7';
      statusBadge = 'LOW';
    } else {
      probeColor = '#10b981'; // green normal
      emissiveColor = '#059669';
      statusBadge = 'OK';
    }
  }

  // Calculate clean outward offset for the label so it hovers clearly outside the box perimeter
  const probePos: [number, number, number] = [sensor.position_x, sensor.position_y, sensor.position_z];

  // Disperse label positions radially outward away from the 3D shipper box (bounds: 3.2 x 1.3 x 3.2)
  const angle = (index / Math.max(1, totalSensors)) * 2 * Math.PI - Math.PI / 4;
  const radialDist = 2.4; // comfortably outside the 1.6 box radius
  const labelHeight = 1.1 + (index % 2) * 0.45; // stagger heights to avoid collision
  const labelPos: [number, number, number] = [
    Math.cos(angle) * radialDist,
    labelHeight,
    Math.sin(angle) * radialDist,
  ];

  return (
    <group>
      {/* 3D Connector Leader Line from Physical Probe to Callout Label */}
      <Line
        points={[probePos, [labelPos[0] * 0.9, labelPos[1] - 0.1, labelPos[2] * 0.9], labelPos]}
        color={isSelected || hovered ? probeColor : '#475569'}
        lineWidth={isSelected || hovered ? 2 : 1}
        transparent
        opacity={isSelected || hovered ? 0.9 : 0.45}
        dashed={!isSelected}
        dashScale={20}
        dashSize={0.2}
        gapSize={0.1}
      />

      {/* Sensor Physical Probe Hardware at actual position */}
      <group
        position={probePos}
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        {/* Metal Mount Stem */}
        <mesh position={[0, -0.25, 0]}>
          <cylinderGeometry args={[0.035, 0.035, 0.5, 16]} />
          <meshStandardMaterial color="#64748b" metalness={0.85} roughness={0.2} />
        </mesh>

        {/* Thermistor Probe Tip */}
        <mesh position={[0, 0, 0]} scale={isSelected || hovered ? 1.5 : 1.1}>
          <sphereGeometry args={[0.13, 24, 24]} />
          <meshStandardMaterial
            color={probeColor}
            emissive={emissiveColor}
            emissiveIntensity={isSelected || hovered ? 1.0 : 0.5}
            roughness={0.2}
            metalness={0.6}
          />
        </mesh>

        {/* Pulse Target Ring */}
        {(isSelected || hovered) && (
          <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
            <ringGeometry args={[0.2, 0.28, 32]} />
            <meshBasicMaterial color={probeColor} side={THREE.DoubleSide} transparent opacity={0.75} />
          </mesh>
        )}
      </group>

      {/* Outboard Uncrammed Label Card with Clear Telemetry Details */}
      <Html position={labelPos} center distanceFactor={7.5}>
        <div
          onClick={(e) => {
            e.stopPropagation();
            onClick();
          }}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '3px',
            padding: '5px 9px',
            borderRadius: '6px',
            background: isSelected
              ? 'rgba(14, 25, 44, 0.98)'
              : hovered
              ? 'rgba(15, 23, 42, 0.95)'
              : 'rgba(5, 11, 20, 0.88)',
            backdropFilter: 'blur(10px)',
            border: `1.5px solid ${isSelected ? probeColor : hovered ? '#38bdf8' : 'rgba(148, 163, 184, 0.25)'}`,
            boxShadow: isSelected
              ? `0 0 16px ${probeColor}50, 0 6px 16px rgba(0,0,0,0.7)`
              : '0 4px 12px rgba(0,0,0,0.5)',
            cursor: 'pointer',
            userSelect: 'none',
            whiteSpace: 'nowrap',
            transition: 'all 0.15s ease',
            transform: isSelected || hovered ? 'scale(1.06)' : 'scale(1.0)',
            zIndex: isSelected ? 20 : 1,
          }}
        >
          {/* Header row: Sensor Name & Status Pill */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
            <span style={{
              fontSize: '10px',
              fontWeight: 800,
              letterSpacing: '0.02em',
              color: isSelected ? '#38bdf8' : '#e2e8f0',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}>
              <span style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: probeColor,
                boxShadow: `0 0 6px ${probeColor}`,
                display: 'inline-block',
              }} />
              {sensor.label}
            </span>
            <span style={{
              fontSize: '8px',
              fontWeight: 800,
              padding: '1px 4px',
              borderRadius: '3px',
              background: `${probeColor}20`,
              color: probeColor,
              border: `1px solid ${probeColor}40`,
            }}>
              {statusBadge}
            </span>
          </div>

          {/* Value row: Temperature Reading */}
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span style={{
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: '13px',
              fontWeight: 800,
              color: probeColor,
            }}>
              {temp !== null && temp !== undefined ? `${temp.toFixed(2)} °C` : 'N/A'}
            </span>
            <span style={{ fontSize: '9px', color: '#64748b' }}>
              ({sensor.id.split('-').pop()})
            </span>
          </div>
        </div>
      </Html>
    </group>
  );
}

// Insulated Shipper Container with Physical Compartment Layout
function InsulatedShipperBox({ vialCount }: { vialCount: number }) {
  // 3x3 grid coordinates: x in [-0.8, 0, 0.8], z in [-0.8, 0, 0.8]
  const slotCoords: [number, number, number][] = [
    [-0.8, 0.05, -0.8], [0.0, 0.05, -0.8], [0.8, 0.05, -0.8],
    [-0.8, 0.05, 0.0],  [0.0, 0.05, 0.0],  [0.8, 0.05, 0.0],
    [-0.8, 0.05, 0.8],  [0.0, 0.05, 0.8],  [0.8, 0.05, 0.8],
  ];

  return (
    <group>
      {/* Outer Cryo Shipper Box Shell */}
      <mesh position={[0, -0.05, 0]}>
        <boxGeometry args={[3.2, 1.2, 3.2]} />
        <meshStandardMaterial
          color="#0b1322"
          roughness={0.7}
          metalness={0.2}
        />
      </mesh>

      {/* Insulated Wall Edges Accent Border */}
      <mesh position={[0, 0.54, 0]}>
        <boxGeometry args={[3.22, 0.04, 3.22]} />
        <meshStandardMaterial color="#0284c7" metalness={0.6} roughness={0.3} />
      </mesh>

      {/* Vacuum Insulated Panel (VIP) Inner Lining */}
      <mesh position={[0, 0.0, 0]}>
        <boxGeometry args={[2.85, 1.15, 2.85]} />
        <meshStandardMaterial
          color="#1e293b"
          roughness={0.4}
          metalness={0.6}
        />
      </mesh>

      {/* Internal Tray Cavity Floor */}
      <mesh position={[0, -0.05, 0]}>
        <boxGeometry args={[2.5, 0.15, 2.5]} />
        <meshStandardMaterial color="#0f172a" roughness={0.9} />
      </mesh>

      {/* Shipper Structural Label Tag */}
      <Html position={[0, 0.62, 1.62]} center distanceFactor={7}>
        <div style={{
          fontSize: '9px',
          fontWeight: 800,
          background: 'rgba(2, 132, 199, 0.95)',
          color: '#fff',
          padding: '2px 8px',
          borderRadius: '3px',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          pointerEvents: 'none',
          boxShadow: '0 2px 8px rgba(0,0,0,0.6)',
        }}>
          Cryo-Shipper Chamber (3x3 Matrix)
        </div>
      </Html>

      {/* 9 Tray Slots / Vial Wells */}
      {slotCoords.map((pos, idx) => {
        const isOccupied = idx < vialCount;
        return (
          <group key={idx}>
            {/* Cylindrical Well Recess */}
            <mesh position={[pos[0], 0.02, pos[2]]}>
              <cylinderGeometry args={[0.28, 0.28, 0.06, 24]} />
              <meshStandardMaterial
                color={isOccupied ? '#090d16' : '#1e293b'}
                roughness={0.8}
                metalness={0.2}
              />
            </mesh>

            {/* Render vial if position is occupied */}
            {isOccupied && <BiologicVial position={pos} index={idx} />}

            {/* Empty slot indicator */}
            {!isOccupied && (
              <Html position={[pos[0], 0.12, pos[2]]} center distanceFactor={7.5}>
                <div style={{
                  fontSize: '8px',
                  fontWeight: 600,
                  color: '#475569',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                  pointerEvents: 'none',
                }}>
                  Slot #{idx + 1}
                </div>
              </Html>
            )}
          </group>
        );
      })}
    </group>
  );
}

export const Package3D: React.FC<Package3DProps> = ({
  vialCount,
  sensors,
  selectedSensorId,
  onSelectSensor,
  lowerLimitC,
  upperLimitC,
}) => {
  return (
    <div style={{ width: '100%', height: '100%', minHeight: '420px', position: 'relative' }}>
      <Canvas
        camera={{ position: [4.4, 3.8, 4.4], fov: 44 }}
        gl={{ antialias: true, alpha: true }}
        style={{ borderRadius: '14px', background: 'radial-gradient(circle, #0a1424 0%, #050b14 100%)' }}
      >
        <ambientLight intensity={0.9} />
        <directionalLight position={[6, 9, 6]} intensity={1.5} castShadow />
        <directionalLight position={[-6, 5, -6]} intensity={0.6} color="#38bdf8" />
        <pointLight position={[0, 2.5, 0]} intensity={0.8} color="#06b6d4" />

        {/* 3D Package Container with 3x3 Vials */}
        <InsulatedShipperBox vialCount={vialCount} />

        {/* Clear Outboard Sensor Markers with Leader Lines */}
        {sensors.map((sensor, idx) => (
          <SensorMarker3D
            key={sensor.id}
            sensor={sensor}
            index={idx}
            totalSensors={sensors.length}
            isSelected={selectedSensorId === sensor.id}
            onClick={() => onSelectSensor?.(sensor.id)}
            lowerLimitC={lowerLimitC}
            upperLimitC={upperLimitC}
          />
        ))}

        <OrbitControls
          enablePan={false}
          minDistance={2.8}
          maxDistance={9.5}
          maxPolarAngle={Math.PI / 2.05} // prevent camera going underneath
        />
      </Canvas>

      {/* Floating 3D Navigation Controls Hint */}
      <div style={{
        position: 'absolute',
        bottom: '12px',
        left: '12px',
        background: 'rgba(5, 11, 20, 0.85)',
        backdropFilter: 'blur(8px)',
        border: '1px solid rgba(148, 163, 184, 0.2)',
        borderRadius: '6px',
        padding: '5px 12px',
        fontSize: '11px',
        color: '#94a3b8',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        pointerEvents: 'none',
        boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
      }}>
        <span>🖱️ Drag to rotate 3D view</span>
        <span>•</span>
        <span>Scroll to zoom</span>
        <span>•</span>
        <span>Click any sensor callout to inspect</span>
      </div>

      {/* Top Right Legend / Status Guide */}
      <div style={{
        position: 'absolute',
        top: '12px',
        right: '12px',
        background: 'rgba(5, 11, 20, 0.85)',
        backdropFilter: 'blur(8px)',
        border: '1px solid rgba(148, 163, 184, 0.2)',
        borderRadius: '6px',
        padding: '6px 10px',
        fontSize: '10px',
        color: '#cbd5e1',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        pointerEvents: 'none',
      }}>
        <div style={{ fontWeight: 700, color: '#38bdf8', fontSize: '10px', marginBottom: '2px' }}>
          PROBE STATUS LEGEND
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981' }} />
          <span>In Envelope (Safe)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#f43f5e' }} />
          <span>Thermal Breach</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#f59e0b' }} />
          <span>Sensor Fault</span>
        </div>
      </div>
    </div>
  );
};
