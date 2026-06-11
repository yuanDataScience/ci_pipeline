import json
import yaml
import argparse

from model import evaluate_model, train_model
from utils import (PROCESSED_TRAINING_DATASET, PROCESSED_TESTING_DATASET,
                   load_data, PARAMS_CONFIG, SEED, TARGET_COLUMN)
from hp_tune import hp_tune_pipeline
from mlflow_utils import upload_training


def main(sha_id, git_sha, git_branch):
    train_X, train_y = load_data(PROCESSED_TRAINING_DATASET, TARGET_COLUMN)
    test_X, test_y = load_data(PROCESSED_TESTING_DATASET, TARGET_COLUMN)

    with open(PARAMS_CONFIG) as f:
        params = yaml.safe_load(f)

    study = hp_tune_pipeline(train_X, train_y, params, SEED, 10)
    best_params = study.best_params
    best_params['random_state'] = SEED

    # train model
    model = train_model(train_X, train_y, best_params)
    metrics = evaluate_model(model, test_X, test_y)

    print("====================Test Set Metrics==================")
    print(json.dumps(metrics, indent=2))
    print("======================================================")

    upload_training(model, metrics, best_params, git_sha, git_branch, sha_id)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--sha_id", type=str, required=True)
    parser.add_argument("--git_sha", type=str, required=True)
    parser.add_argument("--git_branch", type=str, required=True)

    args = parser.parse_args()

    main(args.sha_id, args.git_sha, args.git_branch)
