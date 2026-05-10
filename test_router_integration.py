from temporal_network import RetroRouter, TemporalMessage, RetroNode
from recovery_email_gateway import EmailConfig, EmailAdapter
import time

node = RetroNode("TEST-NODE")
router = node.router

msg = TemporalMessage(
    id="test-msg-1",
    content="hello world",
    source_timestamp=time.time(),
    target_timestamp=time.time() + 10,
    sender_seal="SENDER",
    receiver_seal="RECEIVER"
)

config = EmailConfig(email_address="test@test.com", app_password="password")
router.enable_recovery_email(config)

router.send_message_with_fallback(msg, "PRIMARY_ROUTE")
print("Fallback message enqueued.")

item = router.recovery_gateway._outbox[0]
msg, score, chain_hash = item

try:
    email_msg = EmailAdapter.to_email(msg, config, chain_hash, score)
    print("Email successfully created.")
except Exception as e:
    print(f"Error creating email: {type(e)} {e}")
