
import { validatePassword, getStrength } from '../logic';

/**
 * Authentication & Security Logic Tests
 * Human Note: These tests ensure we don't accidentally weaken the security requirements.
 */
export const runAuthTests = (assert: (name: string, cond: boolean) => void) => {
  // 1. Password Complexity - Standard Cases
  assert("Auth: Detects password length < 8", validatePassword("Pass1!").length === false);
  assert("Auth: Detects missing uppercase letter", validatePassword("password123!").upper === false);
  assert("Auth: Detects missing lowercase letter", validatePassword("PASSWORD123!").lower === false);
  assert("Auth: Detects missing numeric character", validatePassword("Password!").number === false);
  assert("Auth: Detects missing special character", validatePassword("Password123").special === false);
  assert("Auth: Accepts full complexity password", validatePassword("Safety@Pulse2024").length === true);

  // 2. Password Strength Meter - Score Edge Cases
  assert("Strength: 'Weak' for single char", getStrength("a").score === 1);
  assert("Strength: 'Weak' for 7 chars simple", getStrength("abcdefg").score === 1);
  
  const med = getStrength("Password1"); // Length, Upper, Lower, Number = 4 points
  assert("Strength: 'Medium' for partial set", med.score === 2);
  assert("Strength: 'Medium' label matches", med.label === 'Medium');

  const strong = getStrength("Safety@2024"); // Length, Upper, Lower, Number, Special = 5 points
  assert("Strength: 'Strong' for full set", strong.score === 3);
  assert("Strength: 'Strong' color is green", strong.color === 'bg-green-500');

  // 3. Robustness - Empty Inputs
  const empty = validatePassword("");
  assert("Auth: Empty string fails all checks", 
    !empty.length && !empty.upper && !empty.lower && !empty.number && !empty.special
  );
};
