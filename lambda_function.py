import json
import os
from kubernetes import client, config



def get_scaledobject_minreplica(namespace, scaledobject_name, kubeconfig_path):
    config.load_kube_config(config_file=kubeconfig_path)

    api_instance = client.CustomObjectsApi()

    try:
        scaledobject = api_instance.get_namespaced_custom_object(
            group="keda.sh", version="v1alpha1", namespace=namespace, plural="scaledobjects", name=scaledobject_name)
        
        min_replica = scaledobject.get('spec', {}).get('minReplicaCount')

        return f"ScaledObject '{scaledobject_name}' has minReplicaCount: {min_replica}"
    except Exception as e:
        return f"Error retrieving ScaledObject minReplicaCount: {str(e)}"

def scale_scaledobject(namespace, scaledobject_name, new_min_replica, kubeconfig_path):
    config.load_kube_config(config_file=kubeconfig_path)

    api_instance = client.CustomObjectsApi()

    try:
        scaledobject = api_instance.get_namespaced_custom_object(
            group="keda.sh", version="v1alpha1", namespace=namespace, plural="scaledobjects", name=scaledobject_name)
        
        scaledobject['spec']['minReplicaCount'] = new_min_replica

        api_instance.replace_namespaced_custom_object(
            group="keda.sh", version="v1alpha1", namespace=namespace, plural="scaledobjects", name=scaledobject_name, body=scaledobject)

        return f"ScaledObject '{scaledobject_name}' minReplicaCount updated to {new_min_replica}"
    except Exception as e:
        return f"Error updating ScaledObject minReplicaCount: {str(e)}"

def lambda_handler(event, context):
    try:
        namespace = event['namespace']
        scaledobject_name = event['scaledobject_name']
        action = event.get('action')
        new_min_replica = int(event.get('new_min_replica', 0))
        cluster_env = event['cluster']

        if cluster_env == 'dev':
            kubeconfig_path = 'kubeconfig_dev.yaml'
        else:
            kubeconfig_path = 'kubeconfig_stage.yaml'
        
        if action == 'get_minreplica':
            result = get_scaledobject_minreplica(namespace, scaledobject_name, kubeconfig_path)
        elif action == 'update_minreplica':
            result = scale_scaledobject(namespace, scaledobject_name, new_min_replica, kubeconfig_path)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps("Invalid action. Supported actions are 'get_minreplica' and 'update_minreplica'.")
            }

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except ValueError:
        return {
            'statusCode': 400,
            'body': json.dumps("Invalid input. Please provide valid input values.")
        }
