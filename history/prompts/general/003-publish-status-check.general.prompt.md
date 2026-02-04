---
id: "003"
title: "Social Media Posts Publishing Status Check"
stage: "general"
date_iso: "2026-02-03"
surface: "agent"
model: "claude-sonnet-4-5-20250929"
feature: "none"
branch: "001-stable-dashboard"
user: "madeeha"
command: "check if all posts were published successfully"
labels:
  - "social-media"
  - "publishing"
  - "validation"
  - "mcp"
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_yaml: |
  - /home/madeeha/Documents/Personal-AI-Employee/history/prompts/general/003-publish-status-check.general.prompt.md
tests_yaml: |
  - Facebook post publishing status
  - Instagram post publishing status
  - Twitter post publishing status
  - LinkedIn post publishing status
  - WhatsApp post publishing status
prompt_text: |
  check if all posts were published successfully
response_text: |
  ## Social Media Posts Publishing Status

  ### ✅ Successfully Published (Moved to Done folder):
  1. **LinkedIn**: Successfully published and moved to Done folder
  2. **Twitter**: Successfully published and moved to Done folder

  ### ❌ Failed to Publish (Remained in Approved folder with errors):
  1. **Facebook**: Failed due to "Application has been deleted" OAuth error
  2. **Instagram**: Failed due to "credentials not configured"
  3. **WhatsApp**: Failed due to "credentials not configured"

  ### Summary:
  - **2/5** social media platforms published successfully
  - **3/5** social media platforms failed due to credential/configuration issues
  - The system is working correctly - it moves successfully published posts to the Done folder and keeps failed posts in the Approved folder with detailed error messages

  The MCP servers are running and attempting to publish the posts, but they're failing due to authentication issues. This is expected behavior - the system properly handles failed publications by keeping them in the Approved folder with detailed error messages.
outcome: "Successfully validated the publishing status of all social media posts with detailed error reporting."
evaluation: "Success - Complete status check performed showing which posts published successfully and which failed with specific reasons"
---
