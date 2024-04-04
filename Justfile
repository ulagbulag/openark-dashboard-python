# Configure environment variables
export ALPINE_VERSION := env_var_or_default('ALPINE_VERSION', '3.19')
export CUDA_VERSION := env_var_or_default('CUDA_VERSION', '12.2.0')
export OCI_IMAGE := env_var_or_default('OCI_IMAGE', 'quay.io/ulagbulag/openark-dash-management-tool')
export OCI_IMAGE_VERSION := env_var_or_default('OCI_IMAGE_VERSION', 'latest')
export OCI_PLATFORMS := env_var_or_default('OCI_PLATFORMS', 'linux/amd64')
export UBUNTU_VERSION := env_var_or_default('UBUNTU_VERSION', '22.04')

default:
  @just run

run *ARGS:
  streamlit run main.py \
    --browser.gatherUsageStats=False \
    --server.address=0.0.0.0 \
    --server.baseUrlPath=/dev/dash/ \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.headless=true \
    --server.port=8501 \
    {{ ARGS }}

oci-build:
  docker buildx build \
    --file './Dockerfile.alpine' \
    --tag "${OCI_IMAGE}:${OCI_IMAGE_VERSION}" \
    --build-arg ALPINE_VERSION="${ALPINE_VERSION}" \
    --build-arg CUDA_VERSION="${CUDA_VERSION}" \
    --build-arg UBUNTU_VERSION="${UBUNTU_VERSION}" \
    --platform "${OCI_PLATFORMS}" \
    --pull \
    --push >logs.txt 2>logs.txt \
    .

oci-push: oci-build

oci-push-and-update-dash: oci-push
  kubectl -n dash delete pods --selector name=management-tool
