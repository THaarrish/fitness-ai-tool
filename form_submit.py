from db import personal_data_collection, notes_collection
from datetime import datetime, timezone
def update_personal_info1(existing, update_type,**kwargs ):
    if update_type== "goals":
        existing["goals"]= kwargs.get("goals", [])
        update_field= {"goals": existing["goals"]}
    else:
        existing[update_type]= kwargs
        update_field= {update_type: existing[update_type]}

    personal_data_collection.update_one({"_id": existing["_id"]}, {"$set": update_field})
    return existing


def update_personal_info(profile, field_name, **kwargs):
    # 1. Update the local session state dictionary first
    if not profile or not isinstance(profile, dict):
        profile = {}

    profile[field_name] = kwargs

    # 2. Package EVERYTHING together into a fresh document
    new_customer_document = {
        "general": profile.get("general", {}),
        "goals": profile.get("goals", []),
        "nutrition": profile.get("nutrition", {})
    }

    # 3. Force MongoDB to create a completely new record with a new ID
    personal_data_collection.insert_one(new_customer_document)

    # 4. Return it back to your Streamlit state
    return profile
def add_note(note, profile_id):

    new_note={"user_id": profile_id,"text": note, "$vectorize": note, "metadata":{"injested": datetime.now(timezone.utc)}}
    new_note["timestamp"] = datetime.now(timezone.utc)
    result= notes_collection.insert_one(new_note)
    new_note["_id"]= result.inserted_id
    return new_note

def delete_note(_id):
    return  notes_collection.delete_one({"_id": _id})