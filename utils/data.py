import gym
import h5py
import numpy as np
from tqdm import tqdm
import random


def _get_reset_data():
    data = dict(
        observations=[],
        actions=[],
        log_probs=[],
        rewards=[],
        next_observations=[],
        terminals=[],
        timeouts=[],
    )
    return data


def generate_expert_dataset(agent, env_name, seed, max_steps=int(1e6)):
    env = gym.make(env_name)
    env.seed(seed)
    dataset, traj_data = _get_reset_data(), _get_reset_data()
    print("Start to rollout...")
    t = 0
    obs = env.reset()
    while len(dataset["rewards"]) < max_steps:
        t += 1
        action, log_pi = agent(obs, training=False, calcu_log_pi=True)
        next_obs, reward, done, _ = env.step(action)
        timeout, terminal = False, False
        if t == env._max_episode_steps:
            timeout = True
        elif done:
            terminal = done
        # insert transition
        traj_data["observations"].append(obs)
        traj_data["actions"].append(action)
        traj_data["log_probs"].append(log_pi.cpu().data.numpy().flatten())
        traj_data["rewards"].append(reward)
        traj_data["next_observations"].append(next_obs)
        traj_data["terminals"].append(terminal)
        traj_data["timeouts"].append(timeout)

        obs = next_obs
        if terminal or timeout:
            obs = env.reset()
            t = 0
            for k in dataset:
                dataset[k].extend(traj_data[k])
            traj_data = _get_reset_data()

    dataset = dict(
        observations=np.array(dataset["observations"]).astype(np.float32),
        actions=np.array(dataset["actions"]).astype(np.float32),
        next_observations=np.array(dataset["next_observations"]).astype(np.float32),
        rewards=np.array(dataset["rewards"]).astype(np.float32),
        terminals=np.array(dataset["terminals"]).astype(np.bool),
        timeouts=np.array(dataset["timeouts"]).astype(np.bool),
    )
    for k in dataset:
        dataset[k] = dataset[k][:max_steps]  # clip the additional data
    dataset["infos/action_log_probs"] = np.array(dataset["log_probs"]).astype(
        np.float32
    )[:max_steps]
    return dataset


def _get_keys(h5file):
    keys = []

    def visitor(name, item):
        if isinstance(item, h5py.Dataset):
            keys.append(name)

    h5file.visititems(visitor)
    return keys


def read_hdf5_dataset(data_file_path):
    dataset = dict()
    with h5py.File(data_file_path, "r") as dataset_file:
        for k in tqdm(_get_keys(dataset_file), desc="load datafile"):
            dataset[k] = dataset_file[k][:]
    return dataset


def split_dataset(dataset):
    """split dataset into trajectories, return a list of start index"""
    max_step = dataset["observations"].shape[0]
    timeout_idx = np.where(dataset["timeouts"] == True)[0] + 1
    real_done_idx = np.where(dataset["terminals"] == True)[0] + 1
    start_idx = sorted(
        [0]
        + timeout_idx[timeout_idx < max_step].tolist()
        + real_done_idx[real_done_idx < max_step].tolist()
        + [max_step]
    )
    traj_pair = list(zip(start_idx[:-1], start_idx[1:]))
    return traj_pair


def get_trajectory(dataset, start_idx, end_idx):
    new_traj = {
        "observations": dataset["observations"][start_idx:end_idx],
        "actions": dataset["actions"][start_idx:end_idx],
        "log_probs": dataset["infos/action_log_probs"][start_idx:end_idx],
        "rewards": dataset["rewards"][start_idx:end_idx],
        "next_observations": dataset["next_observations"][start_idx:end_idx],
        "terminals": dataset["terminals"][start_idx:end_idx],
    }
    return new_traj


def load_expert_traj(agent, dataset, expert_traj):
    for i, (start_idx, end_idx) in enumerate(expert_traj):
        new_traj = get_trajectory(dataset, start_idx, end_idx)
        observations, actions, log_pis, next_observations, terminals = (
            new_traj["observations"],
            new_traj["actions"],
            new_traj["log_probs"],
            new_traj["next_observations"],
            new_traj["terminals"],
        )
        traj_len = actions.shape[0]
        for i in range(traj_len):
            agent.expert_buffer.add(
                observations[i],
                actions[i],
                log_pis[i],
                next_observations[i],
                terminals[i],
            )


def load_expert_dataset(configs, agent, env):
    # load dataset
    if configs["use_d4rl"]:
        dataset = env.get_dataset()
    else:  # self generated dataset
        data_file_path = configs["dataset_path"]
        dataset = read_hdf5_dataset(data_file_path)

    expert_traj_num = configs["expert_traj_num"]
    if expert_traj_num != 0:
        traj_pair = split_dataset(dataset)
        if len(traj_pair) < expert_traj_num:
            raise ValueError("Not enough expert trajectories!")
        expert_traj = random.sample(traj_pair, expert_traj_num)
        load_expert_traj(agent, dataset, expert_traj)
