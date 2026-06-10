import json
import shutil
from pathlib import Path

import pandas as pd
import optuna
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
import re

from category_encoders import TargetEncoder
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

DATASET_TYPES: list[str] = ["test", "train"]
DROP_COLUMNS: list[str] = ["education"]
FILL_COLUMNS: list[str] = ["workclass"]
TARGET_ENCODE_COLUMNS: list[str] = ["workclass", "marital-status", "occupation",
                         "relationship", "native-country"]
ONE_HOT_COLUMNS: list[str] = ["race", "sex"]
NUMERICAL_COLUMNS: list[str] = ["age", "fnlwgt", "education-num", "capital-gain",
                     "capital-loss", "hours-per-week"]
TARGET_COLUMN: str = "class"
TRAINING_DATASET: str = "data/raw_dataset/train.csv"
TESTING_DATASET: str = "data/raw_dataset/test.csv"
PROCESSED_TRAINING_DATASET: str = "data/processed_dataset/train.csv"
PROCESSED_TESTING_DATASET: str = "data/processed_dataset/test.csv"
RFC_BEST_PARRMS: str = "optimized_outputs/rfc_best_params.json"
HP_TUNE_RESULTS: str = "optimized_outputs/hp_tuning_results.md"
CONFUSION_METRICS_OUTPUT: str = "metrics_plots_outputs/confusion_matrix.png"
METRICS_OUTPUT: str= "metrics_plots_outputs/metrics.json"
PREDICTIONS: str = "metrics_plots_outputs/predictions.csv"
ROC_OUTPUTS: str = "metrics_plots_outputs/roc_curve.csv"
PARAMS_CONFIG: str = "params.yaml"
SEED: int = 42


def delete_and_recreate_dir(path):
    try:
        shutil.rmtree(path)
    except:
        pass
    finally:
        Path(path).mkdir(parents=True, exist_ok=True)


def initialize_dataset():
    adult = fetch_openml(
        "adult",
        version=2,
        as_frame=True
    ).frame

    df_train, df_test = train_test_split(
        adult,
        test_size=0.25,
        stratify=adult["class"],
        random_state=SEED
    )

    df_train.to_csv(TRAINING_DATASET, index=False)
    df_test.to_csv(TESTING_DATASET, index=False)


def create_preprocess_pipeline() -> ColumnTransformer:
    """
    Feature engineering pipeline based on input Feature and target metrics
    1. Target encodes the target_encodeing categorical features and scale
    2. impute missing values based on mean for numerical columns and scale
    3. one hot encodes one_hot categorical columns


    Returns:
    Pipeline: sklearn pipeline
    """

    numerical_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="mean")),
        ("scale", StandardScaler())
    ])

    target_encode_pipeline = Pipeline([
        # ('target_encode', TargetEncoder(cols=TARGET_ENCODE_COLUMNS)),
        ('target_encode', TargetEncoder()),
        ('imputer', SimpleImputer(strategy='mean')),
        ('scale', StandardScaler())
    ])

    onehot_encode_pipeline = Pipeline([
        ('onehot_encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocess_pipeline = ColumnTransformer([
        ('onehot_encode', onehot_encode_pipeline, ONE_HOT_COLUMNS),
        ('target_encode', target_encode_pipeline, TARGET_ENCODE_COLUMNS),
        ('numeric', numerical_pipeline, NUMERICAL_COLUMNS),
    ], remainder='drop')

    return preprocess_pipeline

def load_data(filename: str, target_column: str) -> tuple[pd.DataFrame, pd.Series]:
    """
    Reads the raw data file and returns pandas dataframe
    Target column values are expected in binary format with 0/1 values

    Parameters:
    filename (str): raw data filename
    drop_columns (List[str]): column names that will be dropped
    target_column (str): name of target column

    Returns:
    pd.Dataframe: Target encoded dataframe
    """
    data = pd.read_csv(filename)
    X = data.drop(target_column, axis=1)
    y = data[target_column]
    return X, y


def load_hyperparameters(hyperparameter_file):
    with open(hyperparameter_file, "r") as json_file:
        hyperparameters = json.load(json_file)
    return hyperparameters


def get_hp_tuning_results(study: optuna.study.study.Study) -> str:
    """Get the results of hyperparameter tuning in a Markdown table"""
    df_trials = study.trials_dataframe(
        attrs=("number", "value", "params", "user_attrs"))

    # rename column names to exclude 'user_attrs_'
    col_names = [re.sub("user_attrs_", "", col) for col in df_trials.columns]
    df_trials.columns = col_names

    # Extract and split the 'cv_scores' column into subcolumns
    cv_scores_df = pd.DataFrame(
        df_trials['cv_scores'].to_list()
    )
    cv_scores_df.columns = [f"fold_{i + 1}" for i in range(cv_scores_df.shape[1])]

    # Concatenate the params_df with the original DataFrame
    cv_results = pd.concat(
        [df_trials.drop(columns="cv_scores"), cv_scores_df],
        axis=1
    )

    # Get the columns to display in the Markdown table
    cv_results = cv_results[
        ["cv_mean", "cv_std"]
        + list(cv_scores_df.columns)
        ]

    cv_results.sort_values(by="cv_mean", ascending=False, inplace=True)

    return cv_results.to_markdown(index=False)


def main():
    initialize_dataset()


if __name__ == "__main__":
    main()
