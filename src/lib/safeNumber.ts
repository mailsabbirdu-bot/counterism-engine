/**
 * Conversions between Bangla and English digits.
 */
export const banglaToEnglishDigits = (str: string): string => {
  return str.replace(/[০-৯]/g, (m) => String(['০','১','২','৩','৪','৫','৬','৭','৮','৯'].indexOf(m)));
};

export const englishToBanglaDigits = (str: string): string => {
  return str.replace(/[0-9]/g, (m) => ['০','১','২','৩','৪','৫','৬','৭','৮','৯'][Number(m)]);
};

export const hasBanglaDigits = (str: string): boolean => {
  return /[০-৯]/.test(str);
};

/**
 * Sanitizes potential NaN or undefined values for Remotion CSS properties.
 * Falls back to a provided default value.
 * Also parses Bangla numerals and handles formatting characters.
 */
export const safeNumber = (val: any, fallback: number = 0): number => {
  if (val === undefined || val === null) return fallback;
  if (typeof val === 'number') return isNaN(val) ? fallback : val;

  const str = String(val).trim();
  const hasBangla = hasBanglaDigits(str);
  const cleanStr = hasBangla ? banglaToEnglishDigits(str) : str;

  // Remove commas to avoid parsing issues
  const withoutCommas = cleanStr.replace(/,/g, '');

  // Extract first numeric match (including minus, decimals)
  const match = withoutCommas.match(/-?\d+(\.\d+)?/);
  if (match) {
    const num = Number(match[0]);
    return isNaN(num) ? fallback : num;
  }
  return fallback;
};

/**
 * Checks if a value represents a purely numeric or simple percentage-like value.
 * Compounds with words (like "১৮ লাখ") return false to prevent truncating/formatting bugs.
 */
export const isNumericValue = (val: any): boolean => {
  if (val === undefined || val === null) return false;
  if (typeof val === 'number') return !isNaN(val);

  const str = String(val).trim();
  const hasBangla = hasBanglaDigits(str);
  const cleanStr = (hasBangla ? banglaToEnglishDigits(str) : str).replace(/,/g, '');

  // Strip optional trailing '%' or '+' symbols
  const strictlyNumeric = cleanStr.replace(/[%\+]$/, '').trim();
  return /^-?\d+(\.\d+)?$/.test(strictlyNumeric);
};

/**
 * Formats an animated number value with the correct precision, locale commas, and Bangla digits
 * depending on the format of the original string.
 */
export const formatWithLocaleAndBangla = (currentValue: number, originalValue: any, precision: number = 0): string => {
  if (originalValue === undefined || originalValue === null) {
    return String(Math.round(currentValue));
  }

  const origStr = String(originalValue).trim();
  const hasBangla = hasBanglaDigits(origStr);

  // Detect precision from original value if precision is not explicitly provided
  let detectedPrecision = precision;
  if (precision === 0 && origStr.includes('.')) {
    const cleanOrig = hasBangla ? banglaToEnglishDigits(origStr) : origStr;
    const parts = cleanOrig.split('.');
    if (parts.length > 1) {
      const match = parts[1].match(/^\d+/);
      if (match) {
        detectedPrecision = match[0].length;
      }
    }
  }

  let numStr = currentValue.toFixed(detectedPrecision);

  // Check if original had commas
  const hasCommas = origStr.includes(',');
  if (hasCommas) {
    const parts = numStr.split('.');
    const localeStr = hasBangla ? 'bn-BD' : 'en-US';
    try {
      const integerPart = Number(parts[0]).toLocaleString(localeStr);
      numStr = parts.length > 1 ? `${integerPart}.${parts[1]}` : integerPart;
    } catch (e) {
      // Fallback if toLocaleString fails or lacks support
      const integerPart = Number(parts[0]).toLocaleString('en-US');
      numStr = parts.length > 1 ? `${integerPart}.${parts[1]}` : integerPart;
    }
  }

  if (hasBangla) {
    return englishToBanglaDigits(numStr);
  }
  return numStr;
};
