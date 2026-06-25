import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "../../docs/api/openapi.json",
  output: {
    path: "src/client",
    postProcess: ["prettier"],
  },
  plugins: [
    "@hey-api/typescript",
    {
      name: "@hey-api/client-fetch",
      bundle: true,
    },
    "@hey-api/sdk",
  ],
});
