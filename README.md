# Engineering-Solutions-Lab
A collection of hands-on engineering projects, including gRPC services, HTTP proxy microservices, feature engineering pipelines, and production-ready business logic, focused on real-world implementations rather than algorithmic research.

## 1. [http-proxy](http-proxy/) 
Microservice Unified Proxy，a lightweight proxy layer for microservices, designed to provide a consistent and unified interface across different services.
This project simplifies service integration by:
- Exposing a standardized API gateway for all microservices
- Hiding internal service complexity behind a unified proxy
- Enabling easier scaling, monitoring, and maintenance of distributed systems

## 2. [gRPC-server-interfaces](gRPC-server-interfaces/) 
This repository provides gRPC interface definitions that can be used as a shared dependency for building gRPC services or consumed by other projects.
It contains the .proto files and generated stubs required to ensure consistent communication across different services and clients.  
Use cases  
- As a base library for implementing new gRPC services.
- As a dependency for clients that need to call existing gRPC services.
- To maintain a unified contract for inter-service communication.