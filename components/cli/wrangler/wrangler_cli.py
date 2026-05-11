import argparse
import sys
from core.protocol.fork.ledger_temporal_fork_protocol import LedgerTemporalForkProtocol

# A global mock instance for demonstration
mock_protocol = LedgerTemporalForkProtocol(main_chain_root=b"genesis_root", consensus_threshold=0.03)

def create_fork(args):
    try:
        fork_id = mock_protocol.fork_at(args.timestamp, args.reason)
        print(f"Created fork with ID: {fork_id} from timestamp {args.timestamp}")
    except ValueError as e:
        print(f"Error creating fork: {e}", file=sys.stderr)

def accept_merge(args):
    try:
        success = mock_protocol.merge_fork(args.fork_id)
        if success:
            print(f"Successfully merged fork: {args.fork_id}")
        else:
            print(f"Merge rejected for fork {args.fork_id} due to insufficient coherence gain.")
    except ValueError as e:
        print(f"Error merging fork: {e}", file=sys.stderr)

def rollback(args):
    try:
        mock_protocol.rollback_to(args.timestamp)
        print(f"Successfully rolled back main chain to timestamp: {args.timestamp}")
    except KeyError as e:
        print(f"Error during rollback: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Wrangler D1 CLI for temporal forking operations.")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # Ensure d1 subparser exists to match the requested `wrangler d1 ...` syntax
    d1_parser = subparsers.add_parser('d1', help='D1 temporal forking operations')
    d1_subparsers = d1_parser.add_subparsers(title="d1 commands", dest="d1_command")

    # Fork Create
    fork_parser = d1_subparsers.add_parser('fork', help='Fork operations')
    fork_subparsers = fork_parser.add_subparsers(title="fork commands", dest="fork_command")

    fork_create_parser = fork_subparsers.add_parser('create', help='Create a temporal fork')
    fork_create_parser.add_argument('timestamp', type=float, help='Logical timestamp to fork from')
    fork_create_parser.add_argument('reason', type=str, nargs='?', default='temporal_exploration', help='Reason for the fork')
    fork_create_parser.set_defaults(func=create_fork)

    # Merge Accept
    merge_parser = d1_subparsers.add_parser('merge', help='Merge operations')
    merge_subparsers = merge_parser.add_subparsers(title="merge commands", dest="merge_command")

    merge_accept_parser = merge_subparsers.add_parser('accept', help='Accept a temporal merge')
    merge_accept_parser.add_argument('fork_id', type=str, help='ID of the fork to merge')
    merge_accept_parser.set_defaults(func=accept_merge)

    # Rollback
    rollback_parser = d1_subparsers.add_parser('rollback', help='Rollback operations')
    rollback_parser.add_argument('timestamp', type=float, help='Logical timestamp to rollback to')
    rollback_parser.set_defaults(func=rollback)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
