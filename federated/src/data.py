from collections.abc import Sequence

from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

MNIST_TRANSFORM = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,)),
])


def load_partition(
    partition_id: int,
    num_partitions: int,
    batch_size: int = 64,
    data_dir: str = "./data",
) -> DataLoader:
    train_dataset = datasets.MNIST(data_dir, train=True, download=True, transform=MNIST_TRANSFORM)
    indices = _partition_indices(len(train_dataset), num_partitions, partition_id)
    subset = Subset(train_dataset, indices)
    return DataLoader(subset, batch_size=batch_size, shuffle=True)


def load_test_data(batch_size: int = 1000, data_dir: str = "./data") -> DataLoader:
    test_dataset = datasets.MNIST(data_dir, train=False, download=True, transform=MNIST_TRANSFORM)
    return DataLoader(test_dataset, batch_size=batch_size)


def _partition_indices(
    dataset_size: int,
    num_partitions: int,
    partition_id: int,
) -> Sequence[int]:
    all_indices = list(range(dataset_size))
    return [i for i in all_indices if i % num_partitions == partition_id]
