import os
import openai
import logging
from typing import List, Optional

# Assuming 'app' is in PYTHONPATH and models are structured as app.models.<model_name>
try:
    from app.models.job import Job
    from app.models.bid import Bid
except ImportError:
    # This is a fallback or could indicate a path issue if 'app' is not configured in PYTHONPATH
    # For now, we'll assume the primary imports work in the target environment.
    # If running this module standalone for testing, PYTHONPATH might need adjustment.
    logging.warning("Could not import Job/Bid models directly from app.models. Ensure PYTHONPATH is set correctly or app is installed.")
    # Define dummy classes for type hinting if models can't be imported, to allow module to load for basic tests.
    # This is not ideal for production but helps in isolated development/testing.
    class Job:
        description: Optional[str] = None
    class Bid:
        generated_bid_text: Optional[str] = None


# Initialize OpenAI Client
# The client automatically picks up OPENAI_API_KEY from environment variables.
# If OPENAI_API_KEY is not set, openai.OpenAI() will raise openai.AuthenticationError
# This should be handled by the application ensuring the key is set.
try:
    client = openai.OpenAI()
except openai.AuthenticationError as e:
    logging.error(f"OpenAI API key not found or invalid. Please set the OPENAI_API_KEY environment variable. Error: {e}")
    client = None # Ensure client is None if initialization fails
except Exception as e:
    logging.error(f"An unexpected error occurred during OpenAI client initialization: {e}")
    client = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_text_embedding(text: str, model_name: str = "text-embedding-ada-002") -> Optional[List[float]]:
    """
    Generates an embedding for the given text using the specified OpenAI model.

    Args:
        text: The input text to embed.
        model_name: The name of the OpenAI embedding model to use.

    Returns:
        A list of floats representing the embedding, or None if an error occurs
        or the input is invalid.
    """
    if not client:
        logging.error("OpenAI client is not initialized. Cannot generate embeddings.")
        return None
        
    if not text or text.isspace():
        logging.warning("Input text is empty or whitespace-only. Cannot generate embedding.")
        return None

    try:
        response = client.embeddings.create(input=[text.strip()], model=model_name)
        if response.data and response.data[0].embedding:
            return response.data[0].embedding
        else:
            logging.error("Received an unexpected response structure from OpenAI API.")
            return None
    except openai.APIError as e:
        logging.error(f"OpenAI API error occurred: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while generating text embedding: {e}")
        return None

def generate_job_description_embedding(job: Job, model_name: str = "text-embedding-ada-002") -> Optional[List[float]]:
    """
    Generates an embedding for the description of a Job object.

    Args:
        job: A Job object containing the description.
        model_name: The name of the OpenAI embedding model to use.

    Returns:
        The embedding for the job description, or None if no description is available
        or an error occurs.
    """
    if not job or not job.description:
        logging.info("Job object is None or has no description. Cannot generate embedding.")
        return None
    return get_text_embedding(job.description, model_name)

def generate_bid_text_embedding(bid: Bid, model_name: str = "text-embedding-ada-002") -> Optional[List[float]]:
    """
    Generates an embedding for the generated_bid_text of a Bid object.

    Args:
        bid: A Bid object containing the generated bid text.
        model_name: The name of the OpenAI embedding model to use.

    Returns:
        The embedding for the bid text, or None if no text is available
        or an error occurs.
    """
    if not bid or not bid.generated_bid_text:
        logging.info("Bid object is None or has no generated_bid_text. Cannot generate embedding.")
        return None
    return get_text_embedding(bid.generated_bid_text, model_name)
