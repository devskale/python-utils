import argparse
import time
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Fake job for testing task scheduler.")
    parser.add_argument('--runningtime', type=int, required=True,
                        help='Seconds to simulate job running.')
    parser.add_argument('--returnval', type=int, required=True,
                        help='Exit code to return after completion.')
    args = parser.parse_args()

    print(f"Fake job started. Sleeping for {args.runningtime} seconds...")
    time.sleep(args.runningtime)
    print(f"Fake job finished. Exiting with code {args.returnval}.")
    sys.exit(args.returnval)


if __name__ == "__main__":
    main()
