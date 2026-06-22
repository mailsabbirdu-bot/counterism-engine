/**
 * Sanitizes potential NaN or undefined values for Remotion CSS properties.
 * Falls back to a provided default value.
 */
export const safeNumber = (val: any, fallback: number = 0): number => {
  const num = Number(val);
  return isNaN(num) ? fallback : num;
};
