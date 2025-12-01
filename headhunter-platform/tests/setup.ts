import { PrismaClient } from '@prisma/client';

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.DATABASE_URL = process.env.TEST_DATABASE_URL || 'postgresql://test:test@localhost:5432/headhunter_test';
process.env.JWT_SECRET = 'test-jwt-secret-key';
process.env.JWT_EXPIRES_IN = '1h';

// Global test setup
beforeAll(async () => {
  // Database setup for tests would go here
  console.log('Setting up test environment...');
});

afterAll(async () => {
  // Cleanup after all tests
  console.log('Cleaning up test environment...');
});

// Extend Jest matchers if needed
expect.extend({
  toBeValidToken(received: string) {
    const pass = typeof received === 'string' && received.length > 10;
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid token`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid token`,
        pass: false,
      };
    }
  },
});

declare global {
  namespace jest {
    interface Matchers<R> {
      toBeValidToken(): R;
    }
  }
}