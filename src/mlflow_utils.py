import os
import mlflow
from mlflow.tracking import MlflowClient
from sklearn.pipeline import Pipeline


os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://10.10.10.5:30900"
os.environ["MLFLOW_BOTO_CLIENT_ADDRESSING_STYLE"] = "path"


def upload_training(pipeline: Pipeline, metrics: dict, params:dict) -> None:
    mlflow.set_tracking_uri("http://10.10.10.5:30500")

    client = MlflowClient()

    exp_name = "mlflow-test"
    exp = client.get_experiment_by_name(exp_name)

    if exp is None:
        exp_id = client.create_experiment(exp_name)
    else:
        exp_id = exp.experiment_id

    with mlflow.start_run(experiment_id=exp_id):
        for key, val in metrics:
            mlflow.log_metric(key, val)
        for key, val in params:
            mlflow.log_param(key, val)

        mlflow.sklearn.log_model(pipeline, "test_model")

    print("mlflow upload completed")
