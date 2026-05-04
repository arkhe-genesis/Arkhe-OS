# integrations/email/fisher_rao_middleware.py
"""
Fisher-Rao Filter middleware for email servers.
Integrates with Postfix, Exim, or cloud email services.
"""
import logging
from typing import Dict, Optional
from core.security.fisher_rao_filter import FisherRaoFilter

logger = logging.getLogger(__name__)

class FisherRaoEmailMiddleware:
    """
    Email filtering middleware implementing Substrate 116 anti-spam.

    Usage with Postfix:
      - Add to master.cf as a content filter
      - Configure policy daemon to call verify_message()

    Usage with cloud services:
      - Deploy as serverless function triggered on message receipt
      - Return verdict to email routing logic
    """

    def __init__(self, config: Dict):
        self.filter = FisherRaoFilter(
            local_branch_phase=complex(config['local_branch_phase']),
            coherence_threshold=config.get('coherence_threshold', 0.75),
            phase_tolerance=config.get('phase_tolerance', 0.1),
            jones_verification=config.get('jones_verification', True)
        )
        self.coherence_monitor = config.get('coherence_monitor', None)

    def process_incoming_message(
        self,
        sender: str,
        recipient: str,
        content: str,
        headers: Dict[str, str],
        metadata: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Processes incoming email through Fisher-Rao Filter.

        Returns:
            Dict with verdict, confidence, and action recommendation
        """
        # Extract metadata from headers if not provided
        if metadata is None:
            metadata = self._extract_metadata_from_headers(headers)

        # Get current local coherence level (from monitor or default)
        local_coherence = 0.80  # Default
        if self.coherence_monitor:
            local_coherence = self.coherence_monitor.get_current_coherence()

        # Verify message
        result = self.filter.verify_message(
            sender_id=sender,
            content=content,
            metadata=metadata,
            local_coherence=local_coherence
        )

        # Map verification result to email action
        action = self._map_verdict_to_action(result)

        # Log decision for audit
        logger.info(
            f"Fisher-Rao Filter: sender={sender}, recipient={recipient}, "
            f"verdict={'SPAM' if result['is_spam'] else 'LEGIT'}, "
            f"confidence={result['confidence']:.2f}, reason={result['reason']}"
        )

        return {
            'verdict': 'spam' if result['is_spam'] else 'legitimate',
            'confidence': result['confidence'],
            'action': action,
            'reason': result['reason'],
            'phase_difference': result.get('phase_difference'),
            'jones_consistent': result.get('jones_consistent')
        }

    def _extract_metadata_from_headers(self, headers: Dict[str, str]) -> Dict:
        """Extracts ARKHE metadata from email headers."""
        metadata = {}

        # Extract coherence state from custom header (if present)
        if 'X-ARKHE-Coherence' in headers:
            metadata['coherence_state'] = headers['X-ARKHE-Coherence']

        # Extract causal history from Authentication-Results or custom header
        if 'X-ARKHE-Causal-History' in headers:
            metadata['causal_history'] = headers['X-ARKHE-Causal-History']

        # Extract branch phase if encoded
        if 'X-ARKHE-Branch-Phase' in headers:
            metadata['branch_phase'] = headers['X-ARKHE-Branch-Phase']

        # Default intent based on standard headers
        if 'List-Unsubscribe' in headers:
            metadata['intent'] = 'promotional'
        elif 'X-Priority' in headers and headers['X-Priority'] == '1':
            metadata['intent'] = 'urgent'
        else:
            metadata['intent'] = 'general'

        # Add timestamp
        if 'Date' in headers:
            # Parse RFC 2822 date to timestamp
            from email.utils import parsedate_to_datetime
            try:
                dt = parsedate_to_datetime(headers['Date'])
                metadata['timestamp'] = dt.timestamp()
            except:
                metadata['timestamp'] = 0.0

        return metadata

    def _map_verdict_to_action(self, result: Dict) -> str:
        """Maps verification result to email handling action."""
        if not result['is_spam']:
            return 'accept'

        confidence = result['confidence']
        reason = result['reason']

        if confidence >= 0.95:
            return 'reject'  # High-confidence spam: reject at SMTP level
        elif confidence >= 0.85:
            return 'quarantine'  # Medium-confidence: quarantine for review
        elif 'phase_mismatch' in reason:
            return 'tag_inter_reality'  # Special tag for inter-reality analysis
        else:
            return 'tag_suspicious'  # Low-confidence: tag and deliver
