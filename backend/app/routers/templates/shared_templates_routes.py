from fastapi import APIRouter, HTTPException, Request, Depends, Body
# Dict might be removable if Template.value becomes specific
from typing import List, Dict
import os
import json
from app.auth.jwt import get_current_user
from app.schemas.template import Template  # Import the new Template schema
from app.schemas.auth import MessageResponse  # Import for status messages

router = APIRouter()
# Defines the storage file for templates
TEMPLATES_FILE = "shared_templates.json"

# 📄 Получение всех шаблонов (Get all templates)


@router.get("/shared-templates", response_model=List[Template])
def list_templates(request: Request, user_id: str = Depends(get_current_user)):
    # Role check for potential filtering
    role = request.headers.get("x-user-role", "user")

    if not os.path.exists(TEMPLATES_FILE):
        return []  # Return empty list if file doesn't exist

    with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
        all_templates_data = json.load(f)

    # Ensure data is a list
    if not isinstance(all_templates_data, list):
        # Or handle error appropriately, e.g., log and return empty list
        raise HTTPException(
            status_code=500,
            detail="Invalid template data format."
        )

    if role == "superadmin":
        # Validate each item against Template schema
        return [Template(**t) for t in all_templates_data]
    else:
        # Filter templates by owner_id and validate
        user_templates = [
            Template(
                **t) for t in all_templates_data if t.get("owner_id") == user_id]
        return user_templates

# 💾 Сохранение шаблона (Save template)


@router.post("/templates", response_model=MessageResponse)
def save_template(
        template: Template,
        user_id: str = Depends(get_current_user)):
    if not os.path.exists(TEMPLATES_FILE):
        all_templates_data = []
    else:
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            try:
                all_templates_data = json.load(f)
                if not isinstance(all_templates_data, list):
                    all_templates_data = []  # Reset if format is incorrect
            except json.JSONDecodeError:
                all_templates_data = []  # Reset if file is corrupted

    # Ensure owner_id is set from the authenticated user
    template_dict = template.model_dump()  # Pydantic V2
    template_dict["owner_id"] = user_id

    # Remove any existing template with the same name by the same owner
    all_templates_data = [t for t in all_templates_data if not (
        t.get("name") == template.name and t.get("owner_id") == user_id)]
    all_templates_data.append(template_dict)

    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(all_templates_data, f, indent=2, ensure_ascii=False)

    return MessageResponse(message="saved")

# ♻️ Обновление шаблона (Update template)


@router.patch("/templates/{name}", response_model=MessageResponse)
def update_template(
        name: str,
        updated_value: Dict = Body(...),
        user_id: str = Depends(get_current_user)):
    if not os.path.exists(TEMPLATES_FILE):
        raise HTTPException(status_code=404,
                            detail="No templates found (file missing)")

    with open(TEMPLATES_FILE, "r+", encoding="utf-8") as f:
        try:
            all_templates_data = json.load(f)
            if not isinstance(all_templates_data, list):
                raise HTTPException(
                    status_code=500, detail="Invalid template data format."
                )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, detail="Corrupted template file."
            )

        found_and_updated = False
        for i, t_data in enumerate(all_templates_data):
            if t_data.get("name") == name and t_data.get(
                    "owner_id") == user_id:
                # Update the value field of the found template
                all_templates_data[i]["value"] = updated_value
                found_and_updated = True
                break

        if not found_and_updated:
            raise HTTPException(status_code=404,
                                detail="Template not found or not yours")

        # Go to the beginning of the file to overwrite
        f.seek(0)
        json.dump(all_templates_data, f, indent=2, ensure_ascii=False)
        f.truncate()  # Remove remaining part of old file if new data is shorter

    return MessageResponse(message="updated")

# ❌ Удаление шаблона (Delete template)


@router.delete("/templates/{name}", response_model=MessageResponse)
def delete_template(
        name: str,
        user_id: str = Depends(get_current_user),
        request: Request = None):
    role = request.headers.get("x-user-role", "user")

    if not os.path.exists(TEMPLATES_FILE):
        raise HTTPException(status_code=404,
                            detail="No templates found (file missing)")

    with open(TEMPLATES_FILE, "r+", encoding="utf-8") as f:
        try:
            all_templates_data = json.load(f)
            if not isinstance(all_templates_data, list):
                raise HTTPException(
                    status_code=500, detail="Invalid template data format."
                )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, detail="Corrupted template file."
            )

        original_len = len(all_templates_data)

        if role == "admin" or role == "superadmin":
            # Admin/Superadmin can delete any template by name
            all_templates_data_after_deletion = [
                t for t in all_templates_data if t.get("name") != name]
        else:
            # Regular user can only delete their own template by name
            all_templates_data_after_deletion = [
                t for t in all_templates_data
                if not (t.get("name") == name and t.get("owner_id") == user_id)
            ]

        if len(all_templates_data_after_deletion) == original_len:
            # This means no template was deleted, either because it wasn't found
            # or (for non-admins) it didn't belong to the user.
            raise HTTPException(
                status_code=404,
                detail="Template not found or permission denied"
            )

        # Go to the beginning of the file to overwrite
        f.seek(0)
        json.dump(all_templates_data_after_deletion,
                  f, indent=2, ensure_ascii=False)
        f.truncate()
        # Remove remaining part of old file if new data is
        # shorter

    return MessageResponse(message="deleted")
