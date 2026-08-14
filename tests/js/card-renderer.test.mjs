// Card markup is built by string concatenation and handed to innerHTML, so
// every interpolated field is an injection site. Word text, translation and
// category are all user editable through PUT /words/{id}, and examples and
// synonyms arrive from the language model.
//
// Run with: node tests/js/card-renderer.test.mjs

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

function loadRenderer() {
    const shared = fs.readFileSync(path.join(root, "app/static/js/shared.js"), "utf8");
    const renderer = fs.readFileSync(
        path.join(root, "app/static/js/card-renderer.js"),
        "utf8",
    );
    // shared.js touches document and window only inside functions the renderer
    // never calls, so an empty stub is enough to evaluate both files.
    const source = `
        const document = {getElementById: () => ({classList: {toggle: () => {}}})};
        const window = {speechSynthesis: {cancel: () => {}, getVoices: () => []}};
        ${shared}
        ${renderer}
        return renderWordCard;
    `;
    return new Function(source)();
}

const renderWordCard = loadRenderer();

function makeWord(overrides = {}) {
    return {
        id: 1,
        word: "take off",
        translation: "злітати",
        examples: "The plane took off.",
        synonyms: "depart",
        category: "Verbs",
        level: "A1",
        rank: 100,
        frequency_group: "Core 500",
        type: "word",
        is_learned: false,
        ...overrides,
    };
}

let failures = 0;

function check(name, condition, detail = "") {
    if (condition) {
        console.log(`ok   ${name}`);
    } else {
        failures++;
        console.log(`FAIL ${name}${detail ? `\n     ${detail}` : ""}`);
    }
}

// A payload that becomes an executing element the moment it reaches innerHTML.
const IMG_PAYLOAD = '<img src=x onerror=alert(1)>';

for (const field of ["word", "translation", "examples", "synonyms", "category"]) {
    const html = renderWordCard(makeWord({ [field]: IMG_PAYLOAD }));
    check(
        `${field} does not render a live tag`,
        !html.includes("<img src=x"),
        `found the raw payload in the output for ${field}`,
    );
}

// A double quote closes an HTML attribute, which lets the rest of the payload
// become new attributes. Single-quote escaping alone does not stop this.
const QUOTE_PAYLOAD = 'a" onmouseover="alert(1)';

for (const field of ["word", "translation", "category"]) {
    const html = renderWordCard(makeWord({ [field]: QUOTE_PAYLOAD }));
    // An escaped payload still contains the text "onmouseover=", but followed
    // by &quot; rather than a real quote, so it stays inside the value. Only
    // an unescaped quote actually opens a new attribute.
    check(
        `${field} cannot break out of an attribute`,
        !html.includes('onmouseover="'),
        `payload became a new attribute for ${field}`,
    );
}

// Escaping must not mangle ordinary content.
const plain = renderWordCard(makeWord());
check("renders the word", plain.includes("take off"));
check("renders the translation", plain.includes("злітати"));
check("renders the example", plain.includes("The plane took off."));
check("keeps ampersands readable", renderWordCard(makeWord({ word: "cause & effect" })).includes("cause &amp; effect"));

console.log(failures === 0 ? "\nALL PASS" : `\n${failures} FAILED`);
process.exit(failures === 0 ? 0 : 1);
