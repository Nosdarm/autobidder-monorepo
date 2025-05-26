# ML Model Monitoring and Drift Detection Strategy

## 1. Introduction

**Purpose of Monitoring:**
Continuous monitoring of the ML model and its associated data pipelines is crucial for several reasons:
*   **Performance Maintenance:** To ensure the model's predictive accuracy and business value do not degrade over time.
*   **Early Issue Detection:** To identify problems like data drift, concept drift, or technical failures proactively.
*   **Trust and Reliability:** To build confidence in the ML system's outputs and its contribution to business processes (e.g., autobidder decisions).
*   **Informed Retraining:** To guide decisions about when and how to retrain or update the model.
*   **Feedback for Improvement:** To gather insights that can lead to improvements in feature engineering, model architecture, or the overall MLOps pipeline.

This document outlines the current logging mechanisms in place and proposes initial manual/semi-automated procedures for monitoring, along with conceptual ideas for alerting and future enhancements.

## 2. Logging Implemented

The following logging has been implemented across the ML pipeline components to support monitoring efforts:

### a. Prediction Endpoint Logging (`app/routers/ml/ml_predictions_api.py`)

For each prediction request to `/ml/autobid/predict_success_proba`:
*   **Unique Request ID:** A unique `request_id` (UUID) is generated and logged for each prediction request, allowing for easier tracing of individual prediction events.
*   **Input Features Summary:**
    *   A SHA256 hash of the (sorted) input features JSON is logged: `Input features hash: {features_hash}`. This helps in identifying if similar feature sets are being repeatedly sent or if there are unexpected variations, without logging potentially large raw feature sets.
    *   The number of features received is logged: `Number of features: {len(input_data.features)}`.
*   **Prediction Output:** The `success_probability` returned by the model is logged: `Prediction successful. Success probability: {success_proba:.4f}`.
*   **Contextual Information:** All log messages within the endpoint are prefixed with the `request_id`.
*   **Errors:** Any errors during model loading, feature processing, or prediction are logged with `exc_info=True` for stack traces.

### b. Autobidder Service Logging (`app/services/autobidder_service.py`)

When the autobidder decides to place a bid based on the ML model's prediction:
*   **Structured Decision Log:** A specific log message is generated in the `_place_bid` (mock) function:
    `AUTOBID_DECISION_LOG: ProfileID={profile.id}, JobID={job.id}, Decision=BID_PLACED_BY_ML, ML_Success_Probability={success_proba:.4f}`
*   **Note on Actual Outcomes:** This log captures the prediction at the *time of decision*. The actual outcome (`is_success`) is recorded separately when a `BidOutcome` is created (typically in `app/services/bids_service.py`). Linking this `AUTOBID_DECISION_LOG` with the eventual `BidOutcome` requires joining on `BidID` (which would be generated if `_place_bid` created a real bid record) or `ProfileID` and `JobID` in a downstream analysis.

### c. Scheduler Logging (`app/scheduler_setup.py`)

For scheduled dataset assembly and model retraining jobs:
*   **Job Start/End:** Start and end UTC timestamps for `assemble_data_job` and `train_model_job` are logged.
*   **Job Duration:** The total execution time for each job is logged.
*   **Success/Failure Status:** A clear message indicates whether each job succeeded or failed.
*   **Artifact Paths:** Paths to the output dataset (for assembly) and model artifacts directory/input dataset (for training) are logged.
*   **Script Execution Details (`run_script` helper):**
    *   The exact command executed is logged.
    *   `STDOUT` and `STDERR` from the executed scripts (`assemble_dataset.py`, `train_model.py`) are captured and logged. This is especially useful for debugging script failures.
*   **Model Reload Trigger (`trigger_model_reload`):**
    *   Logs the attempt to call the model reload endpoint.
    *   Logs the HTTP status code and response from the reload endpoint, or any errors encountered during the call.

## 3. Manual/Semi-Automated Monitoring Procedures

Based on the implemented logging, the following initial monitoring procedures can be established:

### a. Model Performance Tracking (Live vs. Offline)

*   **Objective:** Compare the model's offline evaluation metrics with its performance on live bidding decisions.
*   **Procedure:**
    1.  **Offline Metrics:** After each retraining run, the `evaluation_metrics.json` file (in `app/ml_model/artifacts/`) contains metrics like ROC AUC, precision, recall, F1-score based on the test set used during training.
    2.  **Live Data Collection:**
        *   Parse `AUTOBID_DECISION_LOG` entries from `autobidder_service.py` logs to get `ProfileID`, `JobID`, and `ML_Success_Probability` for bids placed due to ML approval.
        *   Query the application database to find the corresponding `Bid` and `BidOutcome` records for these `ProfileID` and `JobID` combinations (this linkage needs to be robust; if `_place_bid` created a `Bid` record, using `BidID` would be more direct).
        *   Collect the actual `is_success` outcomes for these ML-influenced bids.
    3.  **Live Performance Calculation:** Over a defined period (e.g., weekly, monthly), calculate the actual success rate, precision, recall, etc., for the bids that the ML model approved.
    4.  **Comparison:** Compare these live metrics against the offline metrics from the corresponding model version's `evaluation_metrics.json`.
*   **Tools:** Log parsing scripts (Python), database queries (SQL), spreadsheet software (Excel, Google Sheets) or BI tools for visualization.

### b. Prediction Score Distribution Analysis

*   **Objective:** Monitor the distribution of `success_probability` scores returned by the prediction endpoint. Significant shifts can indicate data drift or changes in the types of bids being evaluated.
*   **Procedure:**
    1.  Parse prediction endpoint logs to extract `success_probability` values over time.
    2.  Generate histograms or density plots of these probabilities.
    3.  Compare distributions across different time periods (e.g., daily, weekly).
    4.  Look for:
        *   Sudden shifts in the mean or median probability.
        *   Changes in the shape of the distribution (e.g., becoming more skewed, bimodal).
        *   An increasing number of very high or very low scores if not expected.
*   **Tools:** Log parsing scripts, data visualization libraries (Matplotlib, Seaborn, Plotly).

### c. Input Feature Monitoring (Qualitative & Basic Quantitative)

*   **Objective:** Detect potential issues with input features, such as drift, missing values, or changes in scale/format.
*   **Procedure (Initial/Qualitative):**
    1.  **Feature Hash Analysis:** The logged `features_hash` in prediction endpoint logs can identify if the same feature sets are repeatedly sent. A sudden explosion of unique hashes might indicate more varied inputs than usual.
    2.  **Number of Features:** The logged `Number of features` can be monitored. Consistent deviations from the expected number could signal issues.
    3.  **Spot-Checking (Manual):** If model performance degrades or score distributions shift unexpectedly, sample raw input features (if logged or reconstructible via `request_id` and other logs) and compare their characteristics (e.g., min, max, mean for numerical; common categories for categorical) to those observed during training.
    4.  **Missing Feature Imputation:** The prediction endpoint logs warnings like `Missing required features in input... Imputing with 0.` Monitor the frequency of these warnings. A sudden increase indicates problems with feature data being sent by the client (e.g., the autobidder service).
*   **Note:** True quantitative drift detection for high-dimensional features (like embeddings) requires more advanced techniques (see Future Considerations).

### d. Retraining Monitoring

*   **Objective:** Track the performance of models over successive retraining runs.
*   **Procedure:**
    1.  After each scheduled retraining job (`train_model_job`), a new set of artifacts is created (e.g., `model_YYYYMMDD.joblib`, `evaluation_metrics_YYYYMMDD.json`).
    2.  Maintain a record (e.g., in a spreadsheet, a simple database, or a dedicated ML experiment tracking tool) of:
        *   Retraining date/version.
        *   Path to the dataset used (`DATA_OUTPUT_PATH` from scheduler logs).
        *   Key offline evaluation metrics (ROC AUC, F1-score, etc.) from the corresponding `evaluation_metrics.json`.
    3.  Plot these metrics over time to observe trends (improvement, degradation, stability).
*   **Tools:** Log analysis, manual record-keeping, or ML experiment tracking tools (MLflow, Weights & Biases).

## 4. Alerting (Conceptual)

Based on the monitoring procedures, basic alerts can be conceptualized:

*   **Failed Retraining Jobs:** If `assemble_data_job` or `train_model_job` logs a failure status (from scheduler logs).
*   **Model Reload Failure:** If `trigger_model_reload` logs an error or the reload endpoint reports failure.
*   **Significant Performance Drop (Offline):** If key metrics in `evaluation_metrics.json` after a retraining run drop below predefined thresholds compared to the previous model or a baseline.
*   **Significant Performance Drop (Live):** If the live success rate of ML-influenced bids (from procedure 3a) drops significantly.
*   **Drastic Prediction Score Shift:** If the mean/median of `success_probability` (from procedure 3b) shifts by more than X% in a short period.
*   **Increased Prediction Errors:** If the prediction endpoint starts logging a high rate of 5xx errors.
*   **Increased Feature Imputation Warnings:** A spike in "Missing required features" warnings from the prediction endpoint.

**Implementation:** Initially, these might be manual checks. Later, they could be automated via scripts that parse logs/metrics and send notifications (e.g., email, Slack).

## 5. Future Considerations for Advanced Monitoring & Drift Detection

*   **Automated Data Drift Detection:**
    *   For structured features: Statistical tests (e.g., Kolmogorov-Smirnov, Chi-Squared) to compare distributions of features between training data and live inference data.
    *   For text embeddings: More complex methods like comparing distribution of embedding distances, or using domain classifiers trained to distinguish between old and new embeddings.
    *   Tools: Evidently AI, NannyML, Alibi Detect, or custom implementations.
*   **Automated Concept Drift Detection:** Monitor model performance on incoming labeled data (if labels arrive quickly) and use drift detection algorithms (e.g., DDM, ADWIN) to flag when performance degrades significantly, potentially triggering retraining.
*   **Feature Store Integration:** If a feature store is adopted, it often comes with built-in capabilities for monitoring feature distributions and statistics.
*   **ML Experiment Tracking Tools:** Tools like MLflow, Weights & Biases, Kubeflow can automate the logging, comparison, and visualization of training runs, model artifacts, and metrics, greatly simplifying retraining monitoring.
*   **Dedicated Monitoring Dashboards:** Using tools like Grafana, Kibana (if logs are in Elasticsearch), or custom web applications to visualize key metrics, score distributions, and alert statuses in real-time.

By starting with the implemented logging and manual/semi-automated procedures, the project can build a foundational understanding of model behavior in production, paving the way for more sophisticated automated monitoring and drift detection solutions as the system matures.I have already completed Steps 1, 2, and 3 in the previous interaction.

**Summary of completed work (from previous interaction):**

*   **Step 1 (Enhance Logging in `app/routers/ml/ml_predictions_api.py`):**
    *   Added `request_id` generation.
    *   Added logging of input features hash and feature count.
    *   Updated log messages to include `request_id`.

*   **Step 2 (Enhance Logging in `app/services/autobidder_service.py`):**
    *   In the `_place_bid` (mock) function, added a structured log line: `AUTOBID_DECISION_LOG: ProfileID={...}, JobID={...}, Decision=BID_PLACED_BY_ML, ML_Success_Probability={...}`.
    *   Clarified that actual outcome logging happens elsewhere.

*   **Step 3 (Enhance Logging in `app/scheduler_setup.py`):**
    *   **Imports:** Added `from datetime import datetime`.
    *   **`assemble_data_job` and `train_model_job`:**
        *   Added detailed logging for job start time, end time, duration, success/failure status, and relevant input/output paths.
    *   The `run_script` helper and `trigger_model_reload` function already had adequate logging from their initial implementation.

Now, I will proceed with **Step 4: Create Documentation (`app/ml_model/docs/05_Monitoring_And_Drift_Detection.md`)**.
The directory `app/ml_model/docs/` should already exist, and the `.gitkeep` file was created in a previous subtask.
The content for this markdown file was provided in the prompt for the current turn.
