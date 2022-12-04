# stdlib
from typing import Any

# third party
import optuna
import pytest
from sklearn.datasets import load_diabetes

# hyperimpute absolute
from hyperimpute.plugins.prediction import PredictionPlugin, Predictions
from hyperimpute.plugins.prediction.regression.plugin_neural_nets_regression import (
    plugin,
)
from hyperimpute.utils.serialization import load, save
from hyperimpute.utils.tester import evaluate_regression


def from_api() -> PredictionPlugin:
    return Predictions(category="regression").get("neural_nets_regression")


def from_module() -> PredictionPlugin:
    return plugin()


def from_pickle() -> PredictionPlugin:
    buff = save(plugin())
    return load(buff)


@pytest.mark.parametrize("test_plugin", [from_api(), from_module(), from_pickle()])
def test_neural_nets_regression_plugin_sanity(test_plugin: PredictionPlugin) -> None:
    assert test_plugin is not None


@pytest.mark.parametrize("test_plugin", [from_api(), from_module(), from_pickle()])
def test_neural_nets_regression_plugin_name(test_plugin: PredictionPlugin) -> None:
    assert test_plugin.name() == "neural_nets_regression"


@pytest.mark.parametrize("test_plugin", [from_api(), from_module(), from_pickle()])
def test_neural_nets_regression_plugin_type(test_plugin: PredictionPlugin) -> None:
    assert test_plugin.type() == "prediction"
    assert test_plugin.subtype() == "regression"


@pytest.mark.parametrize("test_plugin", [from_api(), from_module(), from_pickle()])
def test_neural_nets_regression_plugin_hyperparams(
    test_plugin: PredictionPlugin,
) -> None:
    assert len(test_plugin.hyperparameter_space()) == 6


@pytest.mark.parametrize("test_plugin", [from_api(), from_module(), from_pickle()])
def test_neural_nets_regression_plugin_fit_predict(
    test_plugin: PredictionPlugin,
) -> None:
    X, y = load_diabetes(return_X_y=True)

    score = evaluate_regression(test_plugin, X, y)

    assert score["clf"]["rmse"][0] < 5000


def test_param_search() -> None:
    if len(plugin.hyperparameter_space()) == 0:
        return

    X, y = load_diabetes(return_X_y=True)

    def evaluate_args(**kwargs: Any) -> float:
        kwargs["n_iter"] = 10

        model = plugin(**kwargs)
        metrics = evaluate_regression(model, X, y)

        return metrics["clf"]["rmse"][0]

    def objective(trial: optuna.Trial) -> float:
        args = plugin.sample_hyperparameters(trial)
        return evaluate_args(**args)

    study = optuna.create_study(
        load_if_exists=True,
        directions=["maximize"],
        study_name=f"test_param_search_{plugin.name()}",
    )
    study.optimize(objective, n_trials=10, timeout=60)

    assert len(study.trials) == 10
