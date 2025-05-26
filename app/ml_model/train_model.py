import os
import logging
import argparse
import json
import pandas as pd
import numpy as np
import xgboost as xgb # Using xgb directly for XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import joblib
from typing import Optional, Any
from pathlib import Path

# 1. Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

# 3. Load Dataset function
def load_dataset(file_path: str) -> Optional[pd.DataFrame]:
    """
    Loads data from Parquet or CSV based on file extension.
    Handles potential file not found errors.
    """
    path = Path(file_path)
    logging.info(f"Attempting to load dataset from: {path}")
    try:
        if path.suffix == ".parquet":
            df = pd.read_parquet(path)
        elif path.suffix == ".csv":
            df = pd.read_csv(path)
        else:
            logging.error(f"Unsupported file format: {path.suffix}. Please use .parquet or .csv.")
            return None
        logging.info(f"Dataset loaded successfully. Shape: {df.shape}")
        return df
    except FileNotFoundError:
        logging.error(f"Dataset file not found at: {path}")
        return None
    except Exception as e:
        logging.error(f"Error loading dataset from {path}: {e}", exc_info=True)
        return None

# 4. Train and Evaluate Model function
def train_evaluate_model(df: pd.DataFrame, model_output_dir: Path, model_params: dict) -> Optional[Any]:
    """
    Trains, evaluates a model, and saves artifacts.
    """
    logging.info("Starting model training and evaluation...")
    try:
        # Separate Features (X) and Target (y)
        if 'target_is_success' not in df.columns:
            logging.error("Target column 'target_is_success' not found in DataFrame.")
            return None
        
        y = df['target_is_success']
        
        # Columns to drop: target and any trace/ID columns
        cols_to_drop = ['target_is_success']
        # Check for trace columns and add them to cols_to_drop if they exist
        for col in ['bid_id_trace', 'profile_id_trace']:
            if col in df.columns:
                cols_to_drop.append(col)
        
        X = df.drop(columns=cols_to_drop)
        logging.info(f"Features (X) shape: {X.shape}, Target (y) shape: {y.shape}")

        # Train-Test Split
        logging.info("Performing train-test split...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        logging.info(f"Train set shape: {X_train.shape}, Test set shape: {X_test.shape}")

        # Initialize and Train Model
        logging.info(f"Initializing XGBClassifier with parameters: {model_params}")
        # Ensure use_label_encoder=False is not used for modern XGBoost if not needed
        # eval_metric is usually set during fit if early stopping is used.
        model = xgb.XGBClassifier(**model_params, random_state=42)
        
        logging.info("Training the model...")
        model.fit(X_train, y_train)
        logging.info("Model training completed.")

        # Make Predictions
        logging.info("Making predictions on the test set...")
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred_binary = model.predict(X_test)

        # Evaluate Model
        logging.info("Evaluating the model...")
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        precision = precision_score(y_test, y_pred_binary, zero_division=0)
        recall = recall_score(y_test, y_pred_binary, zero_division=0)
        f1 = f1_score(y_test, y_pred_binary, zero_division=0)
        conf_matrix = confusion_matrix(y_test, y_pred_binary)
        class_report = classification_report(y_test, y_pred_binary, zero_division=0)

        metrics = {
            "roc_auc_score": roc_auc,
            "precision_score": precision,
            "recall_score": recall,
            "f1_score": f1,
            "confusion_matrix": conf_matrix.tolist(), # Convert numpy array to list for JSON
            "classification_report": class_report
        }
        logging.info(f"Evaluation Metrics:\nROC AUC: {roc_auc:.4f}\nPrecision: {precision:.4f}\nRecall: {recall:.4f}\nF1 Score: {f1:.4f}")
        logging.info(f"Classification Report:\n{class_report}")
        logging.info(f"Confusion Matrix:\n{conf_matrix}")

        # Save metrics
        metrics_path = model_output_dir / "evaluation_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=4)
        logging.info(f"Evaluation metrics saved to: {metrics_path}")

        # Feature Importance
        logging.info("Extracting feature importances...")
        try:
            importances = model.feature_importances_
            feature_names = X.columns
            feature_importance_df = pd.DataFrame({'feature': feature_names, 'importance': importances})
            feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)
            
            logging.info(f"Top 10 Features:\n{feature_importance_df.head(10)}")
            
            importance_path = model_output_dir / "feature_importances.csv"
            feature_importance_df.to_csv(importance_path, index=False)
            logging.info(f"Feature importances saved to: {importance_path}")
        except Exception as e:
            logging.error(f"Could not extract or save feature importances: {e}", exc_info=True)
            
        return model

    except Exception as e:
        logging.error(f"An error occurred during model training or evaluation: {e}", exc_info=True)
        return None

# 5. Main function
def main():
    """
    Main function to orchestrate model training.
    """
    # Argument Parser
    parser = argparse.ArgumentParser(description="Train an ML model on the assembled dataset.")
    parser.add_argument(
        "--input_path",
        type=str,
        required=True,
        help="Path to the input dataset file (e.g., data/training_dataset.parquet)"
    )
    parser.add_argument(
        "--model_output_dir",
        type=str,
        required=True,
        help="Directory to save the trained model and evaluation results (e.g., app/ml_model/artifacts/)"
    )
    # XGBoost specific hyperparameters
    parser.add_argument("--n_estimators", type=int, default=100, help="Number of gradient boosted trees. Equivalent to number of boosting rounds.")
    parser.add_argument("--learning_rate", type=float, default=0.1, help="Boosting learning rate (xgb's 'eta')")
    parser.add_argument("--max_depth", type=int, default=3, help="Maximum depth of a tree.")
    parser.add_argument("--subsample", type=float, default=1.0, help="Subsample ratio of the training instance.")
    parser.add_argument("--colsample_bytree", type=float, default=1.0, help="Subsample ratio of columns when constructing each tree.")
    parser.add_argument("--objective", type=str, default="binary:logistic", help="Specify the learning task and the corresponding learning objective.")
    # Add use_label_encoder=False and eval_metric='logloss' as fixed if that's standard practice, or allow via args
    
    args = parser.parse_args()
    
    model_output_path = Path(args.model_output_dir)
    
    # Ensure model_output_dir exists
    logging.info(f"Ensuring model output directory exists: {model_output_path}")
    model_output_path.mkdir(parents=True, exist_ok=True)

    # Load dataset
    df = load_dataset(args.input_path)
    if df is None:
        logging.error("Failed to load dataset. Exiting.")
        return

    # Prepare model parameters
    # For XGBoost, use_label_encoder=False is often recommended with newer versions
    # when labels are already 0/1. eval_metric='logloss' is common for binary classification.
    model_params = {
        "n_estimators": args.n_estimators,
        "learning_rate": args.learning_rate,
        "max_depth": args.max_depth,
        "subsample": args.subsample,
        "colsample_bytree": args.colsample_bytree,
        "objective": args.objective,
        # For XGBoost versions >= 1.6.0, 'use_label_encoder' is deprecated and defaults to False when input is numeric.
        # If older XGBoost or string labels, this might be needed.
        # 'use_label_encoder': False, # if labels are already encoded
        # 'eval_metric': 'logloss' # Can be passed to fit for early stopping, or used as default for classifier
    }
    # For XGBClassifier, some params like 'eval_metric' can be passed directly to constructor
    # if not using them in fit() for early stopping.
    # If using early stopping: model.fit(X_train, y_train, eval_set=[(X_test, y_test)], early_stopping_rounds=10)
    # and eval_metric would be specified there.

    # Train and evaluate model
    trained_model = train_evaluate_model(df, model_output_path, model_params)

    if trained_model:
        # Model Serialization
        model_save_path = model_output_path / "model.joblib"
        logging.info(f"Serializing trained model to: {model_save_path}")
        try:
            joblib.dump(trained_model, model_save_path)
            logging.info(f"Model serialized and saved successfully to {model_save_path}")
        except Exception as e:
            logging.error(f"Error serializing model: {e}", exc_info=True)
    else:
        logging.error("Model training failed. Model not saved.")

    logging.info("Model training script finished.")

if __name__ == "__main__":
    main()
