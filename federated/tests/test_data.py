from src.data import _partition_indices


def test_partition_indices_no_overlap():
    n = 100
    num_partitions = 3
    all_indices: set[int] = set()
    for pid in range(num_partitions):
        indices = _partition_indices(n, num_partitions, pid)
        overlap = all_indices & set(indices)
        assert len(overlap) == 0, f"Partition {pid} overlaps with previous partitions"
        all_indices.update(indices)


def test_partition_indices_cover_all():
    n = 100
    num_partitions = 3
    all_indices: set[int] = set()
    for pid in range(num_partitions):
        all_indices.update(_partition_indices(n, num_partitions, pid))
    assert all_indices == set(range(n))


def test_partition_indices_roughly_equal():
    n = 99
    num_partitions = 3
    sizes = [len(_partition_indices(n, num_partitions, pid)) for pid in range(num_partitions)]
    assert all(s == 33 for s in sizes)
