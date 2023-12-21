import json
from lambda_function import lambda_handler

if __name__ == "__main__":
    event = {
        "namespace": "creative-diffusion-playground",
        "scaledobject_name": "lama-job",
        "new_min_replica": "0",  # Set the replica count you want
        "action": "get_minreplica", 
        "cluster": "dev"  # Set this to True if you want to check pod count
    }

    response = lambda_handler(event, None)
    print(json.dumps(response, indent=2))
