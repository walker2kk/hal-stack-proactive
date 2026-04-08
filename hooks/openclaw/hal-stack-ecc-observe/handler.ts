/**
 * Hal Stack ECC Observer Hook
 * Runs after message:received event, extracts user message content
 * and calls the ECC observer to learn patterns.
 */
import type { HookHandler, HookEvent } from "openclaw";

const handler: HookHandler = async (event: HookEvent) => {
  // Only run on message:received events
  if (event.type !== "message:received") {
    return;
  }

  // Get message content from context
  const content = event.context?.content;
  if (!content || typeof content !== "string" || content.trim().length === 0) {
    return;
  }

  // Find the scripts directory
  // Installed location:
  //   handler.ts: <workspace>/hooks/hal-stack-ecc-observe/handler.ts
  //   ecc-observe.py: <workspace>/skills/hal-stack-proactive/scripts/ecc-observe.py
  const scriptPath = require("path").join(
    __dirname,
    "..",
    "..",
    "skills",
    "hal-stack-proactive",
    "scripts",
    "ecc-observe.py"
  );

  // Run the python observer
  const { exec } = require("child_process");
  exec(`python3 "${scriptPath}" observe "${content.replace(/"/g, '\\"')}"`, (error, stdout, stderr) => {
    if (error) {
      console.error(`[hal-stack-ecc-observe] Error: ${error.message}`);
      return;
    }
    if (stderr) {
      console.error(`[hal-stack-ecc-observe] stderr: ${stderr}`);
    }
    if (stdout) {
      console.log(`[hal-stack-ecc-observe] ${stdout}`);
    }
  });

  // No need to send messages to user - this is background observation
  return;
};

export default handler;
