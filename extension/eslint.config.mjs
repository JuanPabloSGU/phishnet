import globals from "globals";
import pluginJs from "@eslint/js";
import tseslint from "typescript-eslint";

export default [
    {
        ignores: [
            "webpack.config.js",
            "**/dist/*",
            "**/node_modules/*",
            "**/test/*",
            "jest.config.js"
        ]
    },
    {
        files: ["**/*.{js,mjs,cjs,ts}"],
        languageOptions: {
            globals: {
                ...globals.browser,
                chrome: 'readonly',
            },
        },
    },
    pluginJs.configs.recommended,
    ...tseslint.configs.recommended,
];

