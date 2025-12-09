#!/usr/bin/env python3
"""
Kubernetes Test Automation Deployment Script
Bu script Selenium test otomasyonunu Kubernetes cluster'ında deploy eder ve yönetir.
"""

import subprocess
import sys
import time
import argparse
import os
from pathlib import Path


class Colors:
    """Terminal renk kodları"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class KubernetesDeployer:
    """Kubernetes deployment yöneticisi"""

    def __init__(self, manifests_dir='k8s/manifests', node_count=2):
        self.manifests_dir = Path(manifests_dir)
        self.node_count = max(1, min(5, node_count))  # 1-5 arası
        self.namespace = 'test-automation'
        self.max_retries = 5
        self.retry_delay = 10
        self.deployment_timeout = 300  # 5 dakika

    def log(self, message, color=Colors.OKBLUE):
        """Renkli log mesajı yazdır"""
        print(f"{color}{message}{Colors.ENDC}")

    def run_command(self, command, check=True, capture_output=True):
        """Komut çalıştır"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                capture_output=capture_output,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Komut hatası: {e}", Colors.FAIL)
            if capture_output and e.stderr:
                self.log(f"Hata detayı: {e.stderr}", Colors.FAIL)
            raise

    def check_kubectl(self):
        """kubectl kurulu mu kontrol et"""
        self.log("kubectl kontrol ediliyor...", Colors.HEADER)
        try:
            result = self.run_command("kubectl version --client")
            self.log("✓ kubectl bulundu", Colors.OKGREEN)
            return True
        except:
            self.log("✗ kubectl bulunamadı! Lütfen kubectl'i yükleyin.", Colors.FAIL)
            return False

    def check_cluster_connection(self):
        """Kubernetes cluster bağlantısını kontrol et"""
        self.log("Cluster bağlantısı kontrol ediliyor...", Colors.HEADER)
        try:
            result = self.run_command("kubectl cluster-info")
            self.log("✓ Cluster'a bağlantı başarılı", Colors.OKGREEN)
            return True
        except:
            self.log("✗ Cluster'a bağlanılamadı!", Colors.FAIL)
            return False

    def create_namespace(self):
        """Namespace oluştur"""
        self.log(f"\n{self.namespace} namespace oluşturuluyor...", Colors.HEADER)
        manifest = self.manifests_dir / '01-namespace.yaml'
        try:
            self.run_command(f"kubectl apply -f {manifest}")
            self.log(f"✓ Namespace oluşturuldu", Colors.OKGREEN)
            return True
        except:
            self.log("✗ Namespace oluşturulamadı", Colors.FAIL)
            return False

    def deploy_configmap(self):
        """ConfigMap deploy et"""
        self.log("\nConfigMap deploy ediliyor...", Colors.HEADER)
        manifest = self.manifests_dir / '02-configmap.yaml'

        # ConfigMap'i node_count ile güncelle
        try:
            self.run_command(f"kubectl apply -f {manifest}")
            # Node count'u güncelle
            self.run_command(
                f"kubectl patch configmap test-automation-config "
                f"-n {self.namespace} "
                f"--type merge -p '{{\"data\":{{\"node_count\":\"{self.node_count}\"}}}}'"
            )
            self.log(f"✓ ConfigMap deploy edildi (node_count: {self.node_count})", Colors.OKGREEN)
            return True
        except:
            self.log("✗ ConfigMap deploy edilemedi", Colors.FAIL)
            return False

    def deploy_chrome_node_service(self):
        """Chrome Node Service deploy et"""
        self.log("\nChrome Node Service deploy ediliyor...", Colors.HEADER)
        manifest = self.manifests_dir / '04-chrome-node-service.yaml'
        try:
            self.run_command(f"kubectl apply -f {manifest}")
            self.log("✓ Chrome Node Service deploy edildi", Colors.OKGREEN)
            return True
        except:
            self.log("✗ Chrome Node Service deploy edilemedi", Colors.FAIL)
            return False

    def scale_chrome_nodes(self):
        """Chrome Node deployment'ı scale et"""
        self.log(f"\nChrome Node deployment scale ediliyor ({self.node_count} replica)...", Colors.HEADER)
        manifest = self.manifests_dir / '03-chrome-node-deployment.yaml'
        try:
            self.run_command(f"kubectl apply -f {manifest}")
            # Replica sayısını ayarla
            self.run_command(
                f"kubectl scale deployment chrome-node "
                f"-n {self.namespace} --replicas={self.node_count}"
            )
            self.log(f"✓ Chrome Node deployment scale edildi", Colors.OKGREEN)
            return True
        except:
            self.log("✗ Chrome Node deployment scale edilemedi", Colors.FAIL)
            return False

    def wait_for_chrome_nodes_ready(self):
        """Chrome Node'ların hazır olmasını bekle"""
        self.log("\nChrome Node'ların hazır olması bekleniyor...", Colors.HEADER)

        start_time = time.time()
        while time.time() - start_time < self.deployment_timeout:
            try:
                result = self.run_command(
                    f"kubectl get deployment chrome-node -n {self.namespace} "
                    f"-o jsonpath='{{.status.readyReplicas}}'",
                    check=False
                )
                ready_replicas = result.stdout.strip()

                if ready_replicas and int(ready_replicas) == self.node_count:
                    self.log(f"✓ Tüm Chrome Node'lar hazır ({ready_replicas}/{self.node_count})", Colors.OKGREEN)
                    return True
                else:
                    ready = ready_replicas if ready_replicas else "0"
                    self.log(f"  Hazır pod sayısı: {ready}/{self.node_count}", Colors.WARNING)
                    time.sleep(self.retry_delay)
            except Exception as e:
                self.log(f"  Kontrol hatası: {e}", Colors.WARNING)
                time.sleep(self.retry_delay)

        self.log("✗ Chrome Node'lar timeout süresinde hazır olamadı", Colors.FAIL)
        return False

    def verify_chrome_node_service(self):
        """Chrome Node Service'in çalıştığını doğrula"""
        self.log("\nChrome Node Service doğrulanıyor...", Colors.HEADER)
        try:
            result = self.run_command(
                f"kubectl get endpoints chrome-node-service -n {self.namespace} "
                f"-o jsonpath='{{.subsets[*].addresses[*].ip}}'",
                check=False
            )
            endpoints = result.stdout.strip()

            if endpoints:
                endpoint_list = endpoints.split()
                self.log(f"✓ Service hazır ({len(endpoint_list)} endpoint)", Colors.OKGREEN)
                return True
            else:
                self.log("✗ Service endpoint'leri bulunamadı", Colors.FAIL)
                return False
        except:
            self.log("✗ Service doğrulanamadı", Colors.FAIL)
            return False

    def deploy_test_controller(self):
        """Test Controller'ı deploy et"""
        self.log("\nTest Controller deploy ediliyor...", Colors.HEADER)
        manifest = self.manifests_dir / '05-test-controller-deployment.yaml'
        try:
            self.run_command(f"kubectl apply -f {manifest}")
            self.log("✓ Test Controller deploy edildi", Colors.OKGREEN)
            return True
        except:
            self.log("✗ Test Controller deploy edilemedi", Colors.FAIL)
            return False

    def monitor_test_execution(self):
        """Test execution'ı izle"""
        self.log("\nTest execution izleniyor...", Colors.HEADER)
        self.log("Test Controller logları:\n", Colors.OKCYAN)

        # Pod'un başlamasını bekle
        time.sleep(5)

        try:
            # Pod adını al
            result = self.run_command(
                f"kubectl get pods -n {self.namespace} "
                f"-l component=test-controller "
                f"-o jsonpath='{{.items[0].metadata.name}}'",
                check=False
            )
            pod_name = result.stdout.strip()

            if not pod_name:
                self.log("✗ Test Controller pod bulunamadı", Colors.FAIL)
                return False

            # Logları takip et (tail -f /dev/null için timeout)
            self.log("Testler çalışıyor, loglar izleniyor...\n")

            max_wait = 300 
            start_time = time.time()
            test_completed = False

            while time.time() - start_time < max_wait:
                result = self.run_command(
                    f"kubectl logs {pod_name} -n {self.namespace} --tail=100",
                    check=False,
                    capture_output=True
                )

                # "Tests completed" veya "passed in" mesajı var mı?
                if result.stdout and ("Tests completed" in result.stdout or "passed in" in result.stdout or "failed in" in result.stdout):
                    # Tüm logları göster
                    full_logs = self.run_command(
                        f"kubectl logs {pod_name} -n {self.namespace}",
                        check=False,
                        capture_output=True
                    )
                    print(full_logs.stdout)
                    test_completed = True
                    break

                time.sleep(5) 

            if not test_completed:
                self.log("\n⚠ Test timeout (5 dakika)", Colors.WARNING)
                # Timeout olsa bile logları göster
                full_logs = self.run_command(
                    f"kubectl logs {pod_name} -n {self.namespace}",
                    check=False,
                    capture_output=True
                )
                print(full_logs.stdout)

            # Test sonucunu kontrol et
            result = self.run_command(
                f"kubectl logs {pod_name} -n {self.namespace}",
                check=False,
                capture_output=True
            )

            if "passed in" in result.stdout and "failed" not in result.stdout:
                self.log("\n✓ Testler başarıyla tamamlandı!", Colors.OKGREEN)
                return True
            else:
                self.log(f"\n✗ Testler başarısız veya tamamlanmadı", Colors.WARNING)
                return True  # Rapor kaydetmek için True dön

        except Exception as e:
            self.log(f"✗ Test monitoring hatası: {e}", Colors.FAIL)
            return False

    def save_test_reports(self):
        """Test raporlarını local'e kaydet"""
        self.log("\nTest raporları kaydediliyor...", Colors.HEADER)

        try:
            # Report dizini
            report_dir = getattr(self, 'report_dir', '/home/ec2-user/TestOps/reports')

            # Report dizinini oluştur
            import os
            os.makedirs(report_dir, exist_ok=True)

            # Timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            report_file = f"{report_dir}/test-results-{timestamp}.log"

            # Pod adını al
            result = self.run_command(
                f"kubectl get pods -n {self.namespace} "
                f"-l component=test-controller "
                f"-o jsonpath='{{.items[0].metadata.name}}'",
                check=False
            )
            pod_name = result.stdout.strip()

            if not pod_name:
                self.log("✗ Test Controller pod bulunamadı", Colors.FAIL)
                return False

            # Logları kaydet
            self.run_command(
                f"kubectl logs {pod_name} -n {self.namespace} > {report_file}",
                check=False
            )

            self.log(f"✓ Test raporu kaydedildi: {report_file}", Colors.OKGREEN)

            # Özet göster
            self.run_command(
                f"cat {report_file} | grep -E '(passed|failed) in' || echo 'Test sonucu bulunamadı'",
                check=False,
                capture_output=False
            )

            return True

        except Exception as e:
            self.log(f"✗ Rapor kaydetme hatası: {e}", Colors.FAIL)
            return False

    def cleanup(self):
        """Tüm kaynakları temizle"""
        self.log("\nKaynaklar temizleniyor...", Colors.HEADER)
        try:
            self.run_command(f"kubectl delete namespace {self.namespace}")
            self.log("✓ Tüm kaynaklar temizlendi", Colors.OKGREEN)
            return True
        except:
            self.log("✗ Temizleme hatası", Colors.FAIL)
            return False

    def deploy(self):
        """Tam deployment sürecini çalıştır"""
        self.log(f"\n{'='*60}", Colors.BOLD)
        self.log("Kubernetes Test Automation Deployment", Colors.BOLD)
        self.log(f"{'='*60}\n", Colors.BOLD)

        # Ön kontroller
        if not self.check_kubectl():
            return False
        if not self.check_cluster_connection():
            return False

        # Deploy adımları
        steps = [
            ("Namespace", self.create_namespace),
            ("ConfigMap", self.deploy_configmap),
            ("Chrome Node Service", self.deploy_chrome_node_service),
            ("Chrome Node Deployment", self.scale_chrome_nodes),
            ("Chrome Node Readiness", self.wait_for_chrome_nodes_ready),
            ("Service Verification", self.verify_chrome_node_service),
            ("Test Controller", self.deploy_test_controller),
            ("Test Execution", self.monitor_test_execution),
            ("Save Reports", self.save_test_reports)
        ]

        for step_name, step_func in steps:
            if not step_func():
                self.log(f"\n✗ Deployment başarısız: {step_name} adımında hata", Colors.FAIL)
                return False

        self.log(f"\n{'='*60}", Colors.BOLD)
        self.log("✓ Deployment başarıyla tamamlandı!", Colors.OKGREEN)
        self.log(f"{'='*60}\n", Colors.BOLD)
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Kubernetes Test Automation Deployment Script'
    )
    parser.add_argument(
        '--node-count',
        type=int,
        default=2,
        help='Chrome Node pod sayısı (1-5 arası, varsayılan: 2)'
    )
    parser.add_argument(
        '--manifests-dir',
        type=str,
        default='k8s/manifests',
        help='Kubernetes manifest dosyalarının bulunduğu dizin'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Tüm kaynakları temizle ve çık'
    )
    parser.add_argument(
        '--report-dir',
        type=str,
        default='/home/ec2-user/TestOps/reports',
        help='Test raporlarının kaydedileceği dizin (varsayılan: /home/ec2-user/TestOps/reports)'
    )

    args = parser.parse_args()

    deployer = KubernetesDeployer(
        manifests_dir=args.manifests_dir,
        node_count=args.node_count
    )
    deployer.report_dir = args.report_dir

    if args.cleanup:
        success = deployer.cleanup()
        sys.exit(0 if success else 1)

    success = deployer.deploy()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
