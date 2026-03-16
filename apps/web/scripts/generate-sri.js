#!/usr/bin/env node
"use strict";
/* eslint-disable @typescript-eslint/no-require-imports */

const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const https = require("https");
const path = require("path");

const SRI_RESOURCE_PATH = path.resolve(__dirname, "..", "sri-resources.json");

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    const request = client.get(
      url,
      {
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
          Accept: "*/*",
        },
      },
      (res) => {
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode}: ${url}`));
          return;
        }
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => resolve(Buffer.concat(chunks)));
      },
    );
    request.on("error", (err) => reject(err));
  });
}

function parseSriResourceFile() {
  return JSON.parse(fs.readFileSync(SRI_RESOURCE_PATH, "utf8"));
}

function writeSriResourceFile(contents) {
  fs.writeFileSync(SRI_RESOURCE_PATH, `${JSON.stringify(contents, null, 2)}\n`);
}

function resolveFetchUrl(resource) {
  if (
    resource.url === "https://www.googletagmanager.com/gtag/js" &&
    !resource.url.includes("?id=")
  ) {
    const gaId = process.env.NEXT_PUBLIC_GA_ID;
    if (!gaId) {
      return null;
    }
    return `${resource.url}?id=${encodeURIComponent(gaId)}`;
  }
  return resource.url;
}

async function generateSRIHash(url) {
  const content = await fetchUrl(url);
  const sha256 = crypto.createHash("sha256").update(content).digest("base64");
  const sha384 = crypto.createHash("sha384").update(content).digest("base64");
  const sha512 = crypto.createHash("sha512").update(content).digest("base64");

  return {
    url,
    sha256: `sha256-${sha256}`,
    sha384: `sha384-${sha384}`,
    sha512: `sha512-${sha512}`,
    size: content.length,
  };
}

async function generateMultipleSRI(urls) {
  console.log("=".repeat(70));
  console.log("SRI HASH GENERATOR");
  console.log("=".repeat(70));

  const results = [];
  for (const url of urls) {
    try {
      console.log(`\nFetching: ${url}`);
      const result = await generateSRIHash(url);
      console.log("OK: generated hashes");
      results.push(result);
    } catch (err) {
      console.error(`Error processing ${url}: ${err.message}`);
    }
  }

  console.log("\n" + "=".repeat(70));
  console.log("RESULTS");
  console.log("=".repeat(70));

  results.forEach((result, index) => {
    console.log(`\n${index + 1}. ${result.url}`);
    console.log(`   Size: ${(result.size / 1024).toFixed(2)} KB`);
    console.log(`   SHA-384 (Recommended): ${result.sha384}`);
    console.log(`   SHA-256: ${result.sha256}`);
    console.log(`   SHA-512: ${result.sha512}`);
    console.log("\n   HTML:");
    console.log(`   <script src="${result.url}"`);
    console.log(`           integrity="${result.sha384}"`);
    console.log('           crossorigin="anonymous"></script>');
  });

  console.log("\n" + "=".repeat(70));
  console.log(`Generated SRI hashes for ${results.length} resource(s).`);
  console.log("=".repeat(70));

  return results;
}

async function refreshSriResourceFile() {
  const sriConfig = parseSriResourceFile();
  const updatedResources = [];

  console.log("Refreshing apps/web/sri-resources.json");

  for (const resource of sriConfig.resources ?? []) {
    const fetchUrl = resolveFetchUrl(resource);

    if (!fetchUrl) {
      console.warn(
        `Skipping ${resource.name}: NEXT_PUBLIC_GA_ID is not set, keeping existing hash.`,
      );
      updatedResources.push(resource);
      continue;
    }

    try {
      console.log(`Fetching hash source for ${resource.name}: ${fetchUrl}`);
      const result = await generateSRIHash(fetchUrl);
      updatedResources.push({
        ...resource,
        integrity: result.sha384,
      });
      console.log(`Updated ${resource.name}`);
    } catch (err) {
      console.warn(
        `Failed to refresh ${resource.name}, keeping existing hash: ${err.message}`,
      );
      updatedResources.push(resource);
    }
  }

  writeSriResourceFile({
    ...sriConfig,
    resources: updatedResources,
  });

  console.log(`Wrote ${SRI_RESOURCE_PATH}`);
  return updatedResources;
}

const defaultResources = [
  "https://accounts.google.com/gsi/client",
  "https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID",
];

if (require.main === module) {
  const urls = process.argv.slice(2);
  if (urls.length === 0) {
    refreshSriResourceFile().catch((err) => {
      console.error(`SRI refresh failed: ${err.message}`);
      process.exit(1);
    });
  } else {
    generateMultipleSRI(urls).catch((err) => {
      console.error(`SRI generation failed: ${err.message}`);
      process.exit(1);
    });
  }
}

module.exports = {
  defaultResources,
  generateSRIHash,
  generateMultipleSRI,
  refreshSriResourceFile,
  resolveFetchUrl,
};
