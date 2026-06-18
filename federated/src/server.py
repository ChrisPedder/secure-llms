from typing import Any

import flwr as fl
import numpy as np
import torch
from torch.utils.data import DataLoader

from .client import get_parameters, set_parameters
from .data import load_test_data
from .model import Net

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_evaluate_fn(
    data_dir: str = "./data",
):
    testloader = load_test_data(data_dir=data_dir)

    def evaluate(
        server_round: int,
        parameters: list[np.ndarray],
        config: dict[str, Any],
    ) -> tuple[float, dict[str, Any]] | None:
        model = Net().to(DEVICE)
        set_parameters(model, parameters)
        loss, accuracy = _test(model, testloader)
        print(f"Round {server_round}: loss={loss:.4f}, accuracy={accuracy:.4f}")
        return loss, {"accuracy": accuracy}

    return evaluate


def create_strategy(
    num_clients: int,
    data_dir: str = "./data",
) -> fl.server.strategy.FedAvg:
    model = Net()
    initial_parameters = fl.common.ndarrays_to_parameters(get_parameters(model))

    return fl.server.strategy.FedAvg(
        fraction_fit=1.0,
        fraction_evaluate=0.0,
        min_fit_clients=num_clients,
        min_available_clients=num_clients,
        initial_parameters=initial_parameters,
        evaluate_fn=get_evaluate_fn(data_dir),
    )


def _test(model: torch.nn.Module, testloader: DataLoader) -> tuple[float, float]:
    model.eval()
    criterion = torch.nn.CrossEntropyLoss()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in testloader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            total_loss += criterion(outputs, labels).item()
            correct += (outputs.argmax(1) == labels).sum().item()
            total += labels.size(0)
    return total_loss / len(testloader), correct / total
