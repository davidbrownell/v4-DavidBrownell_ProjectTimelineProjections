export default {
  "transform": {
    "\\.svelte$": "jest-transform-svelte",
    "^.+\\.ts$": "ts-jest"
  },
  "moduleFileExtensions": [
    "js",
    "ts",
    "svelte"
  ],
  "setupFilesAfterEnv": ["<rootDir>/node_modules/@testing-library/jest-dom/"],
  "testPathIgnorePatterns": [
    "node_modules"
  ],
  "transformIgnorePatterns": [
    "node_modules"
  ],
  "clearMocks": true,
  "collectCoverage": false,
  "verbose": true
  };
