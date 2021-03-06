import logging
import tensorboardX


def get_logger(log_file):
    logger = logging.getLogger()
    logger.setLevel("DEBUG")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s: - %(message)s"
    )

    # use FileHandler to file
    fh = logging.FileHandler(log_file, mode="w")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # # use StreamHandler to screen
    # sh = logging.StreamHandler()
    # sh.setFormatter(formatter)
    # logger.addHandler(sh)

    return logger


def get_writer(tb_dir):
    writer = tensorboardX.SummaryWriter(tb_dir)
    return writer
