import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

const dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    // Mirrors tsconfig.json's "paths": {"@/*": ["./*"]} -- Vitest doesn't
    // read tsconfig path mappings itself, so both must be kept in sync.
    alias: {
      "@": dirname,
    },
  },
  test: {
    include: [
      "tests/**/*.test.ts",
      "tests/**/*.test.tsx",
      "app/**/__tests__/*.test.ts",
      "components/**/__tests__/*.test.tsx",
      "lib/**/__tests__/*.test.ts",
    ],
    passWithNoTests: false,
    reporters: ["default"],
  },
});
