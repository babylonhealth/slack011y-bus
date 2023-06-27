NAME=slack011y-bus
VERSION=$(shell git rev-parse HEAD)
SEMVER_VERSION=$(shell git describe --abbrev=0 --tags)
REQUIREMENTS_HASH=$(shell sha1sum poetry.lock Dockerfile-requirements | sha1sum | cut -d' ' -f1)
REQUIREMENTS_TAG=requirements-$(REQUIREMENTS_HASH)
DOCKER_REPO_HOST=
DOCKER_REPO_ORG=
MAX_LINE_LENGTH=125

run-%:
	./run.sh --$*

clean:
	find . -name "*.py[cod]" -delete

format:
	black .
	isort .

lint:
	flake8 --max-line-length $(MAX_LINE_LENGTH) --ignore=E203,W503 --extend-exclude venv
	black . --check
	isort . --check-only

typecheck:
	MYPYPATH=src mypy -p src

setup-poetry:
	python -m pip install --upgrade pip

install: setup-poetry
	poetry install --no-ansi

build-requirements: clean
	@if docker run -e DOCKER_REPO=$(DOCKER_REPO_ORG)/$(REQUIREMENTS_NAME) -e DOCKER_TAG=$(REQUIREMENTS_TAG) $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/tag-exists; \
	  then echo "Requirements image tag $(REQUIREMENTS_TAG) already exists, skipping the build"; \
	else \
	  docker build -t $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(REQUIREMENTS_TAG) -f Dockerfile-requirements .; \
	  docker push $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(REQUIREMENTS_TAG); \
	fi

build: build-requirements
	docker build --build-arg REQUIREMENTS_TAG=$(REQUIREMENTS_TAG) -t $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(VERSION) .
	docker push $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(VERSION)

test-unit:
	pytest -vvv -p monkeypatch --mypy --cov src/code --cov-report xml --cov-report term src/tests
	
test-unit-dev:
	pytest -vvv -p monkeypatch --mypy --cov src/code --cov-report html --cov-report term src/tests

test-integration:

tag-latest:
	docker tag $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(VERSION) $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):latest
	docker push $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(VERSION)
	docker push $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):latest

tag-semver:
	@if docker run -e DOCKER_REPO=$(DOCKER_REPO_ORG)/$(NAME) -e DOCKER_TAG=$(SEMVER_VERSION) $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/tag-exists; \
	  then echo "Tag $(SEMVER_VERSION) already exists!" && exit 1 ; \
	else \
	  docker tag $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(VERSION) $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(SEMVER_VERSION); \
	  docker push $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(SEMVER_VERSION); \
	fi

docker-pull:
	docker pull $(DOCKER_REPO_HOST)/$(DOCKER_REPO_ORG)/$(NAME):$(VERSION)

.PHONY: run clean format lint typecheck setup-poetry install build-requirements build test test-unit test-integration tag-latest docker-pull tag-semver local-redis stop-local-redis
