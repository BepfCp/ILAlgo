import torch
import torch.nn as nn
import numpy as np


def build_mlp_extractor(input_dim, hidden_size, activation_fn):
    """
    Create MLP feature extractor, code modified from:

    https://github.com/DLR-RM/stable-baselines3/blob/master/stable_baselines3/common/torch_layers.py
    """
    if len(hidden_size) > 0:
        mlp_extractor = [nn.Linear(input_dim, hidden_size[0]), activation_fn()]
    else:
        mlp_extractor = []

    for idx in range(len(hidden_size) - 1):
        mlp_extractor.append(nn.Linear(hidden_size[idx], hidden_size[idx + 1]))
        mlp_extractor.append(activation_fn())

    return mlp_extractor


def soft_update(rho, net, target_net):
    for param, target_param in zip(net.parameters(), target_net.parameters()):
        target_param.data.copy_(rho * param.data + (1 - rho) * target_param.data)


# Initialize Policy weights
def weights_init_(m):
    if isinstance(m, torch.nn.Linear):
        # orthogonal initialization
        torch.nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
        torch.nn.init.zeros_(m.bias)
