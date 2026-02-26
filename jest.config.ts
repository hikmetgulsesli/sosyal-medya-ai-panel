import type { Config } from "jest";

const config: Config = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  testMatch: ["**/*.test.ts", "**/*.test.tsx"],
  transform: {
    "^.+\\.tsx?$": ["ts-jest", {
      tsconfig: {
        jsx: "react-jsx",
      },
    }],
  },
};

export default config;
