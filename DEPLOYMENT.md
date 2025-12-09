# Kubernetes Test Automation – Deployment Rehberi

Bu doküman, Selenium tabanlı testlerin AWS EKS üzerinde nasıl çalıştırıldığını kısaca özetler.  

- CI kısmı GitHub Actions workflow ile yürütülür.
- Deployment kısmı `deploy.py` scripti ile yapılır.
- EKS cluster’ı AWS CLI ile oluşturulmuştur.
- Deployment, gerekli IAM rolleri atanmış bir Amazon Linux EC2 instance üzerinden yapılır.

---

## 1. Genel Mimari

Sistem iki ana pod’dan oluşur:

1. **Test Controller Pod**
   - `tests/`, `pages/` ve `conftest.py` içindeki test kodlarını çalıştırır.
   - Pytest ile testleri başlatır.
   - `CHROME_NODE_SERVICE` gibi ayarları ConfigMap’ten alır.
   - Selenium’u `Remote WebDriver` olarak kullanır.

2. **Chrome Node Pod(lar)**
   - Selenium Grid ve headless Chrome çalıştırır.
   - Kubernetes’te bir Deployment ile yönetilir.
   - `chrome-node-service` isimli bir ClusterIP Service ile 4444 portundan ulaşılan bir endpoint sağlar.

**Pod iletişimi:**

- Test Controller Pod, `CHROME_NODE_SERVICE=http://chrome-node-service:4444` adresine bağlanır.
- Trafik, ClusterIP Service üzerinden uygun Chrome Node Pod’una yönlendirilir.

---

## 2. CI Süreci (GitHub Actions)

Repository içinde tanımlı GitHub Actions workflow şu işleri yapar:

1. Kodu checkout eder.
2. `aws-actions/configure-aws-credentials` ile AWS kimlik bilgilerini yükler.
3. `aws-actions/amazon-ecr-login` ile ECR’a login olur.
4. Gerekirse ECR repository’lerini oluşturur:
   - Chrome Node imajı için (`CHROME_REPO_NAME`, örn: `chrome-node3`)
   - Test Controller imajı için (`CONTROLLER_REPO_NAME`, örn: `test-controller3`)
5. Docker imajlarını build eder ve ECR’a push eder:
   - `docker/Dockerfile.chromenode`
   - `docker/Dockerfile.controller`
6. `k8s/manifests/03-chrome-node-deployment.yaml` ve
   `k8s/manifests/05-test-controller-deployment.yaml` dosyalarındaki `image:` alanlarını
   ilgili ECR image URI’leri ile günceller.
7. Manifest değişikliklerini commit edip repository’ye push eder.

Bu sayede her `main` push’unda güncel imajlar otomatik olarak ECR’a atılır ve manifest’ler güncel kalır.

---

## 3. Deployment Ortamı (EC2)

Deployment işlemi, AWS üzerinde çalışan bir Amazon Linux EC2 instance üzerinden yapılır.

Özellikler:

- Örnek tip: `t3a.medium`
- IAM role:
  - EKS cluster’a erişim (EKS API)
  - ECR’dan imaj çekme yetkisi
- Kurulu araçlar:
  - `awscli`
  - `kubectl`
  - `eksctl`
  - `docker`
  - `git`
  - `python3`

---

## 4. EKS Cluster ve Kubeconfig

EKS cluster AWS CLI ile oluşturulmuştur. 

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
EC2 üzerinde kubeconfig güncellemesi için: FARKLI MAKİNEDEN BAĞLANIRKEN

```

AWS_REGION=us-east-1
CLUSTER_NAME=<eks-cluster-adiniz>

aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"
kubectl get nodes
````

`kubectl get nodes` çıktısında worker node’ları görmeniz gerekir.

---

## 5. Repository’yi Çekme

EC2 instance üzerinde:

```bash
cd ~
git clone https://github.com/refkylp/TestOps.git
cd TestOps

# Eğer repo zaten varsa
git pull
```

Bu aşamada `k8s/manifests` içindeki deployment dosyaları zaten GitHub Actions tarafından
ECR image path’leri ile güncellenmiş durumda olur.

---

## 6. EKS’e Deployment (deploy.py ile)

Deployment, `deploy.py` scripti ile yapılır. Script kabaca şu işleri üstlenir:

* Gerekli namespace’i oluşturur (örneğin `test-automation`).
* ConfigMap’i uygular (Chrome Node service URL, retry ayarları vb.).
* Chrome Node Deployment ve Service’i oluşturur.
* Chrome Node Pod’larının hazır olmasını bekler.
* Test Controller Deployment’ını uygular.
* Test Controller loglarını /reports kalsörüne atar. (sudo chown -R ec2-user:ec2-user reports/ ile izin verilmeli)

Örnek kullanım:

```bash
python3 deploy.py --node-count=2   # node sayısı default 2, ancak min1 max5 olacak şekilde değiştirilebilir.
```

Deployment sonrası kontrol:

```bash
NAMESPACE=test-automation
kubectl get all -n "$NAMESPACE"
kubectl get pods -n "$NAMESPACE"
kubectl get svc -n "$NAMESPACE"
```

Test Controller loglarını izlemek için:

```bash
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l component=test-controller -o jsonpath='{.items[0].metadata.name}')
kubectl logs -f "$POD_NAME" -n "$NAMESPACE"
```

---

## 7. Temizlik

Kaynakları temizlemek için:

```bash
# Script ile
python3 deploy.py --cleanup

# Manuel
kubectl delete namespace test-automation

# eks cluster silme
aws eks describe-cluster --name test-automation --region us-east-1

# ecr repo silme
aws ecr delete-repository --repository-name repo-ismi --region us-east-1
```

Bu doküman, CI tarafının GitHub Actions, deployment tarafının ise `deploy.py` ile yönetildiği
ve EKS cluster’ın önceden AWS CLI ile oluşturulduğu senaryoyu temel alır.


