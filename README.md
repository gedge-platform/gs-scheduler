# GE-Global Scheduler 4.0

## For Multiple Edge Clusters and Cloud Cluster

- Can Apply yaml for 3L Clusters (Edge Cluster / Near Edge Cluster / Cloud Cluster)  
- Updated Center Management Cluster

## Add Gedge Configmap for platform services 

- name is gedge-system-scheduler-configmap.yaml 
- platform service server ip
- platform service port

## Updated GEdge-Scheduler Main Core  

- Add New Platform info POD at Center Management Cluster
- Update kafka message module code
- Add New topic for processing Rest API for resources of multiple cluster    
- Changed to Run Front Server POD and GEdge Scheduler Policy PODs All at Once

![gedge_scheduler_system](./assets/gedge_scheduler_system.png)


## Updated GEdge-Scheduler Source Code for Multiple Users and Workspace, Project 

- Add Newly Multiple Users
  * Admin User/Normal User
  * login management 
- Workspace is created from Cluster Set ( User Selected Clusters)
- User applitions is seperated by project    

![user_workspace_project](./assets/user_workspace_project.png)

## Update Version clusters for Developing System  
- Set K8S version 1.22.x
- Support contaioner runtime are docker,containerd

![testing_system](./assets/testing_system.png)

## Add New GEdge Schedluer Policy 

- (G)MostRequestedPriority for 3LT 
- (G)LowLatencyPriority for 3LT
- GSetClusters for 3LT
- GSelectCluster for 3LT

## Get Start
- Clone the repository
  https://github.com/gedge-platform/gs-scheduler.git
- MongDB
  kubectl create -f mongo-statefulset.yaml
  kubectl create -f headless-service.yaml
  kubectl expose pod gedge-mongo-0 --port 27017 --target-port 27017 --type LoadBalancer -n gedge-system-scheduler

- Redis 
  kubectl apply -k .
  kubectl apply -f redis_service_LoadBalancer.yaml

- MetalLB
  kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.10.2/manifests/namespace.yaml
  kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.10.2/manifests/metallb.yaml
  kubectl apply -f metallb_configmap.yaml

- Kafka
  kubectl apply -f kafka.yaml
  kubectl edit deployment gedge-kafka-server -n gedge-system-scheduler
  Add env 
    - name: KAFKA_HOSTNAME
      value: xxx.xxx.xxx.xxx (host ip)
- Run Front Server
  kubectl apply -f rbac_custom_sch_front_server.yaml
- Run Cluster Agent
  kubectl apply -f rbac_custom_sch_cagent.yaml
  
  
