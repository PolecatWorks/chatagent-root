
HELM_NAME=chatagent
TAG ?= 0.3.0
REPO ?= dockerreg.k8s:5000/polecatworks

DOCKER=docker

BASE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

UVICORN=${BASE_DIR}mcp-venv/bin/uvicorn

aiohttp_apps:=chatagent

PDB = --pdb

chatagent_CMD=chatagent
chatagent_PORT=8000
chatagent_HEALTH_PORT=8079

m365agentsplayground_PORT=56150

customer-mcp_CMD=customer
customer-mcp_HOST=0.0.0.0
customer-mcp_PORT=8180
customer-mcp_HEALTH_PORT=8179

a2a_PORT=8280
a2a_HEALTH_PORT=8279


guard-%:
	@ if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi

status:
	@echo "Aiohhtp apps are: $(aiohttp_apps)"
	@echo "MCP app is: customer-mcp"


# VENV Creation

$(foreach app,$(aiohttp_apps) customer-mcp,$(app)-venv/bin/activate):%-venv/bin/activate:%-container/pyproject.toml
	@echo Creating venv for $*
	python3 -m venv $*-venv
	$*-venv/bin/pip install --upgrade pip
	$*-venv/bin/pip install poetry
	cd $*-container && \
	${BASE_DIR}$*-venv/bin/poetry install --with dev && \
	${BASE_DIR}$*-venv/bin/pip install -e .[dev]


# .PRECIOUS: $(foreach app,$(aiohttp_apps),$(app)-venv)


# $(foreach app,$(aiohttp_apps),$(app)-venv/bin/pytest): %-venv/bin/pytest:%-venv/bin/activate

$(foreach app,$(aiohttp_apps),$(app)-venv/bin/pytest): %-venv/bin/pytest: %-venv/bin/adev
	@touch $@

$(foreach app,customer-mcp,$(app)-venv/bin/pytest): %-venv/bin/pytest: %-venv/bin/uvicorn
	@touch $@


$(foreach app,$(aiohttp_apps),$(app)-venv/bin/adev):%-venv/bin/adev: %-venv/bin/activate
	@echo creating development tools for $*
	@source $*-venv/bin/activate && cd $*-container && poetry install --with dev && pip install -e .[dev] && deactivate && cd ..
	@touch $@


$(foreach app,$(aiohttp_apps) customer-mcp,$(app)-run):%-run: %-venv/bin/activate
	cd $*-container && \
	APP_WEBSERVICE__URL="http://${$*_HOST}:${$*_PORT}" \
	${BASE_DIR}$*-venv/bin/${$*_CMD} start --secrets tests/test_data/secrets --config tests/test_data/config.yaml


$(foreach app,$(aiohttp_apps),$(app)-dev):%-dev:%-venv/bin/adev
	cd $*-container && \
	${BASE_DIR}$*-venv/bin/adev runserver --port ${$*_PORT}


$(foreach app,customer-mcp,$(app)-venv/bin/uvicorn):%-venv/bin/uvicorn: %-venv/bin/activate
	@echo creating development tools for $*
	@source $*-venv/bin/activate && cd $*-container && poetry install --with dev && pip install -e .[dev] && deactivate && cd ..
	@touch $@


$(foreach app,customer-mcp,$(app)-dev):%-dev:%-venv/bin/uvicorn
	cd $*-container && \
	${UVICORN} dev:app --port $($*_PORT) --reload --reload-exclude "tests/*" --reload-include "customer/**"



$(foreach app,$(aiohttp_apps) customer-mcp,$(app)-test):%-test: %-venv/bin/pytest
	cd $*-container && \
	${BASE_DIR}$*-venv/bin/pytest -v


$(foreach app,$(aiohttp_apps) customer-mcp,$(app)-ptw):%-ptw: %-venv/bin/pytest
	cd $*-container && \
	${BASE_DIR}$*-venv/bin/ptw --runner ${BASE_DIR}$*-venv/bin/pytest ${PDB} . -- --enable-livellm


$(foreach app,$(aiohttp_apps) customer-mcp,$(app)-docker):%-docker:
	$(DOCKER) build $*-container -t $* -f $*-container/Dockerfile


# %-docker-test:
# 	$(DOCKER) build $*-container -t $*-test -f $*-container/Dockerfile --target test


# $(foreach app,$(aiohttp_apps),$(app)-docker-run)%-docker-run: %-docker
# 	${DOCKER} run -it --rm \
# 		--name $* \
# 		-v $(shell pwd)/$*-container/tests/test_data/secrets:/opt/app/secrets \
# 		-v $(shell pwd)/$*-container/tests/test_data/config.yaml:/opt/app/configs/config.yaml \
# 		-p ${$*_PORT}:8080 -p ${$*_HEALTH_PORT}:8079 \
# 		$* \
# 		start --secrets /opt/app/secrets --config /opt/app/configs/config.yaml




# terraform-init:
# 	cd terraform && terraform init

# terraform-plan:
# 	cd terraform && terraform plan

# terraform-apply:
# #   add TF_LOG=DEBUG to debug
# 	cd terraform && terraform apply

# terraform-destroy:
# 	cd terraform && terraform destroy




# .ONESHELL:
# docker-build-sample:
# 	{ \
# 	$(DOCKER) build container-python -t $(NAME) -f container-python/Dockerfile; \
# 	$(DOCKER) image ls $(NAME); \
# 	}


# dockerx:
# 	$(DOCKER)  buildx build --push container-python -t $(REPO)/$(NAME):$(TAG) -f container-python/Dockerfile --platform linux/arm64/v8,linux/amd64





m365agentsplayground-env/node_modules/.bin/agentsplayground:
	mkdir -p m365agentsplayground-env
	cd m365agentsplayground-env && npm install @microsoft/m365agentsplayground


m365agentsplayground-dev: m365agentsplayground-env/node_modules/.bin/agentsplayground
	m365agentsplayground-env/node_modules/.bin/agentsplayground -e "http://localhost:${chatagent_PORT}/api/messages" -c "emulator"


m365agentsplayground-docker:
	$(DOCKER) build m365agentsplayground-container -t m365agentsplayground

m365agentsplayground-docker-run: m365agentsplayground-docker
	$(DOCKER) run -it --rm \
		--name m365agentsplayground \
		-p ${m365agentsplayground_PORT}:56150 \
		--add-host=host.docker.internal:host-gateway \
		m365agentsplayground \
		-p 56150 -e "http://host.docker.internal:${chatagent_PORT}/api/messages" -c "emulator"

# 		--add-host=host.docker.internal:host-gateway \

# helm:
# 	@echo Creating helm chart
# 	cd charts && \
# 	helm package ${HELM_NAME}



# clean:
# 	rm -rf *-venv
# 	find *-container -name "*.pyc" -exec rm -f {} \;
