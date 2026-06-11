import os
import mlflow
from mlflow.tracking import MlflowClient
from sklearn.pipeline import Pipeline


os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://10.10.10.5:30900"
os.environ["MLFLOW_BOTO_CLIENT_ADDRESSING_STYLE"] = "path"


def upload_training(pipeline: Pipeline, metrics: dict, params:dict,
                    git_sha:str, git_branch:str, sha_id:str) -> None:
    mlflow.set_tracking_uri("http://10.10.10.5:30500")

    client = MlflowClient()

    exp_name = "sklearn-adult-model-exp"
    exp = client.get_experiment_by_name(exp_name)

    if exp is None:
        exp_id = client.create_experiment(exp_name)
    else:
        exp_id = exp.experiment_id

    with mlflow.start_run(experiment_id=exp_id):
        mlflow.set_tags({
            "git_sha": git_sha,
            "git_branch": git_branch,
            "short_sha": sha_id,
            "source": "jenkins",
            "pipeline": "training",
        })

        for key, val in metrics.items():
            mlflow.log_metric(key, val)
        for key, val in params.items():
            mlflow.log_param(key, val)

        result = mlflow.sklearn.log_model(
            pipeline,
            "model",
            registered_model_name="adult_model"
        )

        if result.registered_model_version:
            client.set_model_version_tag(
                name="adult_model",
                version=result.registered_model_version,
                key="git_sha",
                value=git_sha
            )

    print("mlflow upload completed")
