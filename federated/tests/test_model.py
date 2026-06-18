import torch

from src.model import Net


def test_forward_shape():
    model = Net()
    x = torch.randn(2, 1, 28, 28)
    out = model(x)
    assert out.shape == (2, 10)


def test_forward_no_nan():
    model = Net()
    x = torch.randn(4, 1, 28, 28)
    out = model(x)
    assert not torch.isnan(out).any()
