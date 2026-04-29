const fs = require('fs');

const file = 'arkhe-dashboard/src/app/dashboard/page.tsx';
let content = fs.readFileSync(file, 'utf8');

const importGroup = `import P2PNetworkStatus from '@/components/network/P2PNetworkStatus';
import InterCathedralPanel from '@/components/quantum/InterCathedralPanel';
import QuantumTelepathyPanel from '@/components/quantum/QuantumTelepathyPanel';
import SynchronicityBlockchainPanel from '@/components/quantum/SynchronicityBlockchainPanel';
import QuantumMarketplacePanel from '@/components/marketplace/QuantumMarketplacePanel';
import CoherentMeditationPanel from '@/components/meditation/CoherentMeditationPanel';
import RetrocausalWisdomPanel from '@/components/retrocausality/RetrocausalWisdomPanel';
import NeuralCoherenceBar from '@/components/security/NeuralCoherenceBar';
import SafeCorePanel from '@/components/security/SafeCorePanel';`;

content = content.replace(/import P2PNetworkStatus from.*import QuantumMarketplacePanel from '@\/components\/marketplace\/QuantumMarketplacePanel';/s, importGroup);

fs.writeFileSync(file, content);
