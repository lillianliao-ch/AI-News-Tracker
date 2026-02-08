#!/bin/bash
# Investor Tracking Daily Update Wrapper
# Configured for User: lillianliao
# Project: notion_rag

# 1. Enter Project Directory
cd /Users/lillianliao/notion_rag

# 2. Execute Python Script using Virtual Environment
# Appending output to daily_update.log for debugging
/Users/lillianliao/notion_rag/.venv/bin/python3 investor_tracking/run_daily_update.py >> daily_update.log 2>&1
