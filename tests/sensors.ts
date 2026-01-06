
import { getReadingStatus } from '../logic';

/**
 * Sensor Threshold & Safety Logic Tests
 * Thorough coverage for all gas types and boundary conditions.
 */
export const runSensorTests = (assert: (name: string, cond: boolean) => void) => {
  
  // 1. Carbon Monoxide (CO)
  assert("CO: Normal reading (25ppm)", getReadingStatus(25, 'CO') === 'normal');
  assert("CO: Warning reading (40ppm)", getReadingStatus(40, 'CO') === 'warning');
  assert("CO: Critical reading (60ppm)", getReadingStatus(60, 'CO') === 'critical');
  assert("CO: Exact boundary check (35ppm)", getReadingStatus(35, 'CO') === 'normal');
  assert("CO: Exact boundary check (50ppm)", getReadingStatus(50, 'CO') === 'warning');

  // 2. Hydrogen Sulfide (H2S)
  assert("H2S: Safe reading (5ppm)", getReadingStatus(5, 'H2S') === 'normal');
  assert("H2S: Exposure warning (12ppm)", getReadingStatus(12, 'H2S') === 'warning');
  assert("H2S: Deadly concentration (20ppm)", getReadingStatus(20, 'H2S') === 'critical');

  // 3. Oxygen (O2) - Dual Boundary Logic
  assert("O2: Atmospheric normal (20.9%)", getReadingStatus(20.9, 'O2') === 'normal');
  
  // Lower bounds (Depletion)
  assert("O2: Low warning (20.0%)", getReadingStatus(20, 'O2') === 'warning');
  assert("O2: Low critical (19.0%)", getReadingStatus(19, 'O2') === 'critical');
  
  // Upper bounds (Enrichment)
  assert("O2: High warning (23.0%)", getReadingStatus(23, 'O2') === 'warning');
  assert("O2: High critical (24.0%)", getReadingStatus(24, 'O2') === 'critical');

  // 4. Lower Explosive Limit (LEL)
  assert("LEL: Zero baseline", getReadingStatus(0, 'LEL') === 'normal');
  assert("LEL: Combustion warning (15%)", getReadingStatus(15, 'LEL') === 'warning');
  assert("LEL: Explosive risk (25%)", getReadingStatus(25, 'LEL') === 'critical');

  // 5. Robustness - Unknown Sensor Type
  assert("System: Graceful handle unknown gas", getReadingStatus(100, 'XENON') === 'normal');
};
