# Advanced ML Model Monitoring and Alerting Strategy

## 1. Objective of Advanced Monitoring

While basic logging and manual checks (outlined in `05_Monitoring_And_Drift_Detection.md`) provide initial visibility, an advanced monitoring strategy aims to automate the detection of issues, provide deeper insights into model behavior and data characteristics, and enable proactive responses to maintain high performance and reliability of the ML system. This includes quantitative measurement of data/concept drift and automated alerting.

## 2. Key Components to Monitor & Metrics

### a. Prediction Service Health

*   **Metrics:**
    *   **Latency:** API response time (average, percentiles like p95, p99) for the prediction endpoint (`/ml/autobid/predict_success_proba`).
    *   **Error Rates:** HTTP 5xx errors, 4xx errors (especially 400 for bad input, 503 if model not loaded).
    *   **Traffic Volume:** Number of requests per minute/hour.
*   **Purpose:** Ensure the prediction service is responsive, available, and handling requests correctly.

### b. ML Model Performance (Live)

*   **Metrics:**
    *   **Actual Success Rate of ML-Approved Bids:** Track the real-world success rate of bids that were placed based on a positive ML model prediction.
    *   **Model Calibration:** How well do predicted probabilities align with actual outcomes? (e.g., for bids predicted with 0.7-0.8 probability, is the actual success rate around 70-80%?). Requires plotting calibration curves.
    *   **Comparison to Offline Metrics:** Regularly compare live performance metrics (ROC AUC, Precision, Recall, F1 on new labeled data) against metrics from the model's training/test set (`evaluation_metrics.json`).
    *   **Key Business Metrics Impact:** (If applicable) e.g., total value of successful bids influenced by the model.
*   **Purpose:** Directly measure if the model is performing as expected on live data and delivering business value.

### c. Data Drift (Input Features)

*   **Metrics/Techniques:**
    *   **Feature Distributions:** Track statistical properties (mean, median, variance, min, max for numerical; frequency of categories for categorical) of input features to the prediction endpoint. Compare current distributions to a baseline (e.g., training set distribution).
    *   **Statistical Tests:**
        *   Kolmogorov-Smirnov (KS) test for numerical features.
        *   Chi-Squared test for categorical features.
    *   **Missing Values:** Percentage of missing values for each feature.
    *   **Out-of-Range Values:** Number of values falling outside expected ranges.
    *   **Embedding Drift (for text features):** Monitor changes in the distribution of text embeddings (e.g., distance metrics between centroids of new vs. reference embeddings, or using a domain classifier).
*   **Purpose:** Detect if the statistical properties of incoming data for predictions are significantly different from the data the model was trained on. Data drift is a leading indicator of potential model performance degradation.

### d. Concept Drift (Model Decay Indicators)

*   **Metrics/Techniques:**
    *   **Model Prediction Score Distribution:** Track the distribution of the `success_probability` output by the model. Significant shifts can indicate that the relationship between features and the target has changed.
    *   **Performance on Recent Data:** If labels are available with some delay, continuously evaluate model performance (e.g., ROC AUC) on the most recent data subset. A consistent drop indicates potential concept drift.
    *   **Drift Detection Algorithms:** Employ algorithms like DDM (Drift Detection Method) or ADWIN (Adaptive Windowing) that monitor a model's error rate or other performance metrics to signal a drift.
*   **Purpose:** Detect if the underlying relationship between input features and the bid success outcome has changed since the model was trained.

### e. Retraining Pipeline Health

*   **Metrics:**
    *   **Job Status:** Success/failure of scheduled jobs (`assemble_data_job`, `train_model_job`).
    *   **Job Duration:** Time taken for each job to complete; significant increases can indicate issues.
    *   **Offline Metrics Over Time:** Track ROC AUC, F1, etc., from `evaluation_metrics.json` for each retrained model version. A consistent decline despite retraining might signal fundamental issues.
    *   **Data Volume Processed:** Number of records in the assembled dataset.
    *   **Model Reload Status:** Success/failure of the model reload trigger.
*   **Purpose:** Ensure the automated retraining pipeline is functioning correctly and producing quality models.

### f. Feature Storage & Generation Freshness/Coverage (If Applicable)

*   **Metrics (More relevant if a dedicated Feature Store is used, or for pre-computed stats like `ProfileHistoricalStats`):**
    *   **Freshness:** How up-to-date are the pre-computed features (e.g., `ProfileHistoricalStats.last_updated_at`)?
    *   **Coverage:** Percentage of profiles/jobs for which pre-computed features are available.
    *   **Staleness of `ProfileHistoricalStats`:** As already implemented, the services using these stats check `last_updated_at` and use defaults if too old. The frequency of this fallback should be monitored.
*   **Purpose:** Ensure that features used for prediction are timely and comprehensive.

## 3. Proposed Tools & Techniques

### a. Structured Logging + Log Aggregation (ELK Stack / Grafana Loki)

*   **Structured Logging:** Ensure all application components (FastAPI app, scheduler, ML scripts) produce logs in a structured format (e.g., JSON). This is already partially done with custom log messages. Standardizing further would be beneficial.
*   **Log Aggregation:**
    *   **ELK Stack (Elasticsearch, Logstash, Kibana):** Powerful for collecting, parsing, storing, and visualizing logs. Kibana allows for creating dashboards and alerts based on log queries.
    *   **Grafana Loki:** A horizontally scalable, highly available, multi-tenant log aggregation system inspired by Prometheus. Integrates well with Grafana for visualization.
*   **Use Case:** Centralize logs for debugging, manual inspection, and as a data source for some monitoring dashboards (e.g., error rates, specific event occurrences).

### b. Metrics Collection (Prometheus)

*   **Description:** An open-source systems monitoring and alerting toolkit. Applications expose metrics via an HTTP endpoint, and Prometheus scrapes these metrics at regular intervals.
*   **Instrumentation:** The FastAPI application (prediction endpoint, reload endpoint) and potentially the scheduler/ML scripts would need to be instrumented to expose relevant metrics (e.g., request counts, latencies, error counts, prediction score summaries, job success/failure counts). Libraries like `prometheus-fastapi-instrumentator` and `prometheus-client` for custom metrics.
*   **Use Case:** Time-series database for metrics, powerful querying with PromQL, and foundation for alerting.

### c. Visualization & Dashboards (Grafana)

*   **Description:** An open-source platform for monitoring and observability, widely used for visualizing time-series data from Prometheus, Loki, Elasticsearch, and other sources.
*   **Use Case:** Create dashboards to visualize:
    *   Prediction service health (latency, errors, RPS).
    *   Model prediction score distributions over time.
    *   Retraining pipeline health (job success, duration).
    *   Key data drift indicators (if basic metrics are exposed to Prometheus).

### d. ML Monitoring Libraries (Evidently AI / NannyML / WhyLogs)

*   **Description:** Specialized open-source libraries for detecting data drift, concept drift, and monitoring ML model performance.
    *   **Evidently AI:** Generates interactive reports and dashboards on model performance, data drift, and target drift. Can compare different datasets (e.g., reference training data vs. current production data).
    *   **NannyML:** Focuses on estimating model performance in the absence of ground truth and detecting silent model failures.
    *   **WhyLogs/WhyLabs:** Data logging and profiling platform that can help detect data drift and anomalies.
*   **Integration:** These libraries typically work by analyzing Pandas DataFrames.
    *   For **data drift on input features**: Periodically sample prediction requests (features only) from the live endpoint, save them, and run these tools to compare against a reference dataset (e.g., the training dataset).
    *   For **model performance/concept drift**: Periodically collect prediction scores *and* actual outcomes (once available), then run these tools.
*   **Use Case:** Automate the calculation of drift metrics and generation of detailed reports, providing deeper insights than generic metrics tools alone.

### e. Alerting Systems (Prometheus Alertmanager / Grafana Alerting)

*   **Description:**
    *   **Alertmanager:** Handles alerts sent by client applications such as the Prometheus server. It takes care of deduplicating, grouping, and routing them to the correct receiver integration (email, Slack, PagerDuty).
    *   **Grafana Alerting:** Allows creating and managing alerts directly within Grafana based on dashboard queries.
*   **Use Case:** Configure alerts for critical conditions identified during monitoring (e.g., error rate spikes, model performance degradation, significant drift detected, retraining pipeline failures).

## 4. Workflow Sketch

```
+---------------------+     +---------------------+     +-------------------+     +--------------------+
| App & ML Scripts    | --> | Metrics/Logs Emitters| --> | Collection Layer  | --> | Storage Layer      |
| (FastAPI, Scheduler,|     | (Prometheus client, |     | (Prometheus Scraper|     | (Prometheus TSDB,  |
|  Python Scripts)    |     |  Logging Libs)      |     |  Loki/Fluentd)    |     |  Elasticsearch/Loki|
+---------------------+     +---------------------+     +-------------------+     +--------------------+
                                                                  ^      |                |
                                                                  |      |                v
                                                      +-----------+      |  +-----------------------+
                                                      | Data for Drift   |  | Visualization/Analysis|
                                                      | Analysis         |  | (Grafana, Kibana,     |
                                                      +-----------+      |  |  Evidently AI Reports)|
                                                                  |      |  +-----------------------+
                                                                  v      |                ^
                                                      +-------------------+               |
                                                      | ML Monitoring Libs|               |
                                                      | (Evidently/NannyML|               |
                                                      |  /WhyLogs)        |---------------+
                                                      +-------------------+
                                                                  | Alerting Rules
                                                                  v
                                                      +-------------------+
                                                      | Alerting System   |
                                                      | (Alertmanager/    |
                                                      |  Grafana Alerts)  |
                                                      +-------------------+
                                                                  |
                                                                  v
                                                      +-------------------+
                                                      | Notifications     |
                                                      | (Email, Slack)    |
                                                      +-------------------+
                                                                  |
                                                                  v
                                                      +-------------------+
                                                      | Human Review &    |
                                                      | Action (Feedback) |
                                                      +-------------------+
```

## 5. Initial Implementation Focus

Given the current state, a phased approach to implementing advanced monitoring is recommended:

1.  **Phase 1 (Foundation - Partially Done):**
    *   **Solidify Structured Logging:** Ensure consistent structured logging (e.g., JSON format) across all components (`ml_predictions_api.py`, `autobidder_service.py`, `scheduler_setup.py`, ML scripts).
    *   **Centralized Log Aggregation:** Set up a basic log aggregation system (e.g., Loki with Grafana, or a managed cloud service) to collect and search logs.
    *   **Manual Log Review & Scripted Analysis:** Continue with and enhance the manual/semi-automated procedures outlined in `05_Monitoring_And_Drift_Detection.md` using the aggregated logs.

2.  **Phase 2 (Basic Metrics & Dashboards):**
    *   **Instrument FastAPI Endpoints:** Use `prometheus-fastapi-instrumentator` or similar to expose basic metrics (request count, latency, error rates) for prediction and model reload endpoints.
    *   **Prometheus & Grafana Setup:** Deploy Prometheus to scrape these metrics and Grafana to create initial dashboards for service health and prediction score distributions.
    *   **Scheduler Job Metrics:** Expose metrics from `scheduler_setup.py` (job success/failure, duration) to Prometheus using the `prometheus-client`.

3.  **Phase 3 (Dedicated ML Monitoring - Initial Steps):**
    *   **Data Sampling:** Implement a mechanism to sample prediction requests (features) and, if possible, predictions linked with eventual outcomes.
    *   **Offline Drift Analysis:** Use a library like Evidently AI to periodically generate reports comparing current data samples against a reference training dataset to detect data drift and basic model performance degradation. This can be a scheduled script.

4.  **Phase 4 (Automated Alerting):**
    *   Based on metrics in Prometheus/Grafana and reports from ML monitoring libraries, set up initial alerts for critical issues (e.g., high error rates, job failures, significant offline performance drops, severe data drift).

This phased approach allows for incremental value and manages complexity, building towards a comprehensive monitoring solution.I have already created `app/ml_model/docs/.gitkeep` (which ensures the directory exists) in a previous subtask.

Now I will proceed with creating the content for the first specified markdown file: `app/ml_model/docs/06_Advanced_Monitoring_Setup.md`.
The content for this file was provided in the prompt for this turn.
