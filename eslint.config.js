import js from "@eslint/js";
export default [
    { ignores: ["**/dist/**", "**/node_modules/**", "**/venv/**"] },
    js.configs.recommended,
    {
        languageOptions: {
            ecmaVersion: 2021,
            sourceType: "module",
        }
    }
];
