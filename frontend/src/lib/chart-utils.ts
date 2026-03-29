import type { ChartOptions, ScaleOptionsByType } from 'chart.js';
import { THEME } from './constants';

type ScaleOptions = Partial<ScaleOptionsByType<'category' | 'linear'>>;

const baseScale: ScaleOptions = {
  ticks: { color: THEME.textMuted },
  grid: { color: THEME.gridColor },
};

const hiddenGridScale: ScaleOptions = {
  ticks: { color: THEME.textMuted },
  grid: { display: false },
};

export function createScales(options: {
  xGrid?: boolean;
  yGrid?: boolean;
  stacked?: boolean;
  xRotation?: number;
  yBeginAtZero?: boolean;
} = {}): ChartOptions['scales'] {
  const { xGrid = true, yGrid = true, stacked = false, xRotation, yBeginAtZero = true } = options;

  return {
    x: {
      ...(xGrid ? baseScale : hiddenGridScale),
      ...(stacked && { stacked: true }),
      ...(xRotation && { ticks: { ...baseScale.ticks, maxRotation: xRotation } }),
    },
    y: {
      ...(yGrid ? baseScale : hiddenGridScale),
      ...(stacked && { stacked: true }),
      ...(yBeginAtZero && { beginAtZero: true }),
    },
  };
}

export function createLegend(options: {
  display?: boolean;
  position?: 'top' | 'bottom' | 'left' | 'right';
} = {}) {
  const { display = true, position = 'top' } = options;

  if (!display) return { display: false };

  return {
    display: true,
    position,
    labels: { color: THEME.textMuted, usePointStyle: true, padding: 16 },
  };
}

export const baseChartOptions: Partial<ChartOptions> = {
  responsive: true,
  maintainAspectRatio: false,
};
