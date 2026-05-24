const { ethers } = require("ethers");
const ENS = require("@ensdomains/ensjs").default;

async function registerAsiOwlEth() {
    const provider = new ethers.JsonRpcProvider(process.env.ETH_RPC_URL);
    const signer = new ethers.Wallet(process.env.CATHEDRAL_PRIVATE_KEY, provider);

    const ens = new ENS();
    await ens.setProvider(provider);

    // Name to register
    const name = "asi.owl.eth";

    // Verify availability
    const available = await ens.isAvailable(name);
    if (!available) {
        console.log(name + " is already registered. Updating IPFS pointer...");
    }

    // Register or get the name
    const controller = await ens.getController(name);
    const commitment = await controller.makeCommitment({
        name,
        owner: signer.address,
        duration: 31536000, // 1 year
        resolver: "0x231b0Ee14048e9dCcD1d247744d114a4EB5E8E63" // Public resolver
    });

    // Set the IPFS pointer
    const ipfsCid = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi";
    const resolver = await ens.getResolver(name);
    await resolver.setText("ipfs.cid", ipfsCid, { signer });

    console.log("asi.owl.eth configured to ipfs://" + ipfsCid);
    console.log("Resolver: https://app.ens.domains/asi.owl.eth");
}

registerAsiOwlEth();
