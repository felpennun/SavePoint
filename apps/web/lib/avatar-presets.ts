/** The built-in SavePoint avatars: the gradient hue each one starts from. */
export const AVATAR_PRESET_HUES = ["var(--color-accent-edge)", "#3f5f86", "#3d6a52", "#7a5a2d", "#6b3540"];

export function presetGradient(index: number | null | undefined): string | undefined {
  if (index === null || index === undefined || !AVATAR_PRESET_HUES[index]) return undefined;
  return `linear-gradient(150deg, ${AVATAR_PRESET_HUES[index]}, #3f424d)`;
}
