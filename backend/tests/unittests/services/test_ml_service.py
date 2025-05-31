import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np
import pandas as pd

from backend.app.services import ml_service
from backend.app.schemas.ml import PredictionFeaturesInput, PredictionResponse

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_model_pipeline():
    """Creates a mock scikit-learn pipeline object."""
    mock_pipeline = MagicMock()
    # Mock the predict_proba method
    mock_pipeline.predict_proba.return_value = np.array([[0.2, 0.8]]) # Example probability for two classes

    # Mock feature_names_in_ if your ml_service uses it
    # This depends on how CountVectorizer/TFIDFVectorizer was trained and if it stores feature names.
    # If the pipeline was trained on a DataFrame with specific column names,
    # and CountVectorizer was configured to use one of them.
    # For the "text_feature_for_pipeline" key used in job_service test:
    mock_pipeline.feature_names_in_ = np.array(["text_feature_for_pipeline"])
    return mock_pipeline

async def test_predict_success_proba_service_with_score(mock_model_pipeline):
    """
    Tests predict_success_proba_service with a mocked model,
    ensuring it calculates and returns the score correctly.
    """
    # Patch the global MODEL object in ml_service module
    with patch.object(ml_service, 'MODEL', mock_model_pipeline):
        # Ensure MODEL_PATH is also set if the service uses it for logging or info
        with patch.object(ml_service, 'MODEL_PATH') as mock_model_path:
            mock_model_path.name = "mock_model.pkl"

            input_features = PredictionFeaturesInput(features={"text_feature_for_pipeline": "This is a test job description."})

            response = await ml_service.predict_success_proba_service(input_features)

            # Assertions
            assert response is not None
            assert isinstance(response, PredictionResponse)

            expected_proba = 0.8
            expected_score = expected_proba * 100

            assert response.success_probability == pytest.approx(expected_proba)
            assert response.score == pytest.approx(expected_score)
            assert response.model_info == "Using model: mock_model.pkl"

            # Check if predict_proba was called correctly
            # It expects a DataFrame. ml_service.py constructs this DataFrame.
            # We need to check that predict_proba was called with a DataFrame
            # that has the 'text_feature_for_pipeline' column and correct value.

            # Get the DataFrame passed to predict_proba
            # call_args[0] is a tuple of positional arguments
            # The first positional argument to predict_proba is the DataFrame
            df_passed_to_predict = mock_model_pipeline.predict_proba.call_args[0][0]

            assert isinstance(df_passed_to_predict, pd.DataFrame)
            assert "text_feature_for_pipeline" in df_passed_to_predict.columns
            assert df_passed_to_predict["text_feature_for_pipeline"].iloc[0] == "This is a test job description."
            mock_model_pipeline.predict_proba.assert_called_once()

async def test_predict_success_proba_service_model_not_loaded():
    """
    Tests predict_success_proba_service when the model is not loaded (MODEL is None).
    """
    with patch.object(ml_service, 'MODEL', None): # Ensure model is None
        with patch.object(ml_service, 'logger') as mock_logger: # Optional: check logging
            input_features = PredictionFeaturesInput(features={"text_feature_for_pipeline": "Test text"})

            with pytest.raises(ml_service.HTTPException) as exc_info:
                await ml_service.predict_success_proba_service(input_features)

            assert exc_info.value.status_code == 503
            assert "Model not loaded" in exc_info.value.detail
            mock_logger.error.assert_called_once() # Check that an error was logged

async def test_load_model_on_startup_success(monkeypatch, mock_model_pipeline):
    """Tests successful model loading."""
    mock_joblib_load = MagicMock(return_value=mock_model_pipeline)
    monkeypatch.setattr(ml_service.joblib, 'load', mock_joblib_load)

    mock_path_exists = MagicMock(return_value=True)
    mock_path_isfile = MagicMock(return_value=True)

    # Create a mock Path object for MODEL_PATH
    mock_model_path_obj = MagicMock(spec=ml_service.Path)
    mock_model_path_obj.exists.return_value = True
    mock_model_path_obj.is_file.return_value = True
    mock_model_path_obj.__str__.return_value = "/fake/path/model.pkl" # for logging

    monkeypatch.setattr(ml_service, 'MODEL_PATH', mock_model_path_obj)
    monkeypatch.setattr(ml_service, 'MODEL', None) # Ensure model is None initially

    with patch.object(ml_service, 'logger') as mock_logger:
        ml_service.load_model_on_startup()

        assert ml_service.MODEL is mock_model_pipeline
        mock_joblib_load.assert_called_once_with(mock_model_path_obj)
        mock_logger.info.assert_called_with(f"ML Model loaded successfully from {mock_model_path_obj}")

async def test_load_model_on_startup_file_not_found(monkeypatch):
    """Tests model loading when file does not exist."""
    mock_path_exists = MagicMock(return_value=False)

    mock_model_path_obj = MagicMock(spec=ml_service.Path)
    mock_model_path_obj.exists.return_value = False
    mock_model_path_obj.__str__.return_value = "/fake/path/non_existent_model.pkl"

    monkeypatch.setattr(ml_service, 'MODEL_PATH', mock_model_path_obj)
    monkeypatch.setattr(ml_service, 'MODEL', "dummy_model") # Ensure model is not None initially

    with patch.object(ml_service, 'logger') as mock_logger:
        ml_service.load_model_on_startup()

        assert ml_service.MODEL is None
        mock_logger.warning.assert_called_with(f"Model file not found at {mock_model_path_obj}. Prediction endpoint will be inactive.")

# Add more tests for other scenarios in ml_service.py, like handling different feature inputs,
# missing features, etc., if those parts of ml_service.py are complex.
# The current tests cover the main new functionality (score) and basic model loading.
# The `feature_names_in_` part of the mock_model_pipeline is important if your ml_service.py
# uses this attribute to construct the DataFrame for prediction.
# The key "text_feature_for_pipeline" in `input_features` should match what the
# `CountVectorizer` in the pipeline expects if it was trained on named features/columns.
# If the `CountVectorizer` takes the first column of a DataFrame by default, then the name might not matter
# as long as `ml_service.py` correctly creates a DataFrame with that single column of text.
# The test for `predict_success_proba_service` assumes that `ml_service.py` correctly
# handles the `PredictionFeaturesInput` and transforms it into the DataFrame shape
# that the mocked `predict_proba` (and thus the real `CountVectorizer`) expects.
# Based on current `ml_service.py`, it creates a DataFrame like `pd.DataFrame([input_data.features])`
# or tries to align with `MODEL.feature_names_in_`. The mock setup for `feature_names_in_`
# should align with this.
# If `MODEL.feature_names_in_` is `["text_feature_for_pipeline"]`, then `ml_service.py` will try to
# create `pd.DataFrame([[input_data.features.get("text_feature_for_pipeline")]], columns=["text_feature_for_pipeline"])`.
# This seems correct.
