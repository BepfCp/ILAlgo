from cmath import log
import os
import torch
from torch.distributions import Normal


class BaseAgent:
    def __init__(self, configs):
        self.configs = configs
        self.state_dim = int(configs["state_dim"])
        self.action_dim = int(configs["action_dim"])
        self.action_high = float(configs["action_high"])
        self.device = torch.device(
            configs["device"] if torch.cuda.is_available() else "cpu"
        )
        self.models = dict()

    def __call__(self):
        raise NotImplementedError

    def select_action(
        self, action_mean, action_std, training=False, calcu_log_prob=False
    ):
        with torch.no_grad():
            pi_dist = Normal(action_mean, action_std)
            if training:
                action = pi_dist.sample()
            else:
                action = action_mean
            # clip action
            if self.configs.get("clip_action"):  # for ddpg and td3
                action = torch.clamp(action, -self.action_high, self.action_high)
            if calcu_log_prob:
                log_prob = pi_dist.log_prob(action).sum(axis=-1, keepdims=True)
                return (
                    action.cpu().data.numpy().flatten(),
                    log_prob.cpu().data.numpy().flatten(),
                )
            return action.cpu().data.numpy().flatten()

    def update_param(self):
        raise NotImplementedError

    def learn(self):
        raise NotImplementedError

    def update_param(self):
        raise NotImplementedError

    def squash_action(self, action):
        return self.action_high * torch.tanh(action)  # squash and rescale output action

    def load_model(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError("Model file not found: {}".format(model_path))
        else:
            state_dicts = torch.load(model_path)
            for model in self.models:
                if isinstance(
                    self.models[model], torch.Tensor
                ):  # especially for sac, which has log_alpha to be loaded
                    self.models[model] = state_dicts[model][model]
                else:
                    self.models[model].load_state_dict(state_dicts[model])

    def save_model(self, model_path):
        if not self.models:
            raise ValueError("Models to be saved is \{\}!")
        state_dicts = {}
        for model in self.models:
            if isinstance(self.models[model], torch.Tensor):
                state_dicts[model] = {model: self.models[model]}
            else:
                state_dicts[model] = self.models[model].state_dict()
        torch.save(state_dicts, model_path)
