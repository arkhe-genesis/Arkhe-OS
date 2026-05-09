/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {spawn} from 'node:child_process';
import path from 'node:path';

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {defineTool} from './ToolDefinition.js';

async function runTribev2Query(args: string[]): Promise<{stdout: string; stderr: string; code: number | null}> {
  const skillDir = path.resolve(process.cwd(), 'skills/tribev2');

  // Create a temporary script to run the python code
  const fs = await import('fs');
  const tmpScript = path.join(skillDir, 'run_tribev2_mcp.py');
  fs.writeFileSync(tmpScript, `
import sys
import json
import warnings
warnings.filterwarnings("ignore")

try:
    from tribev2 import TribeModel
except ImportError:
    print("ERROR: missing dependencies. Run: pip install -e skills/tribev2", file=sys.stderr)
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_tribev2_mcp.py <type> <path>", file=sys.stderr)
        sys.exit(1)

    media_type = sys.argv[1]
    media_path = sys.argv[2]

    print(f"Loading TribeModel from huggingface...", file=sys.stderr)
    model = TribeModel.from_pretrained("facebook/tribev2", cache_folder="./cache")

    print(f"Processing {media_type} file: {media_path}", file=sys.stderr)
    if media_type == 'video':
        df = model.get_events_dataframe(video_path=media_path)
    elif media_type == 'audio':
        df = model.get_events_dataframe(audio_path=media_path)
    elif media_type == 'text':
        df = model.get_events_dataframe(text_path=media_path)
    else:
        print(f"Unknown media type: {media_type}", file=sys.stderr)
        sys.exit(1)

    print("Predicting brain responses...", file=sys.stderr)
    preds, segments = model.predict(events=df)

    result = {
        "shape": list(preds.shape),
        "segments": segments,
        "n_timesteps": preds.shape[0],
        "n_vertices": preds.shape[1] if len(preds.shape) > 1 else 0
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
`);

  return new Promise((resolve) => {
    const childProcess = spawn('python3', [tmpScript, ...args], {
      cwd: skillDir,
      env: {...process.env, PYTHONPATH: skillDir}
    });
    let stdout = '';
    let stderr = '';

    childProcess.stdout.on('data', (data: Buffer) => {
      stdout += data.toString();
    });

    childProcess.stderr.on('data', (data: Buffer) => {
      stderr += data.toString();
    });

    childProcess.on('close', (code: number | null) => {
      resolve({stdout, stderr, code});
    });
  });
}

export const tribev2_predict = defineTool({
  name: 'tribev2_predict',
  description: 'Predict fMRI brain responses to naturalistic stimuli (video, audio, text) using TRIBE v2.',
  annotations: {
    category: ToolCategory.AGENT, // or create a new category
    readOnlyHint: true,
  },
  schema: {
    mediaType: zod.enum(['video', 'audio', 'text']).describe('The type of media file.'),
    mediaPath: zod.string().describe('The path to the media file.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine('### TRIBE v2 Brain Response Prediction');
    response.appendResponseLine(`> *File: "${request.params.mediaPath}" (${request.params.mediaType})*`);

    const args = [request.params.mediaType, request.params.mediaPath];

    const {stdout, stderr, code} = await runTribev2Query(args);

    if (stdout) {
      try {
        const result = JSON.parse(stdout);
        response.appendResponseLine(`\n**Prediction successful!**`);
        response.appendResponseLine(`- Shape: \`(${result.shape.join(', ')})\``);
        response.appendResponseLine(`- Timesteps: ${result.n_timesteps}`);
        response.appendResponseLine(`- Vertices: ${result.n_vertices}`);
      } catch (_e) {
         response.appendResponseLine('\n' + stdout);
      }
    }

    if (code !== 0) {
      response.appendResponseLine(`\n**Error**: Prediction failed (Code ${code}).`);
      if (stderr) {
        response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
      }
    } else if (stderr) {
      response.appendResponseLine('\n<details><summary>Diagnostics</summary>\n\n```\n' + stderr + '\n```\n</details>');
    }
  },
});
