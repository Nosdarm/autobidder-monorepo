import json
import logging
from typing import List, Optional, Dict, Any
from sklearn.preprocessing import MultiLabelBinarizer

# Assuming 'app' is in PYTHONPATH and models are structured as app.models.<model_name>
try:
    from app.models.profile import Profile
except ImportError:
    logging.warning("Could not import Profile model directly from app.models. Ensure PYTHONPATH is set correctly or app is installed.")
    # Define dummy class for type hinting if Profile model can't be imported
    class Profile:
        skills: Optional[Any] = None
        experience_level: Optional[str] = None
        profile_type: Optional[str] = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Skill Featurization ---
SKILL_VOCABULARY: List[str] = [
    "python", "javascript", "sql", "fastapi", "react",
    "data_analysis", "project_management", "html", "css",
    "docker", "kubernetes", "aws", "gcp", "azure", "machine_learning"
]
# Initialize MultiLabelBinarizer
# Using fit_transform directly on the current batch of skills,
# but ensuring the binarizer is aware of all classes for consistent output shape.
mlb = MultiLabelBinarizer(classes=SKILL_VOCABULARY)
# Fit with an empty list of lists to ensure all classes are known to the binarizer
# This ensures that transform calls will produce vectors of the correct length,
# even if some skills in SKILL_VOCABULARY are not present in a particular input.
mlb.fit([[]])


def featurize_skills(skills_input: Optional[Any]) -> List[int]:
    """
    Featurizes a list of skills into a multi-hot encoded vector.

    Args:
        skills_input: Raw value from Profile.skills. Expected to be a list of strings,
                      or a JSON string representing a list of strings.

    Returns:
        A list of integers representing the multi-hot encoded skill vector.
        Returns a vector of zeros if skills_input is None, invalid, or empty.
    """
    parsed_skills: List[str] = []
    if skills_input is None:
        logging.debug("Skills input is None.")
    elif isinstance(skills_input, str):
        try:
            loaded_skills = json.loads(skills_input)
            if isinstance(loaded_skills, list):
                parsed_skills = [str(skill).lower() for skill in loaded_skills if isinstance(skill, str)]
            else:
                logging.warning(f"Parsed JSON skills is not a list: {type(loaded_skills)}")
        except json.JSONDecodeError:
            logging.warning(f"Failed to parse skills JSON string: {skills_input}")
    elif isinstance(skills_input, list):
        parsed_skills = [str(skill).lower() for skill in skills_input if isinstance(skill, str)]
    else:
        logging.warning(f"Unexpected type for skills_input: {type(skills_input)}")

    if not parsed_skills:
        return [0] * len(SKILL_VOCABULARY)

    # Transform the skills. mlb expects a list of iterables (e.g., list of lists of skills)
    try:
        # Ensure mlb is fitted if not already (e.g. if SKILL_VOCABULARY changed dynamically, though it's static here)
        # For static vocabulary, fitting once at module load is sufficient.
        # The .fit([[]]) above handles this.
        transformed_skills = mlb.transform([parsed_skills])
        return transformed_skills[0].tolist()
    except Exception as e:
        logging.error(f"Error transforming skills with MultiLabelBinarizer: {e}. Skills: {parsed_skills}")
        return [0] * len(SKILL_VOCABULARY)


# --- Experience Level Featurization ---
EXPERIENCE_MAP: Dict[Optional[str], int] = {
    "entry": 0,
    "intermediate": 1,
    "expert": 2,
    None: -1  # Default for missing or None values
}

def featurize_experience_level(level: Optional[str]) -> int:
    """
    Converts an experience level string to a numerical representation.

    Args:
        level: String from Profile.experience_level (e.g., "entry", "intermediate", "expert").

    Returns:
        An integer representing the experience level.
    """
    return EXPERIENCE_MAP.get(level.lower() if level else None, -1)


# --- Profile Type Featurization ---
PROFILE_TYPE_MAP: Dict[Optional[str], int] = {
    "personal": 0,
    "agency": 1,
    None: -1 # Default for missing or None values
}

def featurize_profile_type(profile_type: Optional[str]) -> int:
    """
    Converts a profile type string to a numerical representation.

    Args:
        profile_type: String from Profile.profile_type (e.g., "personal", "agency").

    Returns:
        An integer representing the profile type.
    """
    return PROFILE_TYPE_MAP.get(profile_type.lower() if profile_type else None, -1)


# --- Main Profile Featurization Function (Optional) ---
def generate_profile_features(profile: Profile) -> Dict[str, Any]:
    """
    Generates a dictionary of features for a given Profile object.

    Args:
        profile: A Profile object.

    Returns:
        A dictionary containing featurized profile data.
    """
    if not isinstance(profile, Profile): # Check if it's the actual model or dummy
        logging.warning("generate_profile_features received an object that is not a Profile instance.")
        # Handle gracefully, perhaps return default/empty features
        return {
            "skill_features": [0] * len(SKILL_VOCABULARY),
            "experience_level": -1,
            "profile_type": -1,
        }

    skill_features = featurize_skills(profile.skills)
    exp_level_feature = featurize_experience_level(profile.experience_level)
    type_feature = featurize_profile_type(profile.profile_type)

    return {
        "skill_features": skill_features,
        "experience_level": exp_level_feature,
        "profile_type": type_feature,
    }
