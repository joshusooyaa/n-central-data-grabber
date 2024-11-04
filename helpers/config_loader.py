import json

class ConfigLoader:
  def __init__(self):
    with open('config.json', 'r') as config:
      self.config = json.load(config)
  
  def __getitem__(self, var):
    return self.config.get(var, None)