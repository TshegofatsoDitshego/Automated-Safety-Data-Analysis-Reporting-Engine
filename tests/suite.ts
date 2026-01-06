
import { runAuthTests } from './auth';
import { runSensorTests } from './sensors';

export type TestResult = {
  name: string;
  passed: boolean;
  message?: string;
};

/**
 * Master test runner. 
 * Human Note: This is how we keep the index.tsx clean while having 
 * enterprise-grade testing coverage.
 */
export const runTestSuite = (): TestResult[] => {
  const results: TestResult[] = [];

  const assert = (name: string, condition: boolean, message?: string) => {
    results.push({ name, passed: condition, message });
  };

  // Run modules
  runAuthTests(assert);
  runSensorTests(assert);

  // System-level Sanity Checks
  assert("System: Logic module loaded", typeof runAuthTests === 'function');

  return results;
};
