# Feedback Loop Design for Model Improvement

## 1. Objective of the Feedback Loop

The primary objective of the feedback loop is to enable continuous improvement of the bid success prediction model. This is achieved by regularly incorporating new data, including bid outcomes and potentially new features, to retrain and update the model, ensuring it adapts to changing dynamics and maintains or improves its predictive accuracy over time.

## 2. Core Principle

The core principle of this feedback loop is **periodic batch retraining**. New data (bids, job details, profile information, and especially bid outcomes) is collected continuously by the main application. This data is then periodically assembled into a new training dataset, which is used to retrain the model. The updated model then replaces the existing one in the prediction service.

## 3. Detailed Data Flow and Components

The feedback loop involves several interconnected components and data flows:

### a. Ongoing Data Collection (Application Layer)

*   **Action:** The main FastAPI application continuously collects data as users interact with the system.
*   **Key Data Points:**
    *   **Bids:** Information submitted for bids (amount, text, settings, associated job, profile). Stored in the `bids` table.
    *   **Jobs:** Details of jobs for which bids are made (description, title). Stored in the `jobs` table.
    *   **Profiles:** Information about the profiles making bids (skills, experience). Stored in the `profiles` table.
    *   **Bid Outcomes:** Crucially, the success or failure of bids. Stored in the `bid_outcomes` table. This is the primary source of labels for the supervised learning model.
    *   **External Signals:** Any other relevant data captured by the application (e.g., market trends, platform changes - though this is more advanced). Stored in `bids.external_signals_snapshot`.

### b. Scheduled Dataset Assembly

*   **Trigger:** A scheduler (e.g., cron job, APScheduler, Airflow) initiates this process at regular intervals (e.g., daily, weekly).
*   **Action:** The `app.ml_model.assemble_dataset.py` script is executed.
*   **Process:**
    1.  **Fetch Data:** The script queries the application database (using `SessionLocal`) to retrieve all bids that have recorded outcomes, along with their related job, profile, and outcome information.
    2.  **Feature Engineering:** For each bid, it generates features using the modules in `app.ml.feature_extraction/`:
        *   Text embeddings for job descriptions (`generate_job_description_embedding`).
        *   Text embeddings for generated bid text (`generate_bid_text_embedding`).
        *   Profile features (skills, experience level, type) (`generate_profile_features`).
        *   Bid temporal features (submission time, bid settings) (`generate_bid_temporal_features`).
        *   Profile historical performance features (success rates, bid frequencies over different windows) (`get_profile_historical_features`).
    3.  **Target Variable Creation:** The `is_success` field from the `BidOutcome` associated with each bid is used as the target variable.
    4.  **Output:** A consolidated, flat dataset (e.g., Pandas DataFrame) is created, where each row represents a bid with all its features and the target variable. This dataset is saved to a versioned file (e.g., `app/ml_model/data/training_dataset_YYYYMMDD.parquet`).
*   **Note on Feature Storage Interaction:** Currently, features (especially embeddings) are generated on-the-fly during dataset assembly. If a dedicated Feature Store were implemented in the future, this step would involve fetching pre-computed features from the Feature Store and joining them with the core bid/outcome data.

### c. Scheduled Model Retraining

*   **Trigger:** The scheduler initiates this process, typically after the successful completion of the dataset assembly task.
*   **Action:** The `app.ml_model.train_model.py` script is executed.
*   **Process:**
    1.  **Load Dataset:** The script loads the latest versioned dataset created by `assemble_dataset.py`.
    2.  **Data Splitting:** The dataset is split into training and testing sets.
    3.  **Model Training:** An XGBoost model (or any other chosen algorithm) is trained on the training set using the hyperparameters specified (or tuned).
    4.  **Model Evaluation:** The trained model is evaluated on the test set. Metrics (ROC AUC, precision, recall, F1-score, confusion matrix) are calculated.
    5.  **Artifact Saving:**
        *   The trained model object is serialized (e.g., `app/ml_model/artifacts/model_YYYYMMDD.joblib`).
        *   Evaluation metrics are saved (e.g., `app/ml_model/artifacts/evaluation_metrics_YYYYMMDD.json`).
        *   Feature importances are saved (e.g., `app/ml_model/artifacts/feature_importances_YYYYMMDD.csv`).

### d. Model Deployment/Activation

*   **Mechanism:** The newly trained and validated model needs to replace the one currently used by the prediction API.
*   **Initial Approach (as discussed in `01_Online_Learning_Strategy.md`):**
    1.  The `train_model.py` script, upon successful training and evaluation (meeting certain quality thresholds if implemented), updates a "latest" model file (e.g., by renaming `model_YYYYMMDD.joblib` to `model.joblib` or updating a symlink `model_latest.joblib` -> `model_YYYYMMDD.joblib`).
    2.  The FastAPI application's `load_model_on_startup()` function (in `app/routers/ml/ml_predictions_api.py`) loads the model from this fixed path (e.g., `app/ml_model/artifacts/model.joblib`).
    3.  **Activation:** This means the new model becomes active upon the next application restart/startup.
*   **Future Enhancements (Hot Swapping):**
    *   Implement an API endpoint to trigger a model reload in the running application.
    *   Use a configuration management system or service discovery to point the API to the latest model version.
    *   Employ more sophisticated deployment strategies like blue/green or canary deployments for new models.

## 4. Dataset Management

*   **Raw Data:** Resides in the primary application database. This is the source of truth.
*   **Assembled Datasets:** Versioned datasets generated by `assemble_dataset.py` should be stored in `app/ml_model/data/`. This allows for reproducibility and re-training on specific historical datasets if needed.
    *   Example: `training_dataset_20231120.parquet`, `training_dataset_20231127.parquet`.
*   **Feature Store (Future):** For more advanced scenarios, a dedicated Feature Store could be implemented. This would store pre-computed features, manage their versions, and provide an efficient way to retrieve feature vectors for training and inference. This would reduce the computational load on the `assemble_dataset.py` script.

## 5. Versioning

Comprehensive versioning is crucial for reproducibility, debugging, and rollback capabilities:

*   **Dataset Versioning:** Assembled datasets should be versioned, typically by timestamp or a unique ID (e.g., `dataset_YYYYMMDD_HHMMSS.parquet`).
*   **Model Versioning:** Trained models should also be versioned similarly (e.g., `model_YYYYMMDD_HHMMSS.joblib`). This helps in tracking which model was trained on which dataset version.
*   **Code Versioning:** All scripts (`assemble_dataset.py`, `train_model.py`, feature extraction modules, API code) must be versioned using Git. Tags can be used to mark versions used for specific model training runs.
*   **Metrics Versioning:** Evaluation metrics for each model version should be stored and versioned (e.g., `evaluation_metrics_YYYYMMDD_HHMMSS.json`), linked to the specific model and dataset version.

## 6. Diagrammatic Representation of the Loop

```
+-------------------------+      +-----------------------+      +------------------------+
| Ongoing Data Collection |----->| Scheduled Dataset     |----->| Scheduled Model        |
| (App DB: Bids,          |      | Assembly              |      | Retraining             |
|  Outcomes, Jobs,        |      | (assemble_dataset.py) |      | (train_model.py)       |
|  Profiles)              |      +----------+------------+      +-----------+------------+
+-------------------------+                 |                           |
          ^                                 |                           |
          |                                 | Versioned Dataset         | Versioned Model
          | Feedback (Implicit)             | (e.g., .parquet)          | & Metrics
          | (Model performance influences   +----------+------------+      +-----------+------------+
          |  user behavior, data captured)            |                           |
          |                                           v                           v
          |                                 +-----------------------+      +------------------------+
          +---------------------------------| Model Deployment/     |<-----| (Validation/QA Step    |
                                            | Activation (API loads |      |  - Optional, Manual or |
                                            |  latest model)        |      |  Automated)            |
                                            +-----------------------+      +------------------------+
                                                        |
                                                        v
                                            +-----------------------+
                                            | Prediction Service    |
                                            | (FastAPI Endpoint)    |
                                            |  - Uses loaded model  |
                                            +-----------------------+
```

**Explanation of Diagram:**

1.  **Ongoing Data Collection:** The application database continually gathers new data.
2.  **Scheduled Dataset Assembly:** Periodically, `assemble_dataset.py` processes this raw data into a versioned, flat dataset suitable for training.
3.  **Scheduled Model Retraining:** `train_model.py` takes the latest dataset, trains a new model, and saves the versioned model artifacts (model object, metrics).
4.  **(Optional Validation):** Before deployment, a validation step (manual or automated) can check if the new model meets quality standards.
5.  **Model Deployment/Activation:** The new model is made active in the prediction service. Initially, this might be via an application restart that loads the latest model from a predefined path.
6.  **Prediction Service:** The API uses the active model to serve predictions.
7.  **Feedback Loop (Implicit):** The predictions influence application behavior (e.g., autobidder decisions), which in turn generates new data (bid outcomes), feeding back into the "Ongoing Data Collection" stage.

This loop ensures that the model is regularly updated with the latest data and performance feedback, allowing it to adapt over time.
