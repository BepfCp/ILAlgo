from algo.base import BaseAgent
from utils.buffer import SimpleReplayBuffer

class BaseImitator(BaseAgent):
    """Base agent class for IL
    """
    def __init__(self, configs):
        super().__init__(configs, init_buffer=False)
        
        self.dataset = configs['dataset']
        self._load_expert_data()
        
    def _load_expert_data(self):
        self.expert_size = self.dataset['rewards'].shape[0]
        self.expert_buffer = SimpleReplayBuffer(self.state_dim, self.action_dim, self.device, self.expert_size)
        
        for i in range(self.expert_size):
            obs = self.dataset['observations'][i]
            next_obs = self.dataset['next_observations'][i]
            action = self.dataset['actions'][i]
            reward = self.dataset['rewards'][i]
            done = self.dataset['terminals'][i]
            self.expert_buffer.add(obs, action, next_obs, reward, done)
    