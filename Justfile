# Configure environment variables
export CUDA_VERSION := env_var_or_default('CUDA_VERSION', '12.3.2')
export DEBIAN_IMAGE := env_var_or_default('DEBIAN_IMAGE', 'docker.io/library/python')
export DEBIAN_VERSION := env_var_or_default('DEBIAN_VERSION', '3.12-slim')
export OCI_IMAGE := env_var_or_default('OCI_IMAGE', 'quay.io/ulagbulag/openark-dash-management-tool')
export OCI_IMAGE_VERSION := env_var_or_default('OCI_IMAGE_VERSION', 'latest')
export OCI_PLATFORMS := env_var_or_default('OCI_PLATFORMS', 'linux/amd64')
export UBUNTU_VERSION := env_var_or_default('UBUNTU_VERSION', '22.04')

default:
  @just run

check:
  # stop if there are Python syntax errors or undefined names
  flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

  # stop on all errors as warnings
  flake8 . --count --exit-zero --max-complexity=10 --max-line-length=80 --statistics

  # FIXME: enable it when python=3.12 support
  # python -m pylint $(git ls-files '*.py')

test: check
  python -m pytest -v tests/*.py

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
    --file './Dockerfile.ubuntu' \
    --tag "${OCI_IMAGE}:${OCI_IMAGE_VERSION}" \
    --build-arg CUDA_VERSION="${CUDA_VERSION}" \
    --build-arg DEBIAN_IMAGE="${DEBIAN_IMAGE}" \
    --build-arg DEBIAN_VERSION="${DEBIAN_VERSION}" \
    --build-arg UBUNTU_VERSION="${UBUNTU_VERSION}" \
    --platform "${OCI_PLATFORMS}" \
    --pull \
    --push \
    .

oci-push: oci-build

oci-push-and-update-dash: oci-push
  kubectl -n dash rollout restart deploy management-tool
