#!/usr/bin/env node

// Node imports
import fs from "node:fs";
import path from "node:path";
import { parseArgs } from "node:util";
import process from "node:process";
import { fileURLToPath } from "node:url";

// Third party imports
import {
  quicktype,
  InputData,
  JSONSchemaInput,
  FetchingJSONSchemaStore,
  splitIntoWords,
  combineWords,
  firstUpperWordStyle,
  allUpperWordStyle,
  legalizeCharacters,
  isLetterOrDigit,
} from "quicktype-core";
import { glob } from "glob";

const projectName = path.basename(process.cwd()).toLowerCase().replaceAll("-", "_");

const args = parseArgs({
  options: {
    startDir: { type: "string" },
    key: { type: "string" },
    separator: { type: "string" },
    prefix: { type: "string", default: projectName },
    requireResponse: { type: "boolean", default: false },
  },
});

console.log({ args });
const startDir = args.values.startDir;
const key = args.values.key;
const separator = args.values.separator;
const prefix = args.values.prefix;
const requireResponse = args.values.requireResponse;

const generatePython = startDir.split(path.sep).includes("src");
console.log("generatePython", generatePython);

const directoryPath = path.resolve(process.cwd(), startDir);
console.log("directoryPath", directoryPath);

const outputFile = path.join(process.cwd(), `${projectName}_schemas.json`);
const outputJsFile = path.join(process.cwd(), `${projectName}_typed_schemas.js`);
const outputTypesFile = path.join(process.cwd(), `${projectName}_typed_schemas.d.ts`);

const errorSchemaFile = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  "src",
  "opengeodeweb_microservice",
  "error.json",
);

// Route schema key holding the JSON schema of the success response body
const RESPONSE_KEY = "response";

// `"response": {"format": "binary"}`: the route streams a file instead of JSON
function isBinaryResponse(jsonData) {
  return jsonData[RESPONSE_KEY]?.format === "binary";
}

// Type name quicktype gives to a top-level source: Python and TypeScript (default "pascal" acronym style) both upper-case acronyms, e.g. picked_ids -> PickedIDS
function quicktypeName(name) {
  return combineWords(
    splitIntoWords(name),
    legalizeCharacters(isLetterOrDigit),
    firstUpperWordStyle,
    firstUpperWordStyle,
    allUpperWordStyle,
    allUpperWordStyle,
    "",
    isLetterOrDigit,
  );
}

function assertGeneratedTypes(content, typeNames, pattern) {
  for (const typeName of typeNames) {
    if (!pattern(typeName).test(content)) {
      throw new Error(`quicktype did not generate expected type ${typeName}`);
    }
  }
}

async function quicktypeJSONSchema(sources, lang, rendererOptions) {
  const schemaInput = new JSONSchemaInput(new FetchingJSONSchemaStore());
  for (const { name, schema } of sources) {
    await schemaInput.addSource({ name, schema });
  }
  const inputData = new InputData();
  inputData.addInput(schemaInput);
  return await quicktype({ inputData, lang, rendererOptions });
}

function requestSchemaString(jsonData, fileContent) {
  if (!(RESPONSE_KEY in jsonData)) {
    return fileContent;
  }
  const requestSchema = JSON.parse(fileContent);
  delete requestSchema[RESPONSE_KEY];
  return JSON.stringify(requestSchema);
}

const PYTHON_OPTIONS = { "just-types": true, "python-version": "3.7" };
const PYTHON_CLASS_PATTERN = /@dataclass\nclass (\w+)(?:\s*\([^)]*\))?\s*:/g;
const PYTHON_CLASS_REPLACEMENT =
  "@dataclass\nclass $1(DataClassJsonMixin):\n    def __post_init__(self) -> None:\n        print_dataclass(self)\n";

function pythonClassNames(content) {
  return [...content.matchAll(PYTHON_CLASS_PATTERN)].map((match) => match[1]);
}

async function appendPythonResponse(filename, jsonData, requestContent) {
  const paramsClass = quicktypeName(filename);
  // Request classes stay exported as before; nested response classes are reached through their module,
  // e.g. `schemas.allowed_objects.AllowedObject`, since several routes share the same nested names
  const exportedNames = [...pythonClassNames(requestContent)];
  let pythonContent = requestContent;
  let responseClass = "BinaryResponse";
  let schemasImport =
    "from opengeodeweb_microservice.schemas import BinaryResponse, Route, load_schema";
  if (!isBinaryResponse(jsonData)) {
    responseClass = quicktypeName(`${filename}_response`);
    schemasImport = "from opengeodeweb_microservice.schemas import Route, load_schema";
    const { lines: responseTypes } = await quicktypeJSONSchema(
      [{ name: `${filename}_response`, schema: JSON.stringify(jsonData[RESPONSE_KEY]) }],
      "python",
      PYTHON_OPTIONS,
    );
    const responseContent = responseTypes
      .join("\n")
      .replace(PYTHON_CLASS_PATTERN, PYTHON_CLASS_REPLACEMENT);
    // Both quicktype runs name their nested classes independently, they must not shadow each other in the module
    const requestClasses = new Set(exportedNames);
    const duplicates = pythonClassNames(responseContent).filter((name) => requestClasses.has(name));
    if (duplicates.length > 0) {
      throw new Error(
        `${filename}: request and response both define class(es) ${duplicates.join(", ")}, give them distinct "title"s`,
      );
    }
    const isImport = (line) => /^(from|import) /.test(line);
    const responseLines = responseContent.split("\n");
    const newImports = responseLines.filter(
      (line) => isImport(line) && !pythonContent.split("\n").includes(line),
    );
    const responseBody = responseLines
      .filter((line) => !isImport(line))
      .join("\n")
      .trim();
    pythonContent = [...newImports, pythonContent.trimEnd(), "", "", responseBody].join("\n");
    exportedNames.push(responseClass);
  }
  assertGeneratedTypes(
    pythonContent,
    isBinaryResponse(jsonData) ? [paramsClass] : [paramsClass, responseClass],
    (typeName) => new RegExp(`^class ${typeName}\\(`, "m"),
  );
  const routeName = `${filename}_route`;
  exportedNames.push(routeName);
  return (
    schemasImport +
    "\n" +
    pythonContent.trimEnd() +
    `\n\n\n${routeName} = Route(\n` +
    `    schema=load_schema(__file__),\n` +
    `    params=${paramsClass},\n` +
    `    response=${responseClass},\n` +
    `)\n\n` +
    `__all__ = [${exportedNames.map((name) => JSON.stringify(name)).join(", ")}]\n`
  );
}

async function generatePythonFile(folderPath, filename, jsonData, fileContent) {
  const { lines: requestTypes } = await quicktypeJSONSchema(
    [{ name: filename, schema: requestSchemaString(jsonData, fileContent) }],
    "python",
    PYTHON_OPTIONS,
  );
  let pythonContent =
    "from dataclasses_json import DataClassJsonMixin\n" +
    "from opengeodeweb_microservice.schemas import print_dataclass\n" +
    requestTypes.join("\n");
  pythonContent = pythonContent.replace(PYTHON_CLASS_PATTERN, PYTHON_CLASS_REPLACEMENT);
  if (RESPONSE_KEY in jsonData) {
    pythonContent = await appendPythonResponse(filename, jsonData, pythonContent);
  }
  fs.writeFileSync(path.join(folderPath, filename + ".py"), pythonContent);
}

// Every request/response JSON schema, fed to a single quicktype run so TS type names are unique
const typescriptSources = [];
const typescriptTypeNames = new Map();

// Routes with the same file name in different folders (e.g. local/app/kill and local/extensions/kill) must not
// share a type name: quicktype would silently rename one of them (KillParams1) behind the Schemas tree's back
function registerTypescriptSource(sourceName, schema, filePath) {
  const typeName = quicktypeName(sourceName);
  if (typescriptTypeNames.has(typeName)) {
    const error = new Error(
      `${filePath}: TypeScript type ${typeName} already generated for ${typescriptTypeNames.get(typeName)}`,
    );
    error.fatal = true;
    throw error;
  }
  typescriptTypeNames.set(typeName, filePath);
  typescriptSources.push({ name: sourceName, schema });
  return typeName;
}

function registerTypescriptTypes(folder_path, filename, filePath, jsonData, fileContent) {
  // Root routes keep their plain name (AllowedFilesParams), nested ones get their folders (LocalAppKillParams)
  const sourceName = [...folder_path.split("/"), filename].filter((part) => part).join("_");
  const params = registerTypescriptSource(
    `${sourceName}_params`,
    requestSchemaString(jsonData, fileContent),
    filePath,
  );
  let response = "unknown";
  if (isBinaryResponse(jsonData)) {
    response = "Blob";
  } else if (RESPONSE_KEY in jsonData) {
    response = registerTypescriptSource(
      `${sourceName}_response`,
      JSON.stringify(jsonData[RESPONSE_KEY]),
      filePath,
    );
  }
  return { params, response };
}

async function return_json_schema(directoryPath, folder_path, prefix) {
  const folders = fs
    .readdirSync(path.normalize(directoryPath), { withFileTypes: true })
    .filter((folder) => folder.isDirectory() && folder.name != "__pycache__")
    .map((folder) => ({
      name: folder.name,
      path: path.join(directoryPath, folder.name),
    }));
  var folders_schemas = {};
  var folders_types = {};
  for (const folder of folders) {
    if (folder.name == "schemas") {
      const jsonFiles = glob.sync(path.join(folder.path, "**/*.json"));
      // Checked before touching any generated file, so a failure leaves the folder as it was
      if (requireResponse) {
        for (const filePath of jsonFiles) {
          if (!(RESPONSE_KEY in JSON.parse(fs.readFileSync(filePath, "utf8")))) {
            throw new Error(
              `${filePath}: missing "${RESPONSE_KEY}" schema (required by --requireResponse)`,
            );
          }
        }
      }
      if (generatePython) {
        fs.readdirSync(folder.path)
          .filter((file) => path.extname(file).toLowerCase() === ".py")
          .forEach((file) => fs.unlinkSync(path.join(folder.path, file)));
      }

      var schemas = {};
      let initContent = "";
      for (const filePath of jsonFiles) {
        const fileContent = fs.readFileSync(filePath, "utf8");
        var jsonData = JSON.parse(fileContent);
        var filename = filePath.replace(/^.*[\\/]/, "").replace(/\.[^/.]+$/, "");
        try {
          var route = jsonData[key];
          var values = [prefix, folder_path, route];
          values = values.map(function (value) {
            return value.replace("/", "").replace(".", "");
          });
          values = values.map(function (value) {
            return value.replaceAll("/", separator).replaceAll(".", separator);
          });
          jsonData["$id"] = values
            .filter(function (val) {
              return val;
            })
            .join(separator);
          schemas[filename] = jsonData;
          folders_types[filename] = registerTypescriptTypes(
            folder_path,
            filename,
            filePath,
            jsonData,
            fileContent,
          );

          if (generatePython) {
            initContent += "from ." + filename + " import *\n";
            await generatePythonFile(folder.path, filename, jsonData, fileContent);
          }
        } catch (error) {
          if (error.fatal) {
            throw error;
          }
          console.error(`Erreur lors de la lecture du fichier ${filePath}:`, error);
        }
      }

      if (generatePython) {
        const initFile = path.join(folder.path, "__init__.py");
        fs.writeFileSync(initFile, initContent);
      }

      folders_schemas = Object.keys(schemas).reduce((acc, key) => {
        const currentSchema = schemas[key];
        const modifiedSchema = {
          $id: path.join(folder_path, currentSchema["$id"]),
          ...currentSchema,
        };
        acc[key] = modifiedSchema;
        return acc;
      }, folders_schemas);
    } else {
      var new_folder_path = folder_path + "/" + folder.name;
      var test = await return_json_schema(folder.path, new_folder_path, prefix);
      folders_schemas[folder.name] = test.schemas;
      folders_types[folder.name] = test.types;
    }
  }
  return { schemas: folders_schemas, types: folders_types };
}

function collectTypeNames(tree) {
  return Object.values(tree).flatMap((value) =>
    isTypesLeaf(value)
      ? [value.params, value.response].filter(
          (typeName) => typeName !== "unknown" && typeName !== "Blob",
        )
      : collectTypeNames(value),
  );
}

function isTypesLeaf(value) {
  return typeof value.params === "string" && typeof value.response === "string";
}

// Mirror the JSON tree: each schema keeps its exact JSON type, intersected with its phantom request/response types
function typesTreeToTypescript(tree, jsonPath, indent) {
  const pad = "  ".repeat(indent);
  const lines = Object.entries(tree).map(([name, value]) => {
    const valuePath = `${jsonPath}[${JSON.stringify(name)}]`;
    const type = isTypesLeaf(value)
      ? `${valuePath} & TypedSchema<${value.params}, ${value.response}>`
      : typesTreeToTypescript(value, valuePath, indent + 1);
    return `${pad}  readonly ${name}: ${type};`;
  });
  return `{\n${lines.join("\n")}\n${pad}}`;
}

async function generateTypescript(typesTree) {
  const sources = [
    ...typescriptSources,
    { name: "error_response", schema: fs.readFileSync(errorSchemaFile, "utf8") },
  ];
  const { lines: tsTypes } = await quicktypeJSONSchema(sources, "typescript", {
    "just-types": true,
    "prefer-unions": true,
  });
  assertGeneratedTypes(
    tsTypes.join("\n"),
    collectTypeNames(typesTree),
    (typeName) => new RegExp(`^export (interface|type) ${typeName}\\b`, "m"),
  );
  const content = [
    "// Generated by opengeodeweb-microservice-generate, do not edit.",
    `import type json from "./${path.basename(outputFile)}";`,
    "",
    tsTypes.join("\n"),
    "// `__params` and `__response` only exist at type level, to infer request/response types from a schema.",
    "// A type alias (not an interface) keeps the implicit index signature of the JSON type it is intersected with.",
    "export type TypedSchema<Params, Response> = {",
    "  readonly __params?: Params;",
    "  readonly __response?: Response;",
    "};",
    "",
    `export interface Schemas ${typesTreeToTypescript(typesTree, "(typeof json)", 0)}`,
    "",
    "declare const schemas: Schemas;",
    "export default schemas;",
    "",
  ].join("\n");
  fs.writeFileSync(outputTypesFile, content);
  fs.writeFileSync(
    outputJsFile,
    [
      "// Generated by opengeodeweb-microservice-generate, do not edit.",
      `import schemas from "./${path.basename(outputFile)}" with { type: "json" };`,
      "",
      "export default schemas;",
      "",
    ].join("\n"),
  );
}

async function main() {
  const finalJson = {};
  const finalTypes = {};
  const { schemas, types } = await return_json_schema(directoryPath, "", prefix);
  finalJson[prefix] = schemas;
  finalTypes[prefix] = types;
  console.log("FINAL", outputFile, finalJson);
  fs.writeFileSync(outputFile, JSON.stringify(finalJson, null, 2));
  await generateTypescript(finalTypes);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
