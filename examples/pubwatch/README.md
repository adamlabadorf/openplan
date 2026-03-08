# PubWatch - Researcher Publication Alert System

PubWatch is a system that automates literature collection for researchers by monitoring PubMed for publications matching defined topic profiles.

## Features

- Automated PubMed literature collection based on topic profiles
- Topic profile management with keywords and search parameters
- Weekly paper digests with relevance scoring 
- Email alert system for publication notifications

## Components

1. **PubMed API Integration** - Wrapper around NCBI E-utilities with caching and rate limiting
2. **Profile Management** - System for creating and managing topic profiles  
3. **Relevance Scoring Engine** - Algorithm for ranking papers by relevance to profiles
4. **Digest Generation Service** - Compiles and formats weekly paper digests
5. **Notification System** - Sends email alerts with top papers

## Quick Start

```
# Install dependencies
pip install requests

# Run a fetch for your topic profile  
python pubwatch.py fetch --profile "COVID-19 research"

# List stored papers
python pubwatch.py list --profile "COVID-19 research"
```

## Development

This project uses the OpenSpec workflow for spec-driven development.