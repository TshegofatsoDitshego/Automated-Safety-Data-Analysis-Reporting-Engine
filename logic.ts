
/**
 * SafetyPulse Core Logic Engine
 * 
 * Human Note: Extracted these from the main component because testing 
 * logic inside React components is a headache.
 */

export const validatePassword = (password: string) => {
  return {
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)
  };
};

export const getStrength = (p: string) => {
  const v = validatePassword(p);
  const count = Object.values(v).filter(Boolean).length;
  // Score-based mapping
  if (count <= 2) return { label: 'Weak', color: 'bg-red-500', width: '33%', score: 1 };
  if (count <= 4) return { label: 'Medium', color: 'bg-yellow-500', width: '66%', score: 2 };
  return { label: 'Strong', color: 'bg-green-500', width: '100%', score: 3 };
};

export const getReadingStatus = (value: number, type: string): 'normal' | 'warning' | 'critical' => {
  // Constants usually better in a separate config, but keeping here for simplicity for now.
  switch (type) {
    case 'CO':
      if (value > 50) return 'critical';
      if (value > 35) return 'warning';
      break;
    case 'H2S':
      if (value > 15) return 'critical';
      if (value > 10) return 'warning';
      break;
    case 'O2':
      // Oxygen is special - danger on both ends
      if (value < 19.5 || value > 23.5) return 'critical';
      if (value < 20.5 || value > 22.5) return 'warning';
      break;
    case 'LEL':
      if (value > 20) return 'critical';
      if (value > 10) return 'warning';
      break;
  }
  return 'normal';
};
