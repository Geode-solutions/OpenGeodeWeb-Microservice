import fs from "fs";
import path from "path";
import { glob } from "glob";
import process from "process";
import {
  quicktype,
  InputData,
  JSONSchemaInput,
  FetchingJSONSchemaStore,
} from "quicktype-core";

console.log("process.argv", process.argv);

var projectName = process.argv[2];
console.log("projectName", projectName);
var folderName = process.argv[3];
console.log("folderName", folderName);
var key = process.argv[4];
console.log("key", key);
var separator = process.argv[5];
console.log("separator", separator);

const findDirectoryPath = (targetDirectoryName, folderName) => {
  const pathToCheck = path.join(
    process.cwd(),
    "/src",
    "/",
    targetDirectoryName
  );
  console.log("pathToCheck", pathToCheck);

  const folders = fs
    .readdirSync(pathToCheck, { withFileTypes: true })
    .filter(
      (folder) =>
        folder.isDirectory() &&
        !folder.name.endsWith(".egg-info") &&
        folder.name != "tests" &&
        folder.name != "__pycache__" &&
        folder.name.includes(folderName)
    )
    .map((folder) => ({
      name: folder.name,
      path: path.join(pathToCheck, folder.name),
    }));
  console.log("folders", folders);
  const routesDirectory = path.join(folders[0].path);
  return routesDirectory;
};

const directoryPath = findDirectoryPath(projectName, folderName);

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

async function return_json_schema(directoryPath, folder_path, projectName) {
  console.log("return_json_schema", directoryPath, folder_path, projectName);

  const folders = fs
    .readdirSync(path.normalize(directoryPath), { withFileTypes: true })
    .filter((folder) => folder.isDirectory() && folder.name != "__pycache__")
    .map((folder) => ({
      name: folder.name,
      path: path.join(directoryPath, folder.name),
    }));
  var folders_schemas = {};
  folders.forEach((folder) => {
    if (folder.name == "schemas") {
      const jsonFiles = glob.sync(path.join(folder.path, "**/*.json"));
      var schemas = {};
      jsonFiles.forEach(async (filePath) => {
        try {
          const fileContent = fs.readFileSync(filePath, "utf8");
          var jsonData = JSON.parse(fileContent);
          var filename = filePath
            .replace(/^.*[\\/]/, "")
            .replace(/\.[^/.]+$/, "");
          var route = jsonData[key];
          var values = [projectName, folder_path, route];
          values = values.map(function (x) {
            return x.replace("/", "").replace(".", "");
          }); // first replace first . / by empty string
          values = values.map(function (x) {
            return x.replaceAll("/", separator).replaceAll(".", separator);
          }); // then replace all . / by separator
          console.log("values", values);
          jsonData["$id"] = values
            .filter(function (val) {
              return val;
            })
            .join(separator);
          schemas[filename] = jsonData;
          const { lines: jsonTypes } = await quicktypeJSONSchema(
            filename,
            fileContent
          );
          let pythonContent =
            "from dataclasses_json import DataClassJsonMixin\n" +
            jsonTypes.join("\n");
          pythonContent = pythonContent.replace(
            /@dataclass\nclass (\w+)(?:\s*\([^)]*\))?\s*:/g,
            "@dataclass\nclass $1(DataClassJsonMixin):"
          );
          const pythonFile = path.join(folder.path, filename + ".py");
          fs.writeFileSync(pythonFile, pythonContent);
        } catch (error) {
          console.error(
            `Erreur lors de la lecture du fichier ${filePath}:`,
            error
          );
        }
      });
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
      var test = return_json_schema(folder.path, new_folder_path, projectName);
      folders_schemas[folder.name] = test;
    }
  });
  return folders_schemas;
}

if (fs.existsSync(outputFile)) {
  fs.unlinkSync(outputFile);
}

async function main() {
  const finalJson = {};
  finalJson[projectName] = return_json_schema(directoryPath, "", projectName);

  fs.writeFileSync(outputFile, JSON.stringify(finalJson, null, 2));
}

main();
