from typing import Dict, Any, List
from ..schemas.version import EventDiff

def generate_diff(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[EventDiff]:
    """
    Generate a diff between two versions of event data
    """
    changes = []
    
    # Find all keys in either dictionary
    all_keys = set(old_data.keys()) | set(new_data.keys())
    
    for key in all_keys:
        # Key exists in both dictionaries but values differ
        if key in old_data and key in new_data and old_data[key] != new_data[key]:
            changes.append(EventDiff(
                field=key,
                old_value=old_data[key],
                new_value=new_data[key]
            ))
        # Key exists only in old data (was removed)
        elif key in old_data and key not in new_data:
            changes.append(EventDiff(
                field=key,
                old_value=old_data[key],
                new_value=None
            ))
        # Key exists only in new data (was added)
        elif key not in old_data and key in new_data:
            changes.append(EventDiff(
                field=key,
                old_value=None,
                new_value=new_data[key]
            ))
    
    return changes