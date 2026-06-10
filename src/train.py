import json
import yaml


from model import evaluate_model, train_model
from utils import (PROCESSED_TRAINING_DATASET, PROCESSED_TESTING_DATASET,
                   load_data, PARAMS_CONFIG, SEED, TARGET_COLUMN)
from hp_tune import hp_tune_pipeline
from mlflow_utils import upload_training


def main():
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

    upload_training(model, metrics, best_params)



if __name__ == "__main__":
    main()