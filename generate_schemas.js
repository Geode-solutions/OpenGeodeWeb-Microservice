#!/usr/bin/env node

// Node imports
import fs from "node:fs";
import path from "node:path";
import { parseArgs } from "node:util"
import process from "node:process";

// Third party imports
import { quicktype, InputData, JSONSchemaInput, FetchingJSONSchemaStore } from "quicktype-core";
import { glob } from "glob";

const projectName = path.basename(process.cwd()).toLowerCase().replaceAll("-", "_");

const args = parseArgs({
  options: {
    startDir: { type: "string" },
    key: { type: "string" },
    separator: { type: "string" },
    prefix: { type: "string", default: projectName },
  },
});

console.log({ args });
const startDir = args.values.startDir;
const key = args.values.key;
const separator = args.values.separator;
const prefix = args.values.prefix;

const generatePython = startDir.split(path.sep).includes("src");
console.log("generatePython", generatePython);

const directoryPath = path.resolve(process.cwd(), startDir);
console.log("directoryPath", directoryPath);

const outputFile = path.join(process.cwd(), `${projectName}_schemas.json`);

async function quicktypeJSONSchema(filename, jsonSchemaString) {
  const schemaInput = new JSONSchemaInput(new FetchingJSONSchemaStore());
  await schemaInput.addSource({ name: filename, schema: jsonSchemaString });
  const inputData = new InputData();
  inputData.addInput(schemaInput);
  return await quicktype({
    inputData,
    lang: "python",
    rendererOptions: { "just-types": true, "python-version": "3.7" },
  });
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
  for (const folder of folders) {
    if (folder.name == "schemas") {
      if (generatePython) {
        fs.readdirSync(folder.path)
          .filter((file) => path.extname(file).toLowerCase() === ".py")
          .forEach((file) => fs.unlinkSync(path.join(folder.path, file)));
      }

      const jsonFiles = glob.sync(path.join(folder.path, "**/*.json"));
      var schemas = {};
      let initContent = "";
      for (const filePath of jsonFiles) {
        try {
          const fileContent = fs.readFileSync(filePath, "utf8");
          var jsonData = JSON.parse(fileContent);
          var filename = filePath.replace(/^.*[\\/]/, "").replace(/\.[^/.]+$/, "");
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

          if (generatePython) {
            initContent += "from ." + filename + " import *\n";
            const { lines: jsonTypes } = await quicktypeJSONSchema(filename, fileContent);
            let pythonContent =
              "from dataclasses_json import DataClassJsonMixin\n" + jsonTypes.join("\n");
            pythonContent = pythonContent.replace(
              /@dataclass\nclass (\w+)(?:\s*\([^)]*\))?\s*:/g,
              "@dataclass\nclass $1(DataClassJsonMixin):\n    def __post_init__(self) -> None:\n        print(self, flush=True)\n",
            );
            const pythonFile = path.join(folder.path, filename + ".py");
            fs.writeFileSync(pythonFile, pythonContent);
          }
        } catch (error) {
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
      folders_schemas[folder.name] = test;
    }
  }
  return folders_schemas;
}

if (fs.existsSync(outputFile)) {
  fs.unlinkSync(outputFile);
}

async function main() {
  const finalJson = {};
  finalJson[prefix] = await return_json_schema(directoryPath, "", prefix);
  console.log("FINAL", outputFile, finalJson);
  fs.writeFileSync(outputFile, JSON.stringify(finalJson, null, 2));
}

main();
