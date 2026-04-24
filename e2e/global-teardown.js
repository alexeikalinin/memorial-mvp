import { execSync } from "child_process";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const backendDir = resolve(__dirname, "../backend");

export default async function globalTeardown() {
  console.log("\n[teardown] Cleaning up test data from DB…");
  try {
    const out = execSync(
      "source .venv/bin/activate && python cleanup_test_data.py",
      { cwd: backendDir, shell: "/bin/zsh", encoding: "utf8", timeout: 60000 }
    );
    console.log("[teardown]", out.trim());
  } catch (err) {
    console.warn("[teardown] Cleanup failed (non-fatal):", err.message);
  }
}
