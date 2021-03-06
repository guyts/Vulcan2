"""Test device switching for networks."""
import pytest

from vulcanai2.models import ConvNet, DenseNet
from vulcanai2.models.utils import master_device_setter
from vulcanai2.datasets import MultiDataset

import torch
from torch.utils.data import DataLoader, TensorDataset, Subset

TEST_CUDA = torch.cuda.is_available()
TEST_MULTIGPU = TEST_CUDA and torch.cuda.device_count() >= 2
DEVICE_COUNT = 0

if TEST_CUDA:
    DEVICE_COUNT = torch.cuda.device_count()


class TestDevice:
    """Test multi-input GPU device switching."""

    @pytest.fixture
    def conv1D_net(self):
        """conv1D fixture."""
        return ConvNet(
            name='conv1D_net',
            in_dim=(1, 28),
            config={
                'conv_units': [
                    dict(
                        in_channels=1,
                        out_channels=24,
                        kernel_size=(5),
                        stride=2,
                        pool_size=2,
                        dropout=0.1
                    ),
                    dict(
                        in_channels=24,
                        out_channels=64,
                        kernel_size=(5),
                        pool_size=2,
                        dropout=0.1
                    )
                ],
            },
            device='cpu'
        )

    @pytest.fixture
    def conv2D_net(self):
        """conv2D fixture."""
        return ConvNet(
            name='conv2D_net',
            in_dim=(1, 28, 28),
            config={
                'conv_units': [
                    dict(
                        in_channels=1,
                        out_channels=24,
                        kernel_size=(5, 5),
                        stride=2,
                        pool_size=2,
                        dropout=0.1
                    ),
                    dict(
                        in_channels=24,
                        out_channels=64,
                        kernel_size=(5, 5),
                        pool_size=2,
                        dropout=0.1
                    )
                ],
            },
            device='cpu'
        )

    @pytest.fixture
    def conv3D_net(self):
        """conv3D fixture."""
        return ConvNet(
            name='conv3D_net',
            in_dim=(1, 28, 28, 28),
            config={
                'conv_units': [
                    dict(
                        in_channels=1,
                        out_channels=16,
                        kernel_size=(5, 5, 5),
                        stride=2,
                        dropout=0.1
                    ),
                    dict(
                        in_channels=16,
                        out_channels=64,
                        kernel_size=(5, 5, 5),
                        dropout=0.1
                    )
                ],
            }
        )

    @pytest.fixture
    def dense_net(self, conv1D_net, conv2D_net):
        """Dense network fixture with two inputs."""
        return DenseNet(
            name='dense_net',
            input_networks=[conv1D_net, conv2D_net],
            config={
                'dense_units': [100, 50],
                'initializer': None,
                'bias_init': None,
                'norm': None,
                'dropout': 0.5,  # Single value or List
            },
            device='cpu'
        )

    @pytest.fixture
    def multi_net(self, conv3D_net, dense_net):
        """Bottom multi-input network fixture."""
        return ConvNet(
            name='multi_input_network',
            input_networks=[conv3D_net, dense_net],
            num_classes=10,
            config={
                'conv_units': [
                    dict(
                        in_channels=1,
                        out_channels=16,
                        kernel_size=(3, 3, 3),
                        stride=2,
                        dropout=0.1
                    ),
                ],
            },
            device='cpu'
        )

    @pytest.mark.skipif(not TEST_CUDA, reason="No CUDA"
                        " supported devices available")
    def test_master_net_device_set_to_cuda(self, multi_net):
        """Test if the network as whole gets switched to cuda."""
        master_device_setter(multi_net, 'cuda:0')
        assert multi_net.device == torch.device(type='cuda', index=0)
        assert multi_net.input_networks['conv3D_net']\
            .device == torch.device(type='cuda', index=0)
        assert multi_net.input_networks['dense_net']\
            .device == torch.device(type='cuda', index=0)
        assert multi_net.input_networks['dense_net'].\
            input_networks['conv1D_net'].\
            device == torch.device(type='cuda', index=0)
        assert multi_net.input_networks['dense_net'].\
            input_networks['conv2D_net'].\
            device == torch.device(type='cuda', index=0)

    @pytest.mark.skipif(not TEST_CUDA, reason="No CUDA"
                        " supported devices available")
    def test_fail_mixed_devices(self, multi_net, conv3D_net,
                                dense_net, conv1D_net):
        """Test training throws ValueError when network has mixed devices."""
        master_device_setter(multi_net, 'cuda:0')
        assert conv3D_net == multi_net.input_networks['conv3D_net']
        assert dense_net == multi_net.input_networks['dense_net']

        dense_net_data = MultiDataset([
                (
                    TensorDataset(
                        torch.ones([10, *conv1D_net.in_dim]),
                        torch.tensor([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]).long()),
                    True, True),
                (
                    TensorDataset(torch.ones(
                        [10, *dense_net.input_networks['conv2D_net'].in_dim])),
                    True, False)
            ])

        multi_net_data = MultiDataset([
            (TensorDataset(torch.ones([10, *conv3D_net.in_dim])), True, False),
            dense_net_data
        ])

        data_len = len(multi_net_data)
        train_loader = DataLoader(
            Subset(multi_net_data, range(data_len//2)))
        valid_loader = DataLoader(
            Subset(multi_net_data, range(data_len//2, data_len)))

        multi_net.fit(
            train_loader=train_loader,
            val_loader=valid_loader,
            epochs=1,
            plot=False)

        with pytest.raises(ValueError) as e_info:
            multi_net.input_networks['conv3D_net'].device = 'cpu'
            multi_net.fit(
                train_loader=train_loader,
                val_loader=valid_loader,
                epochs=1,
                plot=False)

        assert str(e_info.value).endswith("{'conv3D_net': device(type='cpu')}")
