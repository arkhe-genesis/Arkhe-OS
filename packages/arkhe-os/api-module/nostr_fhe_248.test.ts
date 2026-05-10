import { NostrFHEEngine, NostrFHEConfig } from './nostr_fhe_248';
import { SecurityLevel } from './homo_privacy_221';
import { ArkheCommitEvent } from './nostr_events';

test('NostrFHEEngine encrypt and decrypt', async () => {
    const config: NostrFHEConfig = {
        encryptionLevel: SecurityLevel.TC128,
        scheme: 'CKKS'
    };
    const engine = new NostrFHEEngine(config);
    const event: ArkheCommitEvent = {
        kind: 30315,
        pubkey: "test_pubkey",
        created_at: Date.now(),
        tags: [
            ["h", "htree"],
            ["r", "repo_ref"],
            ["commit", "commit_hash"],
            ["coherence", "0.9"],
            ["seal", "seal_val"]
        ],
        content: "test payload",
        sig: "sig_val"
    };

    const encryptedEvent = await engine.encryptCommitPayload(event);
    expect(encryptedEvent.content).not.toBe("test payload");

    const decryptedContent = await engine.decryptPayload(encryptedEvent.content);
    expect(decryptedContent).toBe("test payload");
});
