# A/B Testing Framework for ML Models

## 1. Objective and Applicability of A/B Testing for ML Models

**Objective:**
The primary objective of A/B testing (or online experimentation) for ML models is to empirically evaluate the impact of a new model version (or a new feature set, or different hyperparameters) against the current production model (control) on key business metrics in a live environment. This allows for data-driven decisions about deploying model updates.

**Applicability:**
A/B testing is particularly applicable when:
*   It's crucial to understand the real-world impact of model changes before full rollout.
*   There are significant uncertainties about how a new model will perform on live, unseen data.
*   The cost of deploying a suboptimal model is high.
*   We need to compare multiple model candidates simultaneously (A/B/n testing).

For the bid success prediction model, A/B testing could help determine if a newly retrained model leads to:
*   Higher actual success rates for bids placed by the autobidder.
*   Better calibration of predicted probabilities.
*   Positive (or non-negative) impact on other business KPIs (e.g., value of won jobs, bid acceptance rate).

## 2. Key Components of an A/B Testing Framework

A robust A/B testing framework for ML models typically includes:

### a. Model Versioning & Registry

*   **Description:** A system for storing, versioning, and managing different instances of trained models. Each model should have a unique identifier and associated metadata (training date, dataset used, hyperparameters, offline evaluation metrics).
*   **Current Status:** The current `train_model.py` script saves model artifacts to `app/ml_model/artifacts/`, and the scheduler setup implies versioning by timestamp (e.g., `model_YYYYMMDD_HHMMSS.joblib`). This forms a basic versioning system. A more formal model registry (e.g., MLflow Model Registry, custom database table) would be an enhancement.

### b. Traffic Routing/Splitting Mechanism

*   **Description:** Logic to route incoming prediction requests (or user sessions, or profile IDs in our autobidder context) to different model versions (Control vs. Challenger(s)) based on predefined proportions (e.g., 50/50 split, 90/10 split).
*   **Options:**
    *   **Within the Prediction Endpoint:** The `/ml/autobid/predict_success_proba` endpoint itself could contain logic to select a model version for a given request based on `profile_id` or a random assignment. This requires the endpoint to be able to load and manage multiple model versions simultaneously.
    *   **API Gateway / Service Mesh:** If the application uses an API Gateway (e.g., Nginx, Kong, AWS API Gateway) or a service mesh (e.g., Istio, Linkerd), these tools often provide sophisticated traffic splitting capabilities.
    *   **Application-Level Router:** A dedicated routing component within the application.
*   **Granularity:** Traffic can be split per request, per user/profile, per session, etc. For autobidder, splitting by `profile_id` might be most consistent, ensuring a given profile's decisions are consistently guided by one model version during a test.

### c. Experiment Configuration

*   **Description:** A system to define, manage, and track A/B tests. This includes:
    *   Experiment name and description.
    *   Hypothesis being tested.
    *   Model versions involved (control, challenger(s)).
    *   Traffic allocation percentages.
    *   Target audience/segment (e.g., specific profiles, all profiles).
    *   Start and end dates.
    *   Key metrics to track.
*   **Implementation:** Could range from simple configuration files to a dedicated UI or database schema.

### d. Separate Performance Tracking & Data Logging

*   **Description:** Crucial for attributing outcomes correctly to the model version that influenced the decision.
*   **Mechanism:**
    *   When a prediction is made, the log (and potentially the bid data itself if stored, e.g., in `Bid.external_signals_snapshot`) must include the `model_version` used for that prediction.
    *   The `AUTOBID_DECISION_LOG` in `autobidder_service.py` should be enhanced to include `model_version`.
    *   Eventual bid outcomes (`BidOutcome` records) need to be linkable back to the bid and thus the model version used.
*   **Purpose:** Allows for segmenting performance data by model version to compare their live effectiveness.

### e. Metrics for Comparison & Analysis

*   **Description:** Define primary and secondary metrics to compare model versions.
*   **Primary Metric Examples:**
    *   Actual success rate of bids placed by the autobidder (for profiles using model A vs. model B).
    *   Lift in success rate.
*   **Secondary Metric Examples:**
    *   Average predicted probability vs. actual success rate (calibration).
    *   Number of bids placed.
    *   Distribution of prediction scores.
    *   Impact on any relevant business KPIs.
*   **Statistical Significance:** Use statistical tests (e.g., t-tests, chi-squared tests) to determine if observed differences in metrics are statistically significant or due to chance.

## 3. Workflow for an A/B Test

1.  **Define Hypothesis:** E.g., "The new model version (Challenger B) will increase the bid success rate by X% compared to the current production model (Control A)."
2.  **Configure Experiment:** Set up the A/B test parameters (models, traffic split, duration) in the experiment configuration system.
3.  **Deploy Challenger Model:** Ensure the challenger model is accessible to the traffic routing mechanism.
4.  **Run Experiment:** Activate the traffic split. Monitor service health and basic metrics closely.
5.  **Collect Data:** Log prediction requests, model versions used, autobidder decisions, and actual bid outcomes.
6.  **Analyze Results:** After a sufficient period (or number of observations):
    *   Segment data by model version.
    *   Calculate primary and secondary metrics for each version.
    *   Perform statistical significance testing.
7.  **Make Decision:**
    *   If Challenger is significantly better: Promote Challenger to be the new Control model for 100% of traffic.
    *   If Control is better or no significant difference: Keep Control model. Analyze learnings.
    *   If inconclusive: Extend test or re-evaluate.
8.  **Archive Experiment:** Document results and learnings.

## 4. Implementation Considerations for the Current Project

*   **Complexity:** Implementing a full, dynamic A/B testing framework with real-time traffic splitting across multiple concurrently loaded models is a significant engineering effort.
*   **Current Model Reload Mechanism:** The current system uses `load_model_on_startup()` which loads a single model version (e.g., `model.joblib`). The scheduled retraining job updates this model file, and a reload is triggered (or happens on app restart). This setup is not immediately conducive to serving multiple model versions simultaneously for A/B testing without changes.
*   **Feature Consistency:** Ensuring that the exact same features are available and processed identically for both control and challenger models is critical.

## 5. Recommendation for Current Project

**Short-Term (Prioritize):**

1.  **Robust Model Versioning:**
    *   Continue saving trained models with versioned names (e.g., `model_YYYYMMDD_HHMMSS.joblib`) by the `train_model.py` script.
    *   The `scheduler_setup.py` should ensure that when a new model is trained and validated (even if validation is manual initially based on offline metrics), it can be designated as the "production" model.
    *   The `MODEL_PATH` used by `load_model_on_startup` in `ml_predictions_api.py` should point to this designated production model (e.g., `app/ml_model/artifacts/model_latest.joblib`, which could be a symlink or a copy of a versioned file).

2.  **Sequential Performance Comparison (Pseudo A/B Testing):**
    *   Instead of concurrent A/B testing, leverage the periodic model retraining and deployment for sequential comparison.
    *   **Before deploying a new model (e.g., after a scheduled retrain):** Compare its offline evaluation metrics (`evaluation_metrics_YYYYMMDD.json`) with the current production model's offline metrics. Only proceed if the new model shows improvement or acceptable performance.
    *   **After deploying a new model:**
        *   Use the enhanced logging (request IDs, model info in prediction responses, `AUTOBID_DECISION_LOG`) to track the live performance of this new model version.
        *   Compare its live performance (e.g., actual success rate of ML-approved bids over the next week/month) with the live performance of the *previous* model version during its tenure.
        *   This is a "before-and-after" comparison rather than a true parallel A/B test.
    *   The advanced monitoring strategies (from `06_Advanced_Monitoring_Setup.md`), particularly tracking live model performance and comparing it to offline metrics, are key to this approach.

**Long-Term Roadmap (Future Enhancement):**

*   **Develop a Full A/B Testing Framework:**
    *   **Model Registry:** Implement a proper model registry for better management of model versions and their metadata.
    *   **Dynamic Model Loading:** Modify the prediction service to load and serve multiple model versions concurrently based on routing rules. This might involve a more sophisticated model loading mechanism than just `load_model_on_startup` for a single global model.
    *   **Traffic Splitting Logic:** Implement traffic splitting (e.g., by `profile_id`) within the prediction endpoint or via an API gateway if one is introduced.
    *   **Experiment Management UI/API:** A system to define and control experiments.
    *   **Automated Results Analysis & Reporting:** Dashboards and tools for automated analysis of A/B test results.

**Rationale for Recommendation:**
The current priority should be to solidify the existing MLOps pipeline, including robust retraining, deployment, and advanced monitoring of a single production model. This provides a stable foundation. True A/B testing adds significant complexity and is best tackled once the core system is mature and its performance characteristics are well understood through sequential comparisons and monitoring. The "sequential performance comparison" approach, while not a true A/B test, offers valuable insights with lower initial engineering overhead.I have already created `app/ml_model/docs/.gitkeep` (which ensures the directory exists) and `app/ml_model/docs/06_Advanced_Monitoring_Setup.md` in the previous interaction.

The content for `06_Advanced_Monitoring_Setup.md` was provided and used in that turn.

Now, I will proceed with creating the content for `app/ml_model/docs/07_AB_Testing_Framework.md`.
The content for this file was also provided in the prompt for the current turn.
