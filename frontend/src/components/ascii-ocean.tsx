"use client";

import { useEffect, useRef } from "react";
import { OceanEngine, type AsciiPalette, type SharkSpec } from "@/lib/ascii-sharks";
import { cn } from "@/lib/utils";

/**
 * ASCII 海洋動畫背景（來源：stackedlol/ascii-sharks，MIT）。
 * 色票從 CSS `--ascii-*` semantic tokens 讀取，跟隨 UI Theme。
 */

function parseRgbTriplet(raw: string): [number, number, number] | null {
  const parts = raw.trim().split(/[\s,]+/).map(Number);
  if (parts.length >= 3 && parts.every((n) => Number.isFinite(n))) {
    return [parts[0], parts[1], parts[2]];
  }
  return null;
}

function readAsciiPalette(el: Element): AsciiPalette {
  const cs = getComputedStyle(el);
  const bg = cs.getPropertyValue("--ascii-bg").trim() || "#000000";
  const grid = cs.getPropertyValue("--ascii-grid").trim() || "rgba(255,255,255,0.055)";
  const accent = cs.getPropertyValue("--ascii-accent").trim() || "#91d44f";
  const d1 = parseRgbTriplet(cs.getPropertyValue("--ascii-dot-1")) ?? [66, 169, 199];
  const d2 = parseRgbTriplet(cs.getPropertyValue("--ascii-dot-2")) ?? [145, 212, 79];
  const d3 = parseRgbTriplet(cs.getPropertyValue("--ascii-dot-3")) ?? [184, 212, 222];
  const d4 = parseRgbTriplet(cs.getPropertyValue("--ascii-dot-4")) ?? [200, 230, 240];
  const wake = parseRgbTriplet(cs.getPropertyValue("--ascii-wake")) ?? [145, 212, 79];
  const fish = parseRgbTriplet(cs.getPropertyValue("--ascii-fish")) ?? [200, 230, 245];
  return {
    bg,
    grid,
    dots: [d1, d2, d3, d4, wake],
    accents: [
      accent || "#8fbc63",
      "#5a9aaf",
      "#7a9e6a",
      "#6aafb8",
      "#8a9a7a",
      "#6a8aaa",
      "#a8b87a",
    ],
    fish,
  };
}

export function AsciiOcean({
  className,
  sharks,
}: {
  className?: string;
  sharks?: SharkSpec[];
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<OceanEngine | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const engine = new OceanEngine(canvas, sharks);
    engine.setPalette(readAsciiPalette(canvas));
    engineRef.current = engine;

    const apply = () => {
      engine.setPalette(readAsciiPalette(canvas));
    };

    const mo = new MutationObserver(apply);
    mo.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });

    return () => {
      mo.disconnect();
      engine.destroy();
      engineRef.current = null;
    };
    // 鯊魚陣容改變時重建 engine
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sharks]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={cn(
        "ascii-ocean pointer-events-none absolute inset-0 h-full w-full font-mono",
        className,
      )}
    />
  );
}
