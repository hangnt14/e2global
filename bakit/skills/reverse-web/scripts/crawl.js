#!/usr/bin/env node
/**
 * crawl.js
 * CLI entry point for the reverse-web crawl script.
 * Parses arguments, calls crawl-engine, catches GuardrailViolation.
 * Invoked via Bash tool from within a Claude Code session:
 *   node skills/reverse-web/scripts/crawl.js <url> --consent [options]
 */

import { program } from 'commander';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { crawl } from '../lib/crawl-engine.js';
import { GuardrailViolation } from '../lib/guardrails.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const defaults = JSON.parse(
  readFileSync(join(__dirname, '../config/defaults.json'), 'utf8')
);

program
  .name('reverse-web crawl')
  .description('Crawl a website and capture evidence for BA documentation')
  .argument('<url>', 'Entry URL to crawl (e.g. https://example.com)')
  .option('--consent', 'Confirm you have permission to crawl this site (required)', false)
  .option('--max-pages <n>', 'Max pages to crawl per run', String(defaults.maxPages))
  .option('--depth <n>', 'Max crawl depth from entry URL', String(defaults.maxDepth))
  .option('--delay <ms>', 'Delay between requests in ms', String(defaults.delay))
  .option('--output <dir>', 'Output directory for evidence', './evidence')
  .option('--ignore-robots', 'Skip robots.txt rules', false)
  .option('--clean', 'Remove existing evidence folder before crawling', false)
  .option('--continue', 'Continue from previous crawl (skip already-visited URLs)', false)
  .action(async (url, opts) => {
    // Validate conflicting flags
    if (opts.clean && opts.continue) {
      console.error('Error: Cannot use --clean with --continue. Choose one.');
      process.exit(1);
    }

    // M4: validate numeric options early
    const maxPages = parseInt(opts.maxPages, 10);
    const maxDepth = parseInt(opts.depth, 10);
    const delay = parseInt(opts.delay, 10);
    if (isNaN(maxPages) || maxPages < 1) { console.error('Error: --max-pages must be a positive integer'); process.exit(1); }
    if (isNaN(maxDepth) || maxDepth < 0) { console.error('Error: --depth must be a non-negative integer'); process.exit(1); }
    if (isNaN(delay) || delay < 0) { console.error('Error: --delay must be a non-negative integer'); process.exit(1); }

    // H3: validate output path BEFORE --clean rmSync
    const { validateOutputPath } = await import('../lib/guardrails.js');
    try {
      validateOutputPath(opts.output, process.cwd());
    } catch (err) {
      console.error(`[GUARDRAIL G6] ${err.message}`);
      process.exit(1);
    }

    // Clean evidence dir if requested
    if (opts.clean) {
      const { rmSync, existsSync } = await import('fs');
      const { resolve } = await import('path');
      const outputDir = resolve(opts.output);
      if (existsSync(outputDir)) {
        rmSync(outputDir, { recursive: true, force: true });
        console.log(`✓ Cleaned: ${opts.output}`);
      }
    }

    try {
      await crawl(url, {
        consent: opts.consent,
        maxPages,
        maxDepth,
        delay,
        timeout: defaults.timeout,
        stabilityTimeout: defaults.stabilityTimeout,
        output: opts.output,
        ignoreRobots: opts.ignoreRobots,
        continueMode: opts.continue,
      });
    } catch (err) {
      if (err instanceof GuardrailViolation) {
        console.error(`\n[GUARDRAIL ${err.code}] ${err.message}`);
        process.exit(1);
      }
      console.error(`\n[ERROR] ${err.message}`);
      if (process.env.DEBUG) console.error(err.stack);
      process.exit(2);
    }
  });

program.parse();
