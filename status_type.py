import json

class StatusType:
    """Represents a status type from Super Auto Pets"""

    def __init__(self, food_json: dict | str):
        """Initializes a status type from a JSON dictionary (or string) representing it."""
        if isinstance(food_json, str):
            food_json = json.loads(food_json)
        self.name = food_json['name']
        self.id = food_json['id']
        self.image_data = food_json['image']
        self.ability = food_json['ability']
        
    def __str__(self):
        """Returns a string representation of the status type."""
        return self.name
