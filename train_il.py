import numpy as np
from utils.config import parse_args, load_yml_config
from utils.exp import eval, preprare_training
from utils.data import load_expert_dataset


def train_imitator(configs, agent, env, logger, writer, seed, model_path):
    # load dataset
    load_expert_dataset(configs, agent, env)
    # evaluate before update, to get baseline
    writer.add_scalar(
        f"evaluation_averaged_return",
        eval(agent, configs["env_name"], seed, logger),
        global_step=0,
    )
    # train agent
    best_avg_reward = -np.inf
    for i in range(configs["max_iters"]):
        # train
        snapshot = agent.learn()
        if snapshot != None:
            for key, value in snapshot.items():
                writer.add_scalar(key, value, global_step=i + 1)
        # evaluate
        if (i + 1) % configs["eval_freq"] == 0:
            avg_reward = eval(agent, configs["env_name"], seed, logger)
            writer.add_scalar(
                f"evaluation_averaged_return",
                avg_reward,
                global_step=i + 1,
            )  # evaluate before update, to get baseline
            if avg_reward > best_avg_reward:
                best_avg_reward = avg_reward
                agent.save_model(model_path)


if __name__ == "__main__":
    # read configs
    args = parse_args()
    configs = load_yml_config(args.config)
    # train imitator
    train_imitator(*preprare_training(configs))
