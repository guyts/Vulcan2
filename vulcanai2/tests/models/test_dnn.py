"""Test all DenseNet capabilities."""
import pytest
import numpy as np
import torch
from vulcanai2.models.dnn import DenseNet
from torch.utils.data import TensorDataset, DataLoader


class TestDenseNet:
    """Define DenseNet test class."""

    @pytest.fixture
    def dnn_noclass(self):
        """Create DenseNet with no prediction layer."""
        return DenseNet(
            name='Test_DenseNet_class',
            in_dim=(200),
            config={
                'dense_units': [100, 50],
                'dropout': [0.3, 0.5],
            }
        )

    @pytest.fixture
    def dnn_class(self):
        """Create DenseNet with prediction layer."""
        return DenseNet(
            name='Test_DenseNet_class',
            in_dim=(200),
            config={
                'dense_units': [100, 50],
                'dropout': 0.5,
            },
            num_classes=3
        )

    def test_forward_not_nan(self, dnn_noclass):
        """Confirm out is non nan."""
        test_input = torch.ones([5, *dnn_noclass.in_dim])
        test_dataloader = DataLoader(TensorDataset(test_input, test_input))
        output = dnn_noclass.forward_pass(
            data_loader=test_dataloader,
            convert_to_class=False)
        assert np.any(~np.isnan(output))

    def test_forward_class_not_nan(self, dnn_class):
        """Confirm out is non nan."""
        test_input = torch.ones([5, *dnn_class.in_dim])
        test_dataloader = DataLoader(TensorDataset(test_input, test_input))
        raw_output = dnn_class.forward_pass(
            data_loader=test_dataloader,
            convert_to_class=False)
        class_output = dnn_class.metrics.extract_class_labels(
            in_matrix=test_input)
        assert np.any(~np.isnan(raw_output))
        assert np.any(~np.isnan(class_output))

    def test_freeze_class(self, dnn_class):
        """Test class network freezing."""
        dnn_class.freeze(apply_inputs=False)
        for params in dnn_class.network.parameters():
            assert params.requires_grad is False

    def test_unfreeze_class(self, dnn_class):
        """Test class network unfreezing."""
        dnn_class.freeze(apply_inputs=False)
        dnn_class.unfreeze(apply_inputs=False)
        for params in dnn_class.network.parameters():
            assert params.requires_grad is True

    def test_freeze_noclass(self, dnn_noclass):
        """Test intermediate network freezing."""
        dnn_noclass.freeze(apply_inputs=False)
        for params in dnn_noclass.network.parameters():
            assert params.requires_grad is False

    def test_unfreeze_noclass(self, dnn_noclass):
        """Test intermediate network unfreezing."""
        dnn_noclass.freeze(apply_inputs=False)
        dnn_noclass.unfreeze(apply_inputs=False)
        for params in dnn_noclass.network.parameters():
            assert params.requires_grad is True

    def test_add_input_network(self, dnn_noclass, dnn_class):
        """Test add input Network functionality."""
        dnn_class.add_input_network(dnn_noclass)
        assert dnn_class.input_networks[dnn_noclass.name] is dnn_noclass
        assert dnn_class.in_dim == dnn_noclass.out_dim
