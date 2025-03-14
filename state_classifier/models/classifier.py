"""Model architecture definitions for state classification."""
import torch
import torch.nn as nn
from torchvision import models


class AdaptiveConcatPool2d(nn.Module):
    """
    Applies both adaptive max pooling and adaptive average pooling, then concatenates them.
    This can help preserve more information for the classifier head.
    """

    def __init__(self, output_size=1):
        """
        Initialize the module.

        Args:
            output_size (int or tuple): Size of the output
        """
        super().__init__()
        self.ap = nn.AdaptiveAvgPool2d(output_size)
        self.mp = nn.AdaptiveMaxPool2d(output_size)

    def forward(self, x):
        """Forward pass."""
        return torch.cat([self.mp(x), self.ap(x)], dim=1)


def build_classifier_head(in_features, num_classes, dropout_rate=0.5):
    """
    Build a classifier head for state classification.

    Args:
        in_features (int): Number of input features
        num_classes (int): Number of output classes
        dropout_rate (float): Dropout probability

    Returns:
        nn.Sequential: Classifier head
    """
    return nn.Sequential(
        nn.Linear(in_features, 512),
        nn.ReLU(inplace=True),
        nn.BatchNorm1d(512),
        nn.Dropout(dropout_rate),
        nn.Linear(512, num_classes)
    )


def build_state_classifier(num_classes=50, pretrained=True):
    """
    Build a ResNet101 model for state classification.

    Args:
        num_classes (int): Number of states to classify
        pretrained (bool): Whether to load pretrained weights

    Returns:
        nn.Module: State classifier model
    """
    # Load pretrained model
    if pretrained:
        model = models.resnet101(weights=models.ResNet101_Weights.IMAGENET1K_V2)
    else:
        model = models.resnet101(weights=None)

    # Freeze base layers
    for param in model.parameters():
        param.requires_grad = False

    # Replace the classifier head
    fc_in = model.fc.in_features  # typically 2048 for resnet101
    model.fc = build_classifier_head(fc_in, num_classes)

    return model


def unfreeze_model_layers(model, freeze_conv1=True, freeze_bn1=True, freeze_layer1=True,
                          freeze_layer2=True, freeze_layer3=False, freeze_layer4=False):
    """
    Selectively unfreeze layers of a ResNet model for fine-tuning.

    Args:
        model (nn.Module): ResNet model
        freeze_conv1 (bool): Whether to keep first conv layer frozen
        freeze_bn1 (bool): Whether to keep first batch norm layer frozen
        freeze_layer1-4 (bool): Whether to keep respective layers frozen

    Returns:
        nn.Module: Model with selected layers unfrozen
    """
    # First unfreeze everything
    for param in model.parameters():
        param.requires_grad = True

    # Then freeze selected layers
    if freeze_conv1:
        for param in model.conv1.parameters():
            param.requires_grad = False

    if freeze_bn1:
        for param in model.bn1.parameters():
            param.requires_grad = False

    for param in model.maxpool.parameters():
        param.requires_grad = False

    if freeze_layer1:
        for param in model.layer1.parameters():
            param.requires_grad = False

    if freeze_layer2:
        for param in model.layer2.parameters():
            param.requires_grad = False

    if freeze_layer3:
        for param in model.layer3.parameters():
            param.requires_grad = False

    if freeze_layer4:
        for param in model.layer4.parameters():
            param.requires_grad = False

    # Always ensure the head is trainable
    for param in model.fc.parameters():
        param.requires_grad = True

    return model