import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
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
          opacity={0.65}
          roughness={0.1}
          metalness={0.1}
          transmission={0.6}
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
          emissiveIntensity={0.2}
        />
      </mesh>

      {/* Rubber Stopper & Crimped Aluminum Seal */}
      <mesh position={[0, 0.72, 0]}>
        <cylinderGeometry args={[0.15, 0.15, 0.08, 24]} />
        <meshStandardMaterial color="#64748b" metalness={0.7} roughness={0.3} />
      </mesh>
      {/* Color-coded Flip-off Cap */}
      <mesh position={[0, 0.78, 0]}>
        <cylinderGeometry args={[0.17, 0.17, 0.06, 24]} />
        <meshStandardMaterial color="#0ea5e9" roughness={0.4} />
      </mesh>

      {/* Vial Label */}
      <Html position={[0, -0.15, 0.25]} center distanceFactor={7}>
        <div style={{
          fontSize: '9px',
          fontWeight: 600,
          background: 'rgba(15, 23, 42, 0.85)',
          color: '#cbd5e1',
          padding: '1px 4px',
          borderRadius: '3px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          whiteSpace: 'nowrap',
          pointerEvents: 'none',
        }}>
          Vial #{index + 1}
        </div>
      </Html>
    </group>
  );
}

// Independent Sensor Marker
function SensorMarker3D({
  sensor,
  isSelected,
  onClick,
  lowerLimitC,
  upperLimitC,
}: {
  sensor: Sensor;
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
  if (sensor.health_status !== 'healthy') {
    probeColor = '#f59e0b'; // amber warning
    emissiveColor = '#d97706';
  } else if (temp !== null && temp !== undefined) {
    if (temp > upperLimitC) {
      probeColor = '#f43f5e'; // red breach
      emissiveColor = '#e11d48';
    } else if (temp < lowerLimitC) {
      probeColor = '#38bdf8'; // deep cold blue
      emissiveColor = '#0284c7';
    } else {
      probeColor = '#10b981'; // green normal
      emissiveColor = '#059669';
    }
  }

  return (
    <group
      position={[sensor.position_x, sensor.position_y, sensor.position_z]}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      {/* Probe Stem */}
      <mesh position={[0, -0.2, 0]}>
        <cylinderGeometry args={[0.03, 0.03, 0.4, 16]} />
        <meshStandardMaterial color="#94a3b8" metalness={0.8} roughness={0.2} />
      </mesh>

      {/* Sensor Head Bulb */}
      <mesh scale={isSelected || hovered ? 1.4 : 1.0}>
        <sphereGeometry args={[0.12, 24, 24]} />
        <meshStandardMaterial
          color={probeColor}
          emissive={emissiveColor}
          emissiveIntensity={isSelected || hovered ? 0.9 : 0.4}
          roughness={0.2}
          metalness={0.5}
        />
      </mesh>

      {/* Outer Glow Halo Ring when selected */}
      {(isSelected || hovered) && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.18, 0.22, 32]} />
          <meshBasicMaterial color={probeColor} side={THREE.DoubleSide} transparent opacity={0.8} />
        </mesh>
      )}

      {/* Floating Info Pill */}
      <Html position={[0, 0.32, 0]} center distanceFactor={6}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '2px 6px',
            borderRadius: '4px',
            fontSize: '10px',
            fontWeight: 700,
            background: isSelected ? 'rgba(6, 182, 212, 0.95)' : 'rgba(15, 23, 42, 0.9)',
            color: isSelected ? '#000' : '#f8fafc',
            border: `1px solid ${isSelected ? '#38bdf8' : 'rgba(255, 255, 255, 0.15)'}`,
            boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
            cursor: 'pointer',
            userSelect: 'none',
            whiteSpace: 'nowrap',
          }}
          onClick={onClick}
        >
          <span>{sensor.label.split(' ')[0]}</span>
          <span style={{ color: isSelected ? '#000' : probeColor }}>
            {temp !== null && temp !== undefined ? `${temp.toFixed(1)}°C` : 'N/A'}
          </span>
        </div>
      </Html>
    </group>
  );
}

// Insulated Cryogenic Shipper Container & 3x3 Tray
function InsulatedShipperBox({ vialCount }: { vialCount: number }) {
  // 3x3 grid coordinates: x in [-0.9, 0, 0.9], z in [-0.9, 0, 0.9]
  const slotCoords: [number, number, number][] = [
    [-0.8, 0.05, -0.8], [0.0, 0.05, -0.8], [0.8, 0.05, -0.8],
    [-0.8, 0.05, 0.0],  [0.0, 0.05, 0.0],  [0.8, 0.05, 0.0],
    [-0.8, 0.05, 0.8],  [0.0, 0.05, 0.8],  [0.8, 0.05, 0.8],
  ];

  return (
    <group>
      {/* Outer Cryo Shipper Box Shell (Dark Technical Composite) */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[3.2, 1.3, 3.2]} />
        <meshStandardMaterial
          color="#0f172a"
          roughness={0.6}
          metalness={0.3}
          wireframe={false}
        />
      </mesh>

      {/* Vacuum Insulated Layer (VIP Metallic Foil Rim) */}
      <mesh position={[0, 0.02, 0]}>
        <boxGeometry args={[2.9, 1.25, 2.9]} />
        <meshStandardMaterial
          color="#334155"
          roughness={0.3}
          metalness={0.7}
        />
      </mesh>

      {/* Internal Tray Bed (Polyurethane Cavity) */}
      <mesh position={[0, -0.05, 0]}>
        <boxGeometry args={[2.5, 0.2, 2.5]} />
        <meshStandardMaterial color="#1e293b" roughness={0.8} />
      </mesh>

      {/* 9 Tray Slots / Vial Wells */}
      {slotCoords.map((pos, idx) => {
        const isOccupied = idx < vialCount;
        return (
          <group key={idx}>
            {/* Cylindrical Well Recess */}
            <mesh position={[pos[0], 0.02, pos[2]]}>
              <cylinderGeometry args={[0.28, 0.28, 0.06, 24]} />
              <meshStandardMaterial
                color={isOccupied ? '#0f172a' : '#1e293b'}
                roughness={0.9}
                metalness={0.1}
              />
            </mesh>

            {/* If slot is occupied, render biologic vial */}
            {isOccupied && <BiologicVial position={pos} index={idx} />}

            {/* If slot is empty, show visual vacant marker */}
            {!isOccupied && (
              <Html position={[pos[0], 0.1, pos[2]]} center distanceFactor={8}>
                <div style={{
                  fontSize: '8px',
                  color: '#64748b',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                  opacity: 0.6,
                }}>
                  Empty #{idx + 1}
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
    <div style={{ width: '100%', height: '100%', minHeight: '380px', position: 'relative' }}>
      <Canvas
        camera={{ position: [3.8, 3.2, 3.8], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ borderRadius: '14px', background: 'radial-gradient(circle, #0a1424 0%, #050b14 100%)' }}
      >
        <ambientLight intensity={0.8} />
        <directionalLight position={[5, 8, 5]} intensity={1.4} castShadow />
        <directionalLight position={[-5, 4, -5]} intensity={0.5} color="#38bdf8" />
        <pointLight position={[0, 2, 0]} intensity={0.6} color="#06b6d4" />

        {/* 3D Package Container with 3x3 Vials */}
        <InsulatedShipperBox vialCount={vialCount} />

        {/* Independent Sensor Markers */}
        {sensors.map((sensor) => (
          <SensorMarker3D
            key={sensor.id}
            sensor={sensor}
            isSelected={selectedSensorId === sensor.id}
            onClick={() => onSelectSensor?.(sensor.id)}
            lowerLimitC={lowerLimitC}
            upperLimitC={upperLimitC}
          />
        ))}

        <OrbitControls
          enablePan={false}
          minDistance={2.5}
          maxDistance={8}
          maxPolarAngle={Math.PI / 2.05} // prevent going underneath
        />
      </Canvas>

      {/* Floating 3D Navigation Controls Hint */}
      <div style={{
        position: 'absolute',
        bottom: '12px',
        left: '12px',
        background: 'rgba(5, 11, 20, 0.75)',
        backdropFilter: 'blur(8px)',
        border: '1px solid rgba(148, 163, 184, 0.15)',
        borderRadius: '6px',
        padding: '4px 10px',
        fontSize: '11px',
        color: '#94a3b8',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        pointerEvents: 'none',
      }}>
        <span>🖱️ Drag to rotate</span>
        <span>•</span>
        <span>Scroll to zoom</span>
        <span>•</span>
        <span>Click probe to inspect</span>
      </div>
    </div>
  );
};
