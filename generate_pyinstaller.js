#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";

const projectPath = process.argv[2];
console.log("projectPath", projectPath);

function pythonCommand() {
  const candidates = ["python3", "python"];
  for (const cmd of candidates) {
    try {
      execSync(`${cmd} --version`, { stdio: "ignore" });
      return cmd;
    } catch {
      // silent fail
    }
  }
  throw new Error("Python not found");
}

function createVenv() {
  console.log("🔧 Setting up Python virtual environment...");
  const python = pythonCommand();
  console.log(`→ Using Python: ${python}`);
  const venvPath = path.join(projectPath, "venv");
  if (fs.existsSync(venvPath)) {
    console.log(`→ Found existing venv → ${venvPath}`);
  } else {
    console.log(`→ Creating virtual environment → ${venvPath}`);
    try {
      execSync(`${python} -m venv ${venvPath}`, { stdio: "inherit" });
    } catch (err) {
      console.error("Failed to create virtual environment");
      console.error(err.message);
      process.exit(1);
    }
  }
  if (process.platform === "win32") {
    return path.join(venvPath, "Scripts", "python.exe");
  } else {
    return path.join(venvPath, "bin", "python");
  }
}

function installDependecies(pythonExe) {
  console.log(`→ Installing dependencies ...`);
  const pipCommand = `pip install ${projectPath} pyinstaller`;
  try {
    console.log(`→ Running: ${pythonExe} -m ${pipCommand}`);
    execSync(`${pythonExe} -m ${pipCommand}`, { stdio: "inherit" });
  } catch (err) {
    console.error("Failed to install requirements");
    console.error(err.message);
    process.exit(1);
  }
  console.log("✅ Python virtual environment setup complete");
}

function runPyInstaller(pythonExe) {
  console.log(`→ Running PyInstaller ...`);
  const specFiles = fs.readdirSync(projectPath, { withFileTypes: true })
    .filter(file => file.isFile() && file.name.endsWith(".spec"))
    .map(file => path.join(projectPath, file.name));
  if (specFiles.length !== 1) {
    console.error("Expected 1 spec file, found " + specFiles.length);
    process.exit(1);
  }
  const pyinstallerCommand = `PyInstaller ${specFiles[0]} --distpath ${process.cwd()} --clean`;
  try {
    console.log(`→ Running: ${pythonExe} -m ${pyinstallerCommand}`);
    execSync(`${pythonExe} -m ${pyinstallerCommand}`, { stdio: "inherit" });
  } catch (err) {
    console.error("Failed to run pyinstaller");
    console.error(err.message);
    process.exit(1);
  }
  console.log("✅ PyInstaller complete");
}

function main() {
  const pythonExe = createVenv();
  installDependecies(pythonExe);
  runPyInstaller(pythonExe);
}

main();
