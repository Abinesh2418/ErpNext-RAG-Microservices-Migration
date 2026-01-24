# Architecture Documentation

## System Overview

AI-Modernization is a comprehensive system that automates the conversion of monolithic codebases into event-driven microservices using AI as the reasoning engine.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (React)                    │
│                     TypeScript Frontend                      │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Python)                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              12-Step Processing Pipeline                │ │
│ │                                                          │ │
│ │  Upload → Scan → Dependency → AI Context →              │ │
│ │  Architecture → User Input → Infrastructure →            │ │
│ │  Conversion → Validation → Output → Run → Simulate      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐            │
│         ▼                  ▼                  ▼             │
│    ┌─────────┐      ┌──────────┐      ┌──────────┐        │
│    │ Scanner │      │ AI Engine│      │Validator │        │
│    │  (AST)  │      │ (OpenAI) │      │ (Syntax) │        │
│    └─────────┘      └──────────┘      └──────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Generated Output                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Service A    │  │ Service B    │  │ Service C    │     │
│  │ (FastAPI)    │  │ (FastAPI)    │  │ (FastAPI)    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘             │
│                            ▼                                 │
│              ┌──────────────────────────┐                   │
│              │    Apache Kafka          │                   │
│              │  (Event Bus)             │                   │
│              │  - Topics                │                   │
│              │  - Event Schemas         │                   │
│              │  - Fault Tolerance       │                   │
│              └──────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## Pipeline Stages

### Stage 1: Analysis (No AI)
**Steps 1-3**: Upload, Scan, Dependency Analysis

- Pure static analysis
- AST-based parsing
- No AI calls
- Fast execution

**Output**:
- `uploads/{project_name}/` - Original code
- `temp/scan_summary.json` - Languages, frameworks
- `temp/dependency_graph.json` - Dependencies, hotspots

### Stage 2: AI Planning
**Steps 4-5**: AI Context, Architecture Design

- Prepares RAG-ready context
- AI designs microservices boundaries
- Identifies domains and events

**Output**:
- `temp/ai_context.json` - Summarized context
- `temp/architecture_plan.json` - Service definitions

### Stage 3: User Configuration
**Step 6**: User Interaction

- 2 questions only:
  1. Target tech stack
  2. Conversion level

**Output**:
- `temp/user_choices.json`

### Stage 4: Generation
**Steps 7-8**: Infrastructure, Code Conversion

- Generates Dockerfiles, docker-compose
- AI converts business logic
- Creates event schemas

**Output**:
- `output/{project_name}/` - Complete microservices

### Stage 5: Validation & Deployment
**Steps 9-12**: Validation, Output View, Run, Simulate

- Validates syntax and contracts
- Provides UI for browsing
- Deploys with Docker Compose
- Demonstrates fault tolerance

## Key Design Decisions

### 1. AST Before AI
- Static analysis first (cheap, fast)
- Only summarized context to AI (cost-effective)
- AI focuses on architectural decisions

### 2. RAG-Ready Context
- Summarized, not raw code
- Structured for vector storage
- Reusable for future queries

### 3. Event-Driven by Default
- Kafka as message broker
- Loose coupling between services
- Fault isolation
- Async communication

### 4. Database-Per-Service
- Each service has its own database
- No shared database
- True service independence

### 5. Validation Before Deployment
- Syntax checking
- Event contract validation
- Dockerfile validation
- Prevents broken deployments

## Technology Choices

### Why FastAPI?
- Modern Python framework
- Automatic API documentation
- Type hints and validation
- High performance
- Async support

### Why Kafka?
- Industry-standard event streaming
- Fault tolerance
- Scalability
- Event replay capability
- Mature ecosystem

### Why OpenAI GPT-4?
- Best-in-class code understanding
- Excellent at architectural reasoning
- Reliable code generation
- Large context window

### Why Docker Compose?
- Simple orchestration
- Easy local development
- Production-like environment
- Service isolation

## Scalability Considerations

### Horizontal Scaling
Each generated service can scale independently:
```yaml
service:
  deploy:
    replicas: 3
```

### Kafka Partitioning
Events can be partitioned for parallel processing:
```
topic: invoice-created
partitions: 10
```

### Database Sharding
Each service manages its own data:
- Service A → Database A
- Service B → Database B
- No cross-service queries

## Security Considerations

### API Security
- CORS configuration
- API key authentication (recommended)
- Rate limiting (recommended)

### Service Security
- Network isolation via Docker
- Environment variable secrets
- No hardcoded credentials

### Event Security
- Kafka ACLs (recommended)
- Schema validation
- Event encryption (optional)

## Monitoring & Observability

### Recommended Additions
1. **Logging**: ELK stack or Loki
2. **Metrics**: Prometheus + Grafana
3. **Tracing**: Jaeger or Zipkin
4. **Alerting**: Alertmanager

### Health Checks
Each service includes:
- `/health` endpoint
- Docker health checks
- Readiness probes

## Future Enhancements

### Planned Features
1. **Real-time UI Updates**: WebSocket for progress
2. **Service Templates**: More language support
3. **Advanced Validation**: Integration tests
4. **CI/CD Integration**: GitHub Actions templates
5. **Cloud Deployment**: K8s manifests
6. **Cost Estimation**: Predict infrastructure costs
7. **Rollback Support**: Version management

### Language Support
Currently: Python (primary)
Planned: Java, JavaScript/TypeScript, PHP, Go

## Performance Metrics

### Typical Conversion Times
- Small project (<100 files): 2-5 minutes
- Medium project (100-500 files): 5-15 minutes
- Large project (500+ files): 15-30 minutes

### Resource Requirements
- CPU: 2+ cores recommended
- RAM: 4GB minimum, 8GB recommended
- Disk: 10GB+ for Docker images
- Network: Stable internet for OpenAI API

## Troubleshooting Guide

### Common Issues

**1. OpenAI Rate Limits**
- Implement exponential backoff
- Cache AI responses
- Use rule-based fallback

**2. Large Codebases**
- Process in batches
- Limit context size
- Focus on hotspots first

**3. Docker Memory**
- Increase Docker Desktop memory
- Reduce service count
- Optimize image sizes

**4. Kafka Connection**
- Check Zookeeper status
- Verify network connectivity
- Review bootstrap servers config

## Testing Strategy

### Unit Tests
- Service logic
- AST parsing
- Context building

### Integration Tests
- API endpoints
- Service communication
- Event flow

### End-to-End Tests
- Complete pipeline
- Generated services
- Failure scenarios

## Deployment Options

### Local Development
- Docker Compose (current)
- Manual service start

### Production
- Kubernetes (recommended)
- Docker Swarm
- Cloud platforms (AWS ECS, GCP Cloud Run)

## Maintenance

### Regular Tasks
1. Update dependencies
2. Monitor OpenAI API costs
3. Clean temp/ and output/ directories
4. Rotate logs
5. Backup configurations

### Version Management
- Semantic versioning
- Changelog maintenance
- API versioning

---
