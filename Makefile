.PHONY: test e2e proto benchmark lint check help

help:
	@echo "Enterprise A2A Gateway Commands:"
	@echo "  make test        - Run all unit and security tests via pytest"
	@echo "  make e2e         - Run headless Google Signed Chrome Dual-Theme E2E suite"
	@echo "  make proto       - Compile Protocol Buffer stubs from protos/a2a.proto"
	@echo "  make benchmark   - Run AST ADK Sanitizer latency benchmark"

test:
	.venv/bin/pytest -v

e2e:
	NODE_PATH=node_modules node scratch/run_dual_theme_e2e.js

proto:
	./scripts/compile_protos.sh

benchmark:
	.venv/bin/python skills/ast-sanitizer-benchmark/scripts/benchmark_ast.py
