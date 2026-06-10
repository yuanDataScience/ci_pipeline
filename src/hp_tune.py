import json
import numpy as np
import pandas as pd
import yaml

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
import optuna

from utils import (PROCESSED_TRAINING_DATASET, load_data, get_hp_tuning_results,
                   RFC_BEST_PARRMS, HP_TUNE_RESULTS, TARGET_COLUMN,
                   SEED, PARAMS_CONFIG, create_preprocess_pipeline)


def hp_tune_pipeline(train_x: pd.DataFrame, train_y: pd.Series,
                     params: dict, seed: int, num_trials: int,
                     cv_splits: int = 10) -> optuna.study.study.Study:
    """
    1. fine tune hyper-parameters following preprocess pipeline
    2. fine tune using optuna

    Parameters:
    Train_X: Pandas dataframe containing features
    Train_y: Pandas series containing targets

    Returns:
    Pipeline: sklearn pipeline
    """

    n_estimators_min = params["train"]["n_estimators"]["min"]
    n_estimators_max = params["train"]["n_estimators"]["max"]
    max_depth_min = params["train"]["max_depth"]["min"]
    max_depth_max = params["train"]["max_depth"]["max"]

    def objective(trial):
        n_estimators = trial.suggest_int("n_estimators", n_estimators_min, n_estimators_max)
        max_depth = trial.suggest_int("max_depth", max_depth_min, max_depth_max)

        preprocessor = create_preprocess_pipeline()
        rf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=seed
        )
        cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=seed)
        rf_train_pipeline = Pipeline([
            ('preprocess', preprocessor),
            ('model', rf)
        ])

        try:
            scores = cross_val_score(rf_train_pipeline, train_x, train_y, cv=cv, scoring="roc_auc")

            trial.set_user_attr("cv_scores", scores.tolist())
            trial.set_user_attr("cv_mean", float(scores.mean()))
            trial.set_user_attr("cv_std", float(scores.std()))

            return np.mean(scores)
        except ValueError:
            return float("-inf")  # Penalize failed trials

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=num_trials)

    return study


def main():
    train_X, train_y = load_data(PROCESSED_TRAINING_DATASET, TARGET_COLUMN)

    with open(PARAMS_CONFIG) as f:
        params = yaml.safe_load(f)

    study = hp_tune_pipeline(train_X, train_y, params, SEED, 10)
    best_params = study.best_params
    best_params['random_state'] = SEED

    print("====================Best Hyperparameters==================")
    print(json.dumps(best_params, indent=2))
    print("==========================================================")

    with open(RFC_BEST_PARRMS, "w") as outfile:
        json.dump(best_params, outfile)

    markdown_table = get_hp_tuning_results(study)
    with open(HP_TUNE_RESULTS, "w") as markdown_file:
        markdown_file.write(markdown_table)


if __name__ == "__main__":
    main()
