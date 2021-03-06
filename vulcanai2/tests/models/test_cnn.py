"""Test all ConvNet capabilities."""
import pytest
import numpy as np
import torch
from vulcanai2.models.cnn import ConvNet
from torch.utils.data import TensorDataset, DataLoader


class TestConvNet:
    """Define ConvNet test class."""

    @pytest.fixture
    def cnn_noclass(self):
        """Create ConvNet with no prediction layer."""
        return ConvNet(
            name='Test_ConvNet_noclass',
            in_dim=(1, 28, 28),
            config={
                'conv_units': [
                    {
                        "in_channels": 1,
                        "out_channels": 16,
                        "kernel_size": (5, 5),
                        "pool_size": 2,
                        "stride": 2
                    },
                    {
                        "in_channels": 16,
                        "out_channels": 1,
                        "kernel_size": (5, 5),
                        "stride": 2,
                        "padding": 2
                    }]
            }
        )

    @pytest.fixture
    def cnn_class(self):
        """Create ConvNet with prediction layer."""
        return ConvNet(
            name='Test_ConvNet_class',
            in_dim=(1, 28, 28),
            config={
                'conv_units': [
                    {
                        "in_channels": 1,
                        "out_channels": 16,
                        "kernel_size": (5, 5),
                        "pool_size": 2,
                        "stride": 2
                    },
                    {
                        "in_channels": 16,
                        "out_channels": 1,
                        "kernel_size": (5, 5),
                        "stride": 2,
                        "padding": 2
                    }]
            },
            num_classes=3
        )

    def test_forward_not_nan(self, cnn_noclass):
        """Confirm out is non nan."""
        test_input = torch.ones([1, *cnn_noclass.in_dim])
        test_dataloader = DataLoader(TensorDataset(test_input, test_input))
        output = cnn_noclass.forward_pass(
            data_loader=test_dataloader,
            convert_to_class=False)
        assert np.any(~np.isnan(output))

    def test_forward_class_not_nan(self, cnn_class):
        """Confirm out is non nan."""
        test_input = torch.ones([1, *cnn_class.in_dim])
        test_dataloader = DataLoader(TensorDataset(test_input, test_input))
        raw_output = cnn_class.forward_pass(
            data_loader=test_dataloader,
            convert_to_class=False)
        class_output = cnn_class.metrics.extract_class_labels(
            in_matrix=raw_output)
        assert np.any(~np.isnan(class_output))
        assert np.any(~np.isnan(raw_output))

    def test_freeze_class(self, cnn_class):
        """Test class network freezing."""
        cnn_class.freeze(apply_inputs=False)
        for params in cnn_class.network.parameters():
            assert params.requires_grad is False

    def test_unfreeze_class(self, cnn_class):
        """Test class network unfreezing."""
        cnn_class.freeze(apply_inputs=False)
        cnn_class.unfreeze(apply_inputs=False)
        for params in cnn_class.network.parameters():
            assert params.requires_grad is True

    def test_freeze_noclass(self, cnn_noclass):
        """Test intermediate network freezing."""
        cnn_noclass.freeze(apply_inputs=False)
        for params in cnn_noclass.network.parameters():
            assert params.requires_grad is False

    def test_unfreeze_noclass(self, cnn_noclass):
        """Test intermediate network unfreezing."""
        cnn_noclass.freeze(apply_inputs=False)
        cnn_noclass.unfreeze(apply_inputs=False)
        for params in cnn_noclass.network.parameters():
            assert params.requires_grad is True

    def test_add_input_network(self, cnn_noclass, cnn_class):
        """Test add input Network functionality."""
        cnn_class.add_input_network(cnn_noclass)
        assert cnn_class.input_networks[cnn_noclass.name] is cnn_noclass
        assert cnn_class.in_dim == cnn_noclass.out_dim
