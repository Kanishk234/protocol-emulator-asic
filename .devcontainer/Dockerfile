ARG VARIANT=ubuntu-24.04
FROM mcr.microsoft.com/vscode/devcontainers/base:${VARIANT}
ENV DEBIAN_FRONTEND=noninteractive
ENV PDK=ihp-sg13cmos5l
RUN apt-get update && apt-get install -y --no-install-recommends \
    iverilog verilator yosys sigrok-cli gtkwave python3 python3-venv \
    python3-pip make git curl ca-certificates && rm -rf /var/lib/apt/lists/*
# Python packages belong to the workspace .venv, created after the checkout.
# Physical signoff uses the unchanged official GDS workflow, not this container.
