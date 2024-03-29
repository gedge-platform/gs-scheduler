from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

try :
    config.load_incluster_config()
except:
    config.load_kube_config()
    
v1 = client.CoreV1Api()

def find_node_port_by_service_name(service_name):
    res_services = v1.list_service_for_all_namespaces(pretty=True)
    for i in res_services.items:
        #print(i.metadata.name)
        if i.metadata.name == service_name:
            print("service_name", service_name)
            for j in i.spec.ports:
                print("i.spec.ports",j)
                #if j.node_port:
                #    print("j.node_port", j.node_port)
                #    return j.node_port
                if j.port:
                    print("j.port", j.port)
                    return j.port
    return None

def find_external_ip_by_service_name(service_name):
    res_services = v1.list_service_for_all_namespaces(pretty=True)
    for i in res_services.items:
        if i.metadata.name == service_name:
            print("service_name", service_name)
            #print("i.status", i.status)
            if i.status.load_balancer.ingress[0].ip :
                print("external ip", i.status.load_balancer.ingress[0].ip)
                return i.status.load_balancer.ingress[0].ip
    return None

def get_hostname_by_namespaced_pod_name(namespace_name,pod_name):
    res_pods = v1.list_namespaced_pod(namespace = namespace_name)
    for i in res_pods.items:
        if i.metadata.name == pod_name:
            print("get_hostname_by_pod_name", i.status)
            if i.spec.node_name:
                print("get_hostname_by_pod_name :node_name= ", i.spec.node_name)
                return i.spec.node_name
    return None

def find_host_ip_by_pod_name(pod_name):
    res_pods = v1.list_pod_for_all_namespaces(pretty=True)
    for i in res_pods.items:
        if i.metadata.name == pod_name:
            if i.status.host_ip:
                return i.status.host_ip
    return None