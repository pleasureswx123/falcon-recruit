"use client"

import * as React from "react"

import type { DimensionScore, ScoreDimension } from "@/lib/api/reports"
import { DIMENSION_ORDER } from "@/lib/api/reports"

interface Props {
  dimensions: DimensionScore[]
  size?: number
}

/**
 * 纯 SVG 雷达图（零依赖）。五维固定顺序渲染，缺失维度补 0。
 * 坐标系：中心 (cx, cy) 半径 r，轴按 -90° 起顺时针均匀分布。
 */
export function ScoreRadar({ dimensions, size = 320 }: Props) {
  const padding = 40
  const cx = size / 2
  const cy = size / 2
  const r = size / 2 - padding

  const byDim = React.useMemo(() => {
    const map = new Map<ScoreDimension, DimensionScore>()
    dimensions.forEach((d) => map.set(d.dimension, d))
    return map
  }, [dimensions])

  const axes = DIMENSION_ORDER.map((dim, i) => {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / DIMENSION_ORDER.length
    const d = byDim.get(dim)
    return {
      dim,
      angle,
      score: d?.score ?? 0,
      label: d?.label ?? dim,
    }
  })

  // 多层网格（20/40/60/80/100）
  const rings = [0.2, 0.4, 0.6, 0.8, 1]

  function polar(ratio: number, angle: number): [number, number] {
    return [cx + r * ratio * Math.cos(angle), cy + r * ratio * Math.sin(angle)]
  }

  const polygonPoints = axes
    .map((a) => {
      const [x, y] = polar(a.score / 100, a.angle)
      return `${x},${y}`
    })
    .join(" ")

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className="h-full w-full"
      role="img"
      aria-label="五维评分雷达图"
    >
      {/* 背景同心环 */}
      {rings.map((ratio, idx) => {
        const pts = axes
          .map((a) => polar(ratio, a.angle).join(","))
          .join(" ")
        return (
          <polygon
            key={idx}
            points={pts}
            className="fill-transparent stroke-muted"
            strokeWidth={1}
            strokeDasharray={idx === rings.length - 1 ? undefined : "2 3"}
          />
        )
      })}

      {/* 轴线 */}
      {axes.map((a) => {
        const [x, y] = polar(1, a.angle)
        return (
          <line
            key={a.dim}
            x1={cx}
            y1={cy}
            x2={x}
            y2={y}
            className="stroke-muted"
            strokeWidth={1}
          />
        )
      })}

      {/* 候选人得分多边形 */}
      <polygon
        points={polygonPoints}
        className="fill-indigo-500/20 stroke-indigo-500"
        strokeWidth={2}
      />

      {/* 顶点圆点 */}
      {axes.map((a) => {
        const [x, y] = polar(a.score / 100, a.angle)
        return (
          <circle
            key={`dot-${a.dim}`}
            cx={x}
            cy={y}
            r={3.5}
            className="fill-indigo-500"
          />
        )
      })}

      {/* 维度标签 */}
      {axes.map((a) => {
        const [lx, ly] = polar(1.18, a.angle)
        const anchor =
          Math.abs(Math.cos(a.angle)) < 0.2
            ? "middle"
            : Math.cos(a.angle) > 0
            ? "start"
            : "end"
        return (
          <g key={`lbl-${a.dim}`}>
            <text
              x={lx}
              y={ly}
              textAnchor={anchor}
              dominantBaseline="middle"
              className="fill-foreground text-[11px] font-medium"
            >
              {a.label}
            </text>
            <text
              x={lx}
              y={ly + 14}
              textAnchor={anchor}
              dominantBaseline="middle"
              className="fill-muted-foreground text-[10px]"
            >
              {a.score}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
