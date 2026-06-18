import argparse

import flwr as fl
from flwr.common import Context

from .client import FlowerClient
from .data import load_partition
from .server import create_strategy


def run_local(num_rounds: int, num_clients: int, data_dir: str) -> None:
    strategy = create_strategy(num_clients, data_dir=data_dir)

    def client_fn(context: Context) -> fl.client.Client:
        partition_id = int(context.node_config["partition-id"])
        trainloader = load_partition(partition_id, num_clients, data_dir=data_dir)
        return FlowerClient(trainloader).to_client()

    fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=num_clients,
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Federated Learning with Flower on MNIST")
    parser.add_argument("--local", action="store_true", help="Run in local simulation mode")
    parser.add_argument("--rounds", type=int, default=5, help="Number of federated rounds")
    parser.add_argument("--clients", type=int, default=3, help="Number of simulated clients")
    parser.add_argument("--data-dir", type=str, default="./data", help="Directory for MNIST data")
    args = parser.parse_args()

    if args.local:
        run_local(args.rounds, args.clients, args.data_dir)
    else:
        run_local(args.rounds, args.clients, args.data_dir)


if __name__ == "__main__":
    main()
