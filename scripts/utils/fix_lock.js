import fs from 'fs';
import crypto from 'crypto';

const lockFile = 'skills-lock.json';
const lockContent = fs.readFileSync(lockFile, 'utf8');
// Fix the invalid JSON first
const fixedContent = lockContent.replace(
  /"63dd2da3470700a1fa7a57c79e085830c95e504228dbcaa650f8bf9dbfb90bff"\n    "urbit"/,
  '"63dd2da3470700a1fa7a57c79e085830c95e504228dbcaa650f8bf9dbfb90bff"\n    },\n    "urbit"'
);

let lockData;
try {
  lockData = JSON.parse(fixedContent);
} catch (e) {
  console.log("Still invalid JSON");
  // Just use a basic one if parsing fails
  lockData = {
    "version": 1,
    "skills": {
      "fortytwo-mcp": {
        "source": "Fortytwo-Network/fortytwo-mcp-skills",
        "sourceType": "github",
        "skillPath": "skills/fortytwo-mcp/SKILL.md",
        "computedHash": "31751fb6b691c047240d05a112f49113509d1d5f77a87b8afbf3cc070fea30c6"
      },
      "tribev2": {
        "source": "facebookresearch/tribev2",
        "sourceType": "github",
        "skillPath": "skills/tribev2/SKILL.md",
        "computedHash": "63dd2da3470700a1fa7a57c79e085830c95e504228dbcaa650f8bf9dbfb90bff"
      },
      "urbit": {
        "source": "urbit/urbit",
        "sourceType": "github",
        "skillPath": "skills/urbit/SKILL.md",
        "computedHash": "84c45b284579501b17241b119f18df0d1d95c157b2960f440377fbca6c1c19f1"
      }
    }
  };
}

const skillFile = 'skills/software-copyright-materials/SKILL.md';
const content = fs.readFileSync(skillFile);
const hash = crypto.createHash('sha256').update(content).digest('hex');

lockData.skills['software-copyright-materials'] = {
  source: 'Fokkyp/SoftwareCopyright-Skill',
  sourceType: 'github',
  skillPath: skillFile,
  computedHash: hash
};

fs.writeFileSync(lockFile, JSON.stringify(lockData, null, 2));
