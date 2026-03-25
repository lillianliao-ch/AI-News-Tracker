#!/bin/bash
# 用 IMDS.ai 的 ANTHROPIC_AUTH_TOKEN（可能是真实 Claude OAuth token）
export PATH="$HOME/.bun/bin:$PATH"
export ANTHROPIC_AUTH_TOKEN="sk-ec5425dbb6eb2bf8721b1dc2d225c91cb419a27ffe6d2263d2fb5e7a8b2bd256"
export ANTHROPIC_BASE_URL="https://imds.ai/"
exec claude \
  --channels "plugin:telegram@claude-plugins-official" \
  --dangerously-skip-permissions
