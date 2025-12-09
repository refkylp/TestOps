# TestOps - Kubernetes Based Selenium Test Orchestration

## Project Structure

```
TestOps/
├── .github/workflows/    # CI pipeline definitions
├── docker/               # Dockerfiles for both pods
├── k8s/manifests/        # Kubernetes deployment files
├── TestFiles/            # Test suites and page objects
├── reports/              # Test execution reports
├── deploy.py             # Deployment helper script
└── docker-compose.test.yaml

```
## System Overview

TestOps is a distributed test automation system designed to run Selenium-based UI tests on Kubernetes. The architecture separates test execution logic from browser instances, allowing for scalable and maintainable test infrastructure.

The system consists of two main components:

**Test Controller Pod**: Contains the Python test suite, page objects, and configuration. This pod orchestrates test execution by connecting to remote browser instances rather than running browsers locally.

**Chrome Node Pod**: Runs Selenium Grid with headless Chrome browsers. Multiple instances can be deployed to support parallel test execution.


## How Test Collection and Execution Works

When a test run is initiated, the following sequence occurs:

1. The Test Controller Pod starts pytest, which discovers all test files under the `tests/` directory following standard pytest conventions.

2. The controller reads configuration from a Kubernetes ConfigMap, which includes the Selenium Grid endpoint URL and runtime parameters such as retry settings.

3. As each test requests a browser instance, `conftest.py` creates a Remote WebDriver connection instead of launching a local browser. The WebDriver URL points to the Chrome Node Service:

```
CHROME_NODE_SERVICE=http://chrome-node-service:4444
```

4. Selenium Grid running in the Chrome Node Pods receives the WebDriver request and provisions a headless Chrome session.

5. Test code executes in the controller pod while all browser operations happen remotely in the Chrome Node Pods.

6. When the test completes or fails, the browser session is terminated and resources are released back to the pool.


## Inter-Pod Communication

Communication between pods relies on Kubernetes DNS and Services.

**Service Discovery**: Chrome Node Pods are managed by a Deployment and expose their Selenium Grid instances through a ClusterIP Service named `chrome-node-service`. Kubernetes automatically registers this service in cluster DNS.

**Connection Flow**: The Test Controller Pod resolves `chrome-node-service` through Kubernetes DNS. All WebDriver traffic is routed through this service, which load balances requests across available Chrome Node replicas.

**Network Path**:
```
Test Controller Pod
       |
       v
chrome-node-service (ClusterIP, port 4444)
       |
       v
Chrome Node Pod(s) - Selenium Grid
```

The Chrome Node Service uses label selectors to identify which pods should receive traffic. Any pod with the matching label becomes part of the service backend automatically.


## Deploying the System

### Local Deployment with Docker Compose

For local development and testing, you can use the included Docker Compose file instead of setting up a full Kubernetes cluster.

**Prerequisites**:
- Docker and Docker Compose installed
- Sufficient system resources for running Chrome instances

**Steps**:

1. Clone the repository:
```bash
git clone https://github.com/refkylp/TestOps.git
cd TestOps
```

2. Start the environment:
```bash
docker-compose -f docker-compose.test.yaml up -d
```

3. Run tests against the local environment:
```bash
docker-compose -f docker-compose.test.yaml logs -f test-controller
```

4. Stop the environment when finished:
```bash
docker-compose -f docker-compose.test.yaml down
```

Docker Compose provides a simpler alternative to Kubernetes for local development. The same test code works in both environments since the Remote WebDriver connection logic remains identical.


### AWS EKS Deployment

For production or CI/CD environments, deploy to an EKS cluster.

**Prerequisites**:
- AWS CLI configured with appropriate credentials
- Docker and docker-compose installed
- kubectl installed and configured
- eksctl installed (optional but recommended)
- ECR repositories for container images (created automatically by CI pipeline)

**Step 1: Configure kubectl**

Create EKS cluster with awscli commands;

```bash
eksctl create cluster \
  --name test-automation \
  --region us-east-1 \ 
  --version 1.33 \
  --zones us-east-1a,us-east-1b \
  --node-type t3a.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 3 \
  --with-oidc \
  --managed
```

Retrieve the kubeconfig for your EKS cluster:
```bash
aws eks update-kubeconfig \
  --region us-east-1 \
  --name your-cluster-name
```

Verify connectivity:
```bash
kubectl get nodes
```

**Step 2: Clone the Repository**

```bash
git clone https://github.com/refkylp/TestOps.git
cd TestOps
```

If the CI pipeline has run, the Kubernetes manifests in `k8s/manifests/` will already contain the correct ECR image URIs.

**Step 3: Deploy with the Helper Script**

The repository includes `deploy.py` which handles the deployment sequence:
```bash
python3 deploy.py
```

This script performs the following operations:
- Creates or updates the namespace
- Applies the ConfigMap with test settings
- Deploys Chrome Node Pods and Service
- Waits for Chrome Nodes to become ready
- Deploys the Test Controller Pod

**Step 4: Verify Deployment**

Check that all pods are running:
```bash
kubectl get pods -n test-automation
kubectl get svc -n test-automation
```

View test execution logs:
```bash
kubectl logs -f -l component=test-controller -n test-automation
```


## Manual Kubernetes Deployment

If you prefer to apply manifests manually rather than using the deployment script:

```bash
kubectl apply -f k8s/manifests/01-namespace.yaml
kubectl apply -f k8s/manifests/02-configmap.yaml
kubectl apply -f k8s/manifests/03-chrome-node-deployment.yaml
kubectl apply -f k8s/manifests/04-chrome-node-service.yaml
kubectl apply -f k8s/manifests/05-test-controller-deployment.yaml
```

Wait for Chrome Nodes before deploying the controller to ensure the Selenium Grid is available when tests start.


## Configuration

Test behavior is controlled through the ConfigMap defined in the Kubernetes manifests. Key settings include:

| Parameter | Description |
|-----------|-------------|
| CHROME_NODE_SERVICE | URL of the Selenium Grid endpoint |
| NODE_COUNT | Number of Chrome Node replicas |
| MAX_RETRIES | Retry attempts for Selenium connection |
| RETRY_DELAY | Delay between retry attempts |


## CI Pipeline

The GitHub Actions workflow handles image building and manifest updates:

1. Builds Chrome Node and Test Controller images from the Dockerfiles
2. Pushes images to Amazon ECR
3. Updates the Kubernetes manifests with new image tags
4. Commits the updated manifests back to the repository

After CI completes, pull the latest changes and run the deployment script to apply updates to your cluster.