# fix-add-ai-evolution.ps1
# Adds AI evolution timeline with interview-ready details to M00
# Run: .\fix-add-ai-evolution.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding AI Evolution Timeline to M00 ===" -ForegroundColor Cyan
Write-Host "1 module updated. Estimated: 10 minutes." -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/1] M00 - Adding evolution timeline..." -ForegroundColor Green

$cmd = @"
Read prompts/21-ai-evolution-timeline.md for the complete specification with research-backed details. Open the M00 HTML file in output/. Add a new section as the VERY FIRST section before everything else titled The Evolution: From Rule-Based AI to Agentic AI.

Include an animated horizontal timeline with 7 eras each with specific dates and key names and milestones: Era 1 Foundations and Rule-Based AI 1948-2000s with Shannon and Turing and McCarthy and Deep Blue and expert systems. Era 2 Machine Learning 2000s-2015 with Random Forests and Hinton and AlexNet and GANs. Era 3 Transformers and NLP 2017-2020 with the Attention Is All You Need paper and GPT-1 and BERT and GPT-3. Era 4 Generative AI Explosion 2020-2023 with DALL-E and Stable Diffusion and Midjourney and GitHub Copilot and ChatGPT reaching 100M users. Explain the 4 types of generative AI: text and image and code and audio-video generation. Explain the KEY LIMITATION that generative AI generates but cannot ACT which is the gap agents fill. Era 5 LLMs Mature 2023-2024 with Claude 3 family and RAG and fine-tuning becoming standard and enterprise adoption. Era 6 Agentic AI 2024-present with Claude tool use and MCP protocol and Agent SDK and Google A2A and AWS Strands. Era 7 The Frontier 2025-2026 with multi-modal agents and distributed agentic intranets.

Each era must have a UCC domain example and an Interview Answer paragraph in a callout box that students can memorize.

Include the Why Agents Are Possible NOW table comparing 2022 vs 2026 across 5 capabilities showing 240x cost reduction and 200K context windows and native tool use.

Include the market reality data points: 500M raised by agentic startups and 20-30 percent cost reduction and MIT AI Agent Index stats.

Include the Explain It to an Interviewer summary paragraph at the end.

Add the animated timeline SVG where each era lights up sequentially with icons and the capabilities stack visual. About 700 words. Use str_replace to insert at the very beginning.
"@

claude --dangerously-skip-permissions -p $cmd
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "M00 now starts with the complete AI evolution from 1948 to 2026."
Write-Host "Each era has interview-ready answers students can use immediately."
