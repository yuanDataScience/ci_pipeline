import json

from metrics_and_plots import save_metrics, save_predictions, save_roc_curve
from model import evaluate_model, train_model
from utils import (PROCESSED_TRAINING_DATASET, PROCESSED_TESTING_DATASET,
                   load_data, load_hyperparameters, RFC_BEST_PARRMS, TARGET_COLUMN)


def main():
    train_X, train_y = load_data(PROCESSED_TRAINING_DATASET, TARGET_COLUMN)
    test_X, test_y = load_data(PROCESSED_TESTING_DATASET, TARGET_COLUMN)

    # Load hyperparameters from the JSON file
    hyperparameters = load_hyperparameters(RFC_BEST_PARRMS)
    model = train_model(train_X, train_y, hyperparameters)
    metrics, y_pred, y_pred_proba = evaluate_model(model, test_X, test_y)

    print("====================Test Set Metrics==================")
    print(json.dumps(metrics, indent=2))
    print("======================================================")

    save_metrics(metrics)
    save_predictions(test_y, y_pred)
    save_roc_curve(test_y, y_pred_proba)


if __name__ == "__main__":
    main()