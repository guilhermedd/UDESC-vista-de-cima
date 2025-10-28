import yaml

with open('data.yaml', 'r') as file:
    data = yaml.safe_load(file)
    
print(data.keys())

data.update({
    "image_3": {
        "score": 10,
        "attempts": 3
    },
    "image_4": {
        "score": 10,
        "attempts": 3
    }
})

with open('data.yaml', 'w') as file:
    yaml.dump(data, file)