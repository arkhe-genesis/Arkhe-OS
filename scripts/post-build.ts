
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as fs from 'node:fs';
import * as path from 'node:path';

const BUILD_DIR = path.join(process.cwd(), 'build');

function writeFile(filePath: string, content: string): void {
  fs.writeFileSync(filePath, content, 'utf-8');
}

function main(): void {
  const devtoolsThirdPartyPath =
    'node_modules/chrome-devtools-frontend/front_end/third_party';
  const devtoolsFrontEndCorePath =
    'node_modules/chrome-devtools-frontend/front_end/core';

  // Create i18n mock
  const i18nDir = path.join(BUILD_DIR, devtoolsFrontEndCorePath, 'i18n');
  fs.mkdirSync(i18nDir, {recursive: true});
  const localesFile = path.join(i18nDir, 'locales.js');
  const localesContent = `
export const LOCALES = [
  'en-US',
];

export const BUNDLED_LOCALES = [
  'en-US',
];

export const DEFAULT_LOCALE = 'en-US';

export const REMOTE_FETCH_PATTERN = '@HOST@/remote/serve_file/@VERSION@/core/i18n/locales/@LOCALE@.json';

export const LOCAL_FETCH_PATTERN = './locales/@LOCALE@.json';`;
  writeFile(localesFile, localesContent);

  // Create codemirror.next mock.
  const codeMirrorDir = path.join(
    BUILD_DIR,
    devtoolsThirdPartyPath,
    'codemirror.next',
  );
  fs.mkdirSync(codeMirrorDir, {recursive: true});
  const codeMirrorFile = path.join(codeMirrorDir, 'codemirror.next.js');
  const codeMirrorContent = `export default {
    cssStreamParser: async () => ({
        startState: () => ({})
    }),
    StringStream: class {
        constructor() { this.pos = 0; }
    },
    css: {
        cssLanguage: {
            parser: {
                parse: () => ({ topNode: { getChild: () => null } })
            }
        }
    }
}`;
  writeFile(codeMirrorFile, codeMirrorContent);

  // Create codemirror mode mocks
  const codeMirrorModesDir = path.join(
    BUILD_DIR,
    devtoolsThirdPartyPath,
    'codemirror',
    'package',
    'mode'
  );
  fs.mkdirSync(path.join(codeMirrorModesDir, 'xml'), {recursive: true});
  writeFile(path.join(codeMirrorModesDir, 'xml', 'xml.mjs'), 'export default {}');

  fs.mkdirSync(path.join(codeMirrorModesDir, 'css'), {recursive: true});
  writeFile(path.join(codeMirrorModesDir, 'css', 'css.mjs'), 'export default {}');

  fs.mkdirSync(path.join(codeMirrorModesDir, 'javascript'), {recursive: true});
  writeFile(path.join(codeMirrorModesDir, 'javascript', 'javascript.mjs'), 'export default {}');

  const codeMirrorAddonDir = path.join(
    BUILD_DIR,
    devtoolsThirdPartyPath,
    'codemirror',
    'package',
    'addon',
    'runmode'
  );
  fs.mkdirSync(codeMirrorAddonDir, {recursive: true});
  writeFile(path.join(codeMirrorAddonDir, 'runmode-standalone.mjs'), 'export default {}');

  // Create root mock
  const rootDir = path.join(BUILD_DIR, devtoolsFrontEndCorePath, 'root');
  fs.mkdirSync(rootDir, {recursive: true});
  const runtimeFile = path.join(rootDir, 'Runtime.js');
  const runtimeContent = `
export function getChromeVersion() { return ''; };
export const hostConfig = {};
export const Runtime = {
  experiments: { isEnabled: () => false },
  isDescriptorEnabled: () => true,
  queryParam: () => null,
  getRemoteBase: () => null,
  GdpProfilesEnterprisePolicyValue: {
      DISABLED: 0,
      ENABLED: 1
  }
}
export const experiments = {
  isEnabled: () => false,
}
export const ExperimentName = {
  ALL: '*',
  CAPTURE_NODE_CREATION_STACKS: 'capture-node-creation-stacks',
  LIVE_HEAP_PROFILE: 'live-heap-profile',
  PROTOCOL_MONITOR: 'protocol-monitor',
  SAMPLING_HEAP_PROFILER_TIMELINE: 'sampling-heap-profiler-timeline',
  SHOW_OPTION_TO_EXPOSE_INTERNALS_IN_HEAP_SNAPSHOT: 'show-option-to-expose-internals-in-heap-snapshot',
  TIMELINE_INVALIDATION_TRACKING: 'timeline-invalidation-tracking',
  TIMELINE_SHOW_ALL_EVENTS: 'timeline-show-all-events',
  TIMELINE_V8_RUNTIME_CALL_STATS: 'timeline-v8-runtime-call-stats',
  APCA: 'apca',
  FONT_EDITOR: 'font-editor',
  FULL_ACCESSIBILITY_TREE: 'full-accessibility-tree',
  CONTRAST_ISSUES: 'contrast-issues',
  EXPERIMENTAL_COOKIE_FEATURES: 'experimental-cookie-features',
  INSTRUMENTATION_BREAKPOINTS: 'instrumentation-breakpoints',
  AUTHORED_DEPLOYED_GROUPING: 'authored-deployed-grouping',
  JUST_MY_CODE: 'just-my-code',
  USE_SOURCE_MAP_SCOPES: 'use-source-map-scopes',
  TIMELINE_SHOW_POST_MESSAGE_EVENTS: 'timeline-show-postmessage-events',
  TIMELINE_DEBUG_MODE: 'timeline-debug-mode',
}
  `;
  writeFile(runtimeFile, runtimeContent);

  copyDevToolsDescriptionFiles();

  fs.mkdirSync(path.join(BUILD_DIR, 'src', 'bin'), {recursive: true});
}

function copyDevToolsDescriptionFiles() {
  const devtoolsIssuesDescriptionPath =
    'node_modules/chrome-devtools-frontend/front_end/models/issues_manager/descriptions';
  const sourceDir = path.join(process.cwd(), devtoolsIssuesDescriptionPath);
  const destDir = path.join(
    BUILD_DIR,
    'src',
    'third_party',
    'issue-descriptions',
  );
  if (fs.existsSync(sourceDir)) { fs.cpSync(sourceDir, destDir, {recursive: true}); }
}

main();
