module.exports = {
    preset: 'jest-puppeteer',
    testTimeout: 30000,
    coverageDirectory: 'coverage',
    collectCoverage: true,
    testEnvironment: 'node',
    transform: {
        '^.+\\.ts$': 'ts-jest',  // Ensure ts-jest is used for .ts files
    },
    moduleFileExtensions: ['ts', 'js'],
    testPathIgnorePatterns: ['/node_modules/'],
    transformIgnorePatterns: ['/node_modules/'],
};

