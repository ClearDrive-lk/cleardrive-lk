#!/usr/bin/env node
"use strict";

const { chromium } = require("playwright");

async function testSRI() {
  console.log("Testing SRI implementation...\n");

  const browser = await chromium.launch();
  const page = await browser.newPage();

  const consoleMessages = [];
  page.on("console", (msg) => consoleMessages.push(msg.text()));

  const failedRequests = [];
  page.on("requestfailed", (request) => {
    failedRequests.push({
      url: request.url(),
      failure: request.failure() ? request.failure().errorText : "unknown",
    });
  });

  await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const sriErrors = consoleMessages.filter(
    (msg) =>
      msg.toLowerCase().includes("integrity") ||
      msg.toLowerCase().includes("blocked"),
  );

  console.log("=".repeat(70));
  console.log("SRI TEST RESULTS");
  console.log("=".repeat(70));

  if (sriErrors.length > 0) {
    console.log("\nSRI ERRORS FOUND:");
    sriErrors.forEach((error) => console.log(`   ${error}`));
  } else {
    console.log("\nNo SRI errors detected");
  }

  if (failedRequests.length > 0) {
    console.log("\nFAILED REQUESTS:");
    failedRequests.forEach((req) => {
      console.log(`   ${req.url}`);
      console.log(`   Error: ${req.failure}`);
    });
  } else {
    console.log("All external resources loaded successfully");
  }

  console.log("\n" + "=".repeat(70));
  await browser.close();
}

testSRI().catch((err) => {
  console.error("SRI test failed:", err);
  process.exit(1);
});
