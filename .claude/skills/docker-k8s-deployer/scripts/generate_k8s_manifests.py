#!/usr/bin/env python3
"""
Kubernetes Manifest Generator - Creates K8s YAML manifests for deployments

Usage:
    generate_k8s_manifests.py --app-name <name> --namespace <ns> [options]

Options:
    --app-name          Application name (required)
    --namespace         Kubernetes namespace (default: default)
    --services          Comma-separated services: backend,frontend,db (default: backend)
    --image             Docker image for backend (default: app:latest)
    --frontend-image    Docker image for frontend
    --replicas          Number of replicas (default: 2)
    --port              Container port (default: 8000)
    --frontend-port     Frontend port (default: 3000)
    --output            Output directory (default: ./k8s)

Examples:
    generate_k8s_manifests.py --app-name myapp --namespace prod
    generate_k8s_manifests.py --app-name myapp --services backend,frontend --replicas 3
"""

import argparse
import sys
from pathlib import Path
import yaml


def generate_deployment(app_name: str, namespace: str, image: str,
                        port: int, replicas: int, component: str = 'backend') -> dict:
    """Generate Kubernetes Deployment manifest."""
    return {
        'apiVersion': 'apps/v1',
        'kind': 'Deployment',
        'metadata': {
            'name': f'{app_name}-{component}',
            'namespace': namespace,
            'labels': {
                'app': app_name,
                'component': component,
            },
        },
        'spec': {
            'replicas': replicas,
            'selector': {
                'matchLabels': {
                    'app': app_name,
                    'component': component,
                },
            },
            'template': {
                'metadata': {
                    'labels': {
                        'app': app_name,
                        'component': component,
                    },
                },
                'spec': {
                    'securityContext': {
                        'runAsNonRoot': True,
                        'runAsUser': 1000,
                        'fsGroup': 1000,
                    },
                    'containers': [{
                        'name': component,
                        'image': image,
                        'ports': [{
                            'containerPort': port,
                            'protocol': 'TCP',
                        }],
                        'envFrom': [{
                            'configMapRef': {
                                'name': f'{app_name}-config',
                            },
                        }, {
                            'secretRef': {
                                'name': f'{app_name}-secrets',
                            },
                        }],
                        'resources': {
                            'requests': {
                                'cpu': '100m',
                                'memory': '128Mi',
                            },
                            'limits': {
                                'cpu': '500m',
                                'memory': '512Mi',
                            },
                        },
                        'livenessProbe': {
                            'httpGet': {
                                'path': '/health',
                                'port': port,
                            },
                            'initialDelaySeconds': 15,
                            'periodSeconds': 20,
                            'timeoutSeconds': 5,
                            'failureThreshold': 3,
                        },
                        'readinessProbe': {
                            'httpGet': {
                                'path': '/health',
                                'port': port,
                            },
                            'initialDelaySeconds': 5,
                            'periodSeconds': 10,
                            'timeoutSeconds': 3,
                            'failureThreshold': 3,
                        },
                        'securityContext': {
                            'allowPrivilegeEscalation': False,
                            'readOnlyRootFilesystem': True,
                            'capabilities': {
                                'drop': ['ALL'],
                            },
                        },
                    }],
                },
            },
        },
    }


def generate_service(app_name: str, namespace: str, port: int,
                     component: str = 'backend') -> dict:
    """Generate Kubernetes Service manifest."""
    return {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {
            'name': f'{app_name}-{component}',
            'namespace': namespace,
            'labels': {
                'app': app_name,
                'component': component,
            },
        },
        'spec': {
            'type': 'ClusterIP',
            'selector': {
                'app': app_name,
                'component': component,
            },
            'ports': [{
                'name': 'http',
                'port': port,
                'targetPort': port,
                'protocol': 'TCP',
            }],
        },
    }


def generate_configmap(app_name: str, namespace: str) -> dict:
    """Generate Kubernetes ConfigMap manifest."""
    return {
        'apiVersion': 'v1',
        'kind': 'ConfigMap',
        'metadata': {
            'name': f'{app_name}-config',
            'namespace': namespace,
            'labels': {
                'app': app_name,
            },
        },
        'data': {
            'LOG_LEVEL': 'info',
            'DEBUG': 'false',
            # Add more non-sensitive config here
        },
    }


def generate_secret(app_name: str, namespace: str) -> dict:
    """Generate Kubernetes Secret manifest."""
    return {
        'apiVersion': 'v1',
        'kind': 'Secret',
        'metadata': {
            'name': f'{app_name}-secrets',
            'namespace': namespace,
            'labels': {
                'app': app_name,
            },
        },
        'type': 'Opaque',
        'stringData': {
            'DATABASE_URL': 'postgresql://user:password@db:5432/app',
            'SECRET_KEY': 'change-me-in-production',
            # Add more secrets here - use stringData for plaintext
        },
    }


def generate_namespace(namespace: str) -> dict:
    """Generate Kubernetes Namespace manifest."""
    return {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': namespace,
            'labels': {
                'name': namespace,
            },
        },
    }


def generate_hpa(app_name: str, namespace: str, component: str = 'backend') -> dict:
    """Generate Kubernetes HorizontalPodAutoscaler manifest."""
    return {
        'apiVersion': 'autoscaling/v2',
        'kind': 'HorizontalPodAutoscaler',
        'metadata': {
            'name': f'{app_name}-{component}-hpa',
            'namespace': namespace,
        },
        'spec': {
            'scaleTargetRef': {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'name': f'{app_name}-{component}',
            },
            'minReplicas': 2,
            'maxReplicas': 10,
            'metrics': [{
                'type': 'Resource',
                'resource': {
                    'name': 'cpu',
                    'target': {
                        'type': 'Utilization',
                        'averageUtilization': 70,
                    },
                },
            }, {
                'type': 'Resource',
                'resource': {
                    'name': 'memory',
                    'target': {
                        'type': 'Utilization',
                        'averageUtilization': 80,
                    },
                },
            }],
        },
    }


def generate_ingress(app_name: str, namespace: str, host: str,
                     backend_port: int, frontend_port: int = None) -> dict:
    """Generate Kubernetes Ingress manifest."""
    paths = [{
        'path': '/api',
        'pathType': 'Prefix',
        'backend': {
            'service': {
                'name': f'{app_name}-backend',
                'port': {'number': backend_port},
            },
        },
    }]

    if frontend_port:
        paths.append({
            'path': '/',
            'pathType': 'Prefix',
            'backend': {
                'service': {
                    'name': f'{app_name}-frontend',
                    'port': {'number': frontend_port},
                },
            },
        })

    return {
        'apiVersion': 'networking.k8s.io/v1',
        'kind': 'Ingress',
        'metadata': {
            'name': f'{app_name}-ingress',
            'namespace': namespace,
            'annotations': {
                'nginx.ingress.kubernetes.io/rewrite-target': '/$1',
            },
        },
        'spec': {
            'ingressClassName': 'nginx',
            'rules': [{
                'host': host,
                'http': {
                    'paths': paths,
                },
            }],
        },
    }


def write_manifest(manifest: dict, path: Path, filename: str):
    """Write a manifest to a YAML file."""
    filepath = path / filename
    with open(filepath, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    print(f"Generated: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate Kubernetes manifests for deployments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--app-name', required=True,
                        help='Application name')
    parser.add_argument('--namespace', default='default',
                        help='Kubernetes namespace (default: default)')
    parser.add_argument('--services', default='backend',
                        help='Comma-separated services: backend,frontend,db')
    parser.add_argument('--image', default='app:latest',
                        help='Docker image for backend')
    parser.add_argument('--frontend-image',
                        help='Docker image for frontend')
    parser.add_argument('--replicas', type=int, default=2,
                        help='Number of replicas (default: 2)')
    parser.add_argument('--port', type=int, default=8000,
                        help='Backend container port (default: 8000)')
    parser.add_argument('--frontend-port', type=int, default=3000,
                        help='Frontend container port (default: 3000)')
    parser.add_argument('--host', default='app.local',
                        help='Ingress host (default: app.local)')
    parser.add_argument('--output', default='./k8s',
                        help='Output directory (default: ./k8s)')
    parser.add_argument('--include-hpa', action='store_true',
                        help='Include HorizontalPodAutoscaler')
    parser.add_argument('--include-ingress', action='store_true',
                        help='Include Ingress')

    args = parser.parse_args()

    try:
        services = [s.strip() for s in args.services.split(',')]

        # Create output directory
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate namespace if not default
        if args.namespace != 'default':
            write_manifest(
                generate_namespace(args.namespace),
                output_path, '00-namespace.yaml'
            )

        # Generate ConfigMap and Secret
        write_manifest(
            generate_configmap(args.app_name, args.namespace),
            output_path, '01-configmap.yaml'
        )
        write_manifest(
            generate_secret(args.app_name, args.namespace),
            output_path, '02-secret.yaml'
        )

        # Generate backend manifests
        if 'backend' in services:
            write_manifest(
                generate_deployment(
                    args.app_name, args.namespace, args.image,
                    args.port, args.replicas, 'backend'
                ),
                output_path, '10-backend-deployment.yaml'
            )
            write_manifest(
                generate_service(
                    args.app_name, args.namespace, args.port, 'backend'
                ),
                output_path, '11-backend-service.yaml'
            )
            if args.include_hpa:
                write_manifest(
                    generate_hpa(args.app_name, args.namespace, 'backend'),
                    output_path, '12-backend-hpa.yaml'
                )

        # Generate frontend manifests
        if 'frontend' in services:
            frontend_image = args.frontend_image or f'{args.app_name}-frontend:latest'
            write_manifest(
                generate_deployment(
                    args.app_name, args.namespace, frontend_image,
                    args.frontend_port, args.replicas, 'frontend'
                ),
                output_path, '20-frontend-deployment.yaml'
            )
            write_manifest(
                generate_service(
                    args.app_name, args.namespace, args.frontend_port, 'frontend'
                ),
                output_path, '21-frontend-service.yaml'
            )
            if args.include_hpa:
                write_manifest(
                    generate_hpa(args.app_name, args.namespace, 'frontend'),
                    output_path, '22-frontend-hpa.yaml'
                )

        # Generate Ingress
        if args.include_ingress:
            frontend_port = args.frontend_port if 'frontend' in services else None
            write_manifest(
                generate_ingress(
                    args.app_name, args.namespace, args.host,
                    args.port, frontend_port
                ),
                output_path, '30-ingress.yaml'
            )

        print(f"\nGenerated K8s manifests in: {output_path}")
        print("\nApply with:")
        print(f"  kubectl apply -f {output_path}/")
        print("\nOr apply in order:")
        print(f"  kubectl apply -f {output_path}/ --recursive")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
