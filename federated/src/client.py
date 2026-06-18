from collections import OrderedDict
from typing import Any

import flwr as fl
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .model import Net

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_parameters(model: nn.Module) -> list[np.ndarray]:
    return [val.cpu().numpy() for _, val in model.state_dict().items()]


def set_parameters(model: nn.Module, parameters: list[np.ndarray]) -> None:
    state_dict = OrderedDict(
        {
            k: torch.tensor(v)
            for k, v in zip(model.state_dict().keys(), parameters, strict=True)
        }
    )
    model.load_state_dict(state_dict, strict=True)


def train_one_epoch(model: nn.Module, trainloader: DataLoader) -> float:
    model.train()
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
    total_loss = 0.0
    for images, labels in trainloader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        loss = criterion(model(images), labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(trainloader)


class FlowerClient(fl.client.NumPyClient):
    def __init__(self, trainloader: DataLoader) -> None:
        self.model = Net().to(DEVICE)
        self.trainloader = trainloader

    def get_parameters(self, config: dict[str, Any]) -> list[np.ndarray]:
        return get_parameters(self.model)

    def fit(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Any],
    ) -> tuple[list[np.ndarray], int, dict[str, Any]]:
        set_parameters(self.model, parameters)
        loss = train_one_epoch(self.model, self.trainloader)
        return get_parameters(self.model), len(self.trainloader.dataset), {"loss": loss}

    def evaluate(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Any],
    ) -> tuple[float, int, dict[str, Any]]:
        set_parameters(self.model, parameters)
        model = self.model
        model.eval()
        criterion = nn.CrossEntropyLoss()
        total_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in self.trainloader:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = model(images)
                total_loss += criterion(outputs, labels).item()
                correct += (outputs.argmax(1) == labels).sum().item()
                total += labels.size(0)
        return total_loss / len(self.trainloader), total, {"accuracy": correct / total}
