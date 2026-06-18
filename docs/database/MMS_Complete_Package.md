# AIRLINE MMS - COMPLETE API & DATABASE PACKAGE
## Quarkus REST API with PostgreSQL + Cosmos DB

---

## TABLE OF CONTENTS
1. [Database Schemas](#step-1-database-schemas)
2. [API Design](#step-2-api-design)
3. [Quarkus Implementation](#step-3-quarkus-implementation)

---

# STEP 1: DATABASE SCHEMAS

## PostgreSQL (Primary Transactional Database)

**File**: `01_postgresql_schema.sql`

### Tables: 38

| # | Table | Type | Purpose |
|---|-------|------|---------|
| 1 | `aircraft_model` | Reference | Aircraft type definitions |
| 2 | `engine_type` | Reference | Engine model definitions |
| 3 | `station` | Reference | Airports & maintenance stations |
| 4 | `aircraft` | Master | Individual aircraft in fleet |
| 5 | `engine` | Master | Individual engine instances |
| 6 | `maintenance_program` | Master | Approved maintenance programs |
| 7 | `check_package` | Master | A/B/C/D check packages |
| 8 | `maintenance_task` | Master | Individual tasks within package |
| 9 | `maintenance_visit` | Transaction | Scheduled/unscheduled visits |
| 10 | `task_card` | Transaction | Executable task instances |
| 11 | `flight_utilization` | Transaction | Daily flight data |
| 12 | `utilization_forecast` | Transaction | Projected utilization |
| 13 | `airworthiness_directive` | Master | Regulatory ADs |
| 14 | `service_bulletin` | Master | OEM bulletins |
| 15 | `adsb_compliance` | Transaction | Per-aircraft compliance |
| 16 | `reliability_metric` | Transaction | Fleet health metrics |
| 17 | `life_limited_part` | Master | LLP tracking by serial |
| 18 | `deferred_defect` | Transaction | MEL/CDL deferrals |
| 19 | `part_master` | Master | Part catalog |
| 20 | `rotable_component` | Master | Serialized components |
| 21 | `pool_allocation` | Transaction | Spare pool distribution |
| 22 | `vendor` | Master | External repair shops |
| 23 | `repair_order` | Transaction | Component repair orders |
| 24 | `shelf_life_material` | Transaction | Expiry-tracked materials |
| 25 | `calibration_tool` | Master | Precision tools |
| 26 | `logbook` | Master | Digital logbooks |
| 27 | `logbook_entry` | Transaction | Individual entries |
| 28 | `certificate_release` | Transaction | CRS documents |
| 29 | `component_history` | Transaction | Lifecycle events |
| 30 | `mechanic` | Master | Maintenance personnel |
| 31 | `mechanic_qualification` | Transaction | Licenses & ratings |
| 32 | `hangar` | Master | Hangar facilities |
| 33 | `hangar_bay` | Master | Individual bays |
| 34 | `hangar_slot` | Transaction | Bay reservations |
| 35 | `app_user` | Master | System users |
| 36 | `warranty_claim` | Transaction | OEM warranty claims |
| 37 | `pbh_contract` | Master | Engine contracts |
| 38 | `lease_agreement` | Master | Aircraft leases |

### Key Features
- UUID primary keys with `gen_random_uuid()`
- JSONB columns for flexible attributes
- Generated columns for computed values (LLP remaining life)
- 42 indexes for query performance
- 2 materialized views: `vw_aircraft_status`, `vw_overdue_checks`
- Full foreign key constraint graph

---

## Cosmos DB (Event Store & Documents)

**File**: `01_cosmosdb_containers.json`

| Container | Partition Key | Purpose |
|-----------|--------------|---------|
| `component-events` | `/componentId` | Back-to-birth traceability events |
| `audit-log` | `/entityType` | Immutable compliance audit trail |
| `maintenance-documents` | `/documentCategory` | OEM bulletins, CRS PDFs, attachments |

---

# STEP 2: API DESIGN

**File**: `02_api_design.md`

## Base URL
```
https://api.mms.airline.com/v1
```

## Authentication
- Bearer Token (JWT)
- Scopes: `mms:read`, `mms:write`, `mms:admin`, `mms:certify`

## Endpoint Summary: 60+ Endpoints

### 1. Aircraft Maintenance Planning & Scheduling

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/planning/check-packages` | READ | List check packages |
| POST | `/planning/check-packages` | WRITE | Create package |
| GET | `/planning/check-packages/{id}` | READ | Get package details |
| PUT | `/planning/check-packages/{id}` | WRITE | Update package |
| POST | `/planning/utilization` | WRITE | Record flight data |
| GET | `/planning/utilization/{aircraftId}` | READ | Utilization history |
| GET | `/planning/utilization/{aircraftId}/accumulated` | READ | Current totals |
| POST | `/planning/utilization/{id}/adjust` | ADMIN | Manual adjustment |
| GET | `/planning/forecasts` | READ | Visit forecasts |
| POST | `/planning/forecasts/generate` | WRITE | Generate forecast |
| GET | `/planning/forecasts/{id}/scenario` | READ | Compare scenarios |
| GET | `/planning/visits/{id}/task-cards` | READ | Visit task cards |
| POST | `/planning/task-cards/{id}/assign` | WRITE | Assign mechanic |
| POST | `/planning/task-cards/{id}/start` | WRITE | Start work |
| POST | `/planning/task-cards/{id}/complete` | WRITE | Complete task |
| POST | `/planning/task-cards/{id}/defer` | WRITE | Defer task |
| GET | `/planning/routing/recommendation` | READ | Route recommendation |
| GET | `/planning/stations/{code}/capabilities` | READ | Station capabilities |

### 2. Reliability & Airworthiness Monitoring

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/reliability/metrics` | READ | Fleet metrics |
| GET | `/reliability/metrics/alerts` | READ | Active alerts |
| POST | `/reliability/metrics/{id}/investigate` | WRITE | Start investigation |
| GET | `/reliability/reports/monthly` | READ | Monthly report |
| GET | `/reliability/ads` | READ | List ADs |
| GET | `/reliability/ads/{id}/applicability` | READ | AD applicability |
| GET | `/reliability/compliance` | READ | Compliance status |
| POST | `/reliability/compliance/{id}/update` | WRITE | Update compliance |
| GET | `/reliability/llp` | READ | Life-limited parts |
| GET | `/reliability/llp/{id}/forecast` | READ | Replacement forecast |
| GET | `/reliability/defects` | READ | Deferred defects |
| POST | `/reliability/defects` | WRITE | Create defect |
| POST | `/reliability/defects/{id}/rectify` | WRITE | Rectify defect |
| POST | `/reliability/defects/{id}/extend` | ADMIN | Extend deferral |

### 3. Component & Inventory Control

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/inventory/rotables` | READ | List rotables |
| GET | `/inventory/rotables/{id}` | READ | Component details |
| POST | `/inventory/rotables/{id}/move` | WRITE | Move component |
| GET | `/inventory/pools` | READ | Pool allocation |
| POST | `/inventory/pools/rebalance` | WRITE | Rebalance pools |
| GET | `/inventory/repair-orders` | READ | List repair orders |
| POST | `/inventory/repair-orders` | WRITE | Create repair order |
| GET | `/inventory/repair-orders/{id}/status` | READ | RO status |
| POST | `/inventory/repair-orders/{id}/receive` | WRITE | Receive repaired |
| GET | `/inventory/vendors/{id}/performance` | READ | Vendor scorecard |
| GET | `/inventory/shelf-life` | READ | Shelf-life materials |
| GET | `/inventory/calibration-tools` | READ | Calibration tools |
| POST | `/inventory/calibration-tools/{id}/calibrate` | WRITE | Record calibration |

### 4. Technical Records & Documentation

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/records/logbooks` | READ | List logbooks |
| GET | `/records/logbooks/{id}/entries` | READ | Logbook entries |
| POST | `/records/logbooks/{id}/entries` | WRITE | Create entry |
| POST | `/records/logbooks/{id}/entries/{eid}/amend` | ADMIN | Amend entry |
| POST | `/records/crs/generate` | CERTIFY | Generate CRS |
| GET | `/records/crs/{id}/validate` | READ | Validate CRS |
| GET | `/records/crs/{id}/download` | READ | Download CRS PDF |
| GET | `/records/traceability/{id}` | READ | Component history |
| GET | `/records/traceability/{id}/pedigree` | READ | Pedigree certificate |
| GET | `/records/traceability/gaps` | READ | Find gaps |

### 5. Workforce & Hangar Resource Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/workforce/mechanics` | READ | List mechanics |
| GET | `/workforce/mechanics/{id}/qualifications` | READ | Qualifications |
| GET | `/workforce/mechanics/{id}/authorization-check` | READ | Auth check |
| GET | `/workforce/qualifications/expiring` | READ | Expiring soon |
| GET | `/workforce/hangars` | READ | List hangars |
| GET | `/workforce/hangars/{id}/bays` | READ | Hangar bays |
| GET | `/workforce/hangars/{id}/schedule` | READ | Schedule (Gantt) |
| POST | `/workforce/hangars/{id}/slots` | WRITE | Reserve slot |
| POST | `/workforce/hangars/{id}/slots/{sid}/release` | WRITE | Release slot |

### 6. Cross-Cutting Operations

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/visits` | READ | List visits |
| POST | `/visits` | WRITE | Create visit |
| GET | `/visits/{id}` | READ | Visit details |
| POST | `/visits/{id}/start` | WRITE | Start visit |
| POST | `/visits/{id}/complete` | WRITE | Complete visit |
| GET | `/aircraft` | READ | List aircraft |
| GET | `/aircraft/{id}` | READ | Aircraft details |
| GET | `/aircraft/{id}/status` | READ | Airworthiness status |
| POST | `/documents/upload` | WRITE | Upload document |
| GET | `/documents/{id}` | READ | Document metadata |
| GET | `/documents/{id}/download` | READ | Download document |
| GET | `/documents/search` | READ | Search documents |
| GET | `/events/component/{id}` | READ | Component events |
| GET | `/audit/{type}/{id}` | READ | Audit trail |
| GET | `/audit/stream` | READ | Real-time events (SSE) |

---

# STEP 3: QUARKUS IMPLEMENTATION

**File**: `03_quarkus_implementation.md`

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Quarkus | 3.15+ |
| Language | Java | 21 |
| ORM | Hibernate ORM with Panache | 6.6+ |
| REST | RESTEasy Reactive | - |
| JSON | Jackson | - |
| Auth | SmallRye JWT | - |
| Validation | Hibernate Validator | - |
| DB Primary | PostgreSQL (Azure SQL) | 16 |
| DB Events | Azure Cosmos DB (NoSQL) | - |
| Docs | SmallRye OpenAPI + Scalar | - |
| Metrics | Micrometer + Prometheus | - |
| Health | SmallRye Health | - |

## Project Structure

```
mms-api/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/airline/mms/
│   │   │       ├── api/                    # REST Resources
│   │   │       │   ├── MaintenanceVisitResource.java
│   │   │       │   ├── TaskCardResource.java
│   │   │       │   ├── AircraftResource.java
│   │   │       │   ├── ReliabilityResource.java
│   │   │       │   ├── InventoryResource.java
│   │   │       │   ├── RecordsResource.java
│   │   │       │   ├── WorkforceResource.java
│   │   │       │   └── DocumentResource.java
│   │   │       ├── service/                # Business Logic
│   │   │       │   ├── MaintenancePlanningService.java
│   │   │       │   ├── TaskCardService.java
│   │   │       │   ├── ReliabilityService.java
│   │   │       │   ├── InventoryService.java
│   │   │       │   ├── RecordsService.java
│   │   │       │   ├── WorkforceService.java
│   │   │       │   └── DocumentService.java
│   │   │       ├── domain/                 # Entities
│   │   │       │   ├── entity/             # JPA Entities
│   │   │       │   └── repository/         # Panache Repositories
│   │   │       ├── dto/                    # DTOs
│   │   │       │   ├── request/
│   │   │       │   ├── response/
│   │   │       │   └── cosmos/             # Cosmos DB DTOs
│   │   │       ├── exception/              # Custom Exceptions
│   │   │       ├── mapper/                 # Exception Mappers
│   │   │       ├── cosmos/                 # Cosmos DB Repositories
│   │   │       ├── security/               # JWT/Auth
│   │   │       └── config/                 # App Config
│   │   └── resources/
│   │       ├── application.properties
│   │       ├── import.sql                  # Seed data
│   │       └── META-INF/
│   │           └── resources/
│   │               └── scalar/
│   │                   └── index.html      # Scalar Docs UI
│   └── test/
│       └── java/
│           └── com/airline/mms/
│               └── api/
│                   └── *ResourceTest.java
├── pom.xml
├── Dockerfile
└── README.md
```

## Key Implementation Files

### pom.xml Dependencies
```xml
<dependencies>
    <!-- REST & JSON -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-rest-jackson</artifactId>
    </dependency>

    <!-- OpenAPI / Scalar -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-smallrye-openapi</artifactId>
    </dependency>

    <!-- Database -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-hibernate-orm-panache</artifactId>
    </dependency>
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-jdbc-postgresql</artifactId>
    </dependency>

    <!-- Cosmos DB -->
    <dependency>
        <groupId>io.quarkiverse.azure</groupId>
        <artifactId>quarkus-azure-cosmos</artifactId>
        <version>1.0.0</version>
    </dependency>

    <!-- Security -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-smallrye-jwt</artifactId>
    </dependency>

    <!-- Validation -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-hibernate-validator</artifactId>
    </dependency>

    <!-- Health & Metrics -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-smallrye-health</artifactId>
    </dependency>
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-micrometer-registry-prometheus</artifactId>
    </dependency>
</dependencies>
```

### application.properties
```properties
# Application
quarkus.application.name=mms-api
quarkus.http.port=8080
quarkus.http.root-path=/api/v1

# Database (PostgreSQL)
quarkus.datasource.db-kind=postgresql
quarkus.datasource.username=${DB_USER:mms_user}
quarkus.datasource.password=${DB_PASSWORD:mms_password}
quarkus.datasource.jdbc.url=${DB_URL:jdbc:postgresql://localhost:5432/mms}
quarkus.datasource.jdbc.max-size=20
quarkus.datasource.jdbc.min-size=5

# Hibernate
quarkus.hibernate-orm.database.generation=validate
quarkus.hibernate-orm.log.sql=false
quarkus.hibernate-orm.packages=com.airline.mms.domain.entity

# Cosmos DB
quarkus.azure.cosmos.endpoint=${COSMOS_ENDPOINT}
quarkus.azure.cosmos.key=${COSMOS_KEY}
quarkus.azure.cosmos.database=mms_events

# JWT
mp.jwt.verify.publickey.location=${JWT_PUBLIC_KEY_URL}
mp.jwt.verify.issuer=${JWT_ISSUER:https://auth.airline.com}
smallrye.jwt.sign.key.location=${JWT_PRIVATE_KEY}

# OpenAPI
quarkus.smallrye-openapi.path=/openapi
quarkus.swagger-ui.path=/swagger-ui
quarkus.swagger-ui.always-include=true

# Logging
quarkus.log.level=INFO
quarkus.log.category."com.airline.mms".level=DEBUG

# CORS
quarkus.http.cors=true
quarkus.http.cors.origins=${CORS_ORIGINS:http://localhost:3000}
quarkus.http.cors.methods=GET,POST,PUT,DELETE,PATCH,OPTIONS
quarkus.http.cors.headers=Authorization,Content-Type,X-Requested-With
```

## Key Code Patterns

### Panache Entity Pattern
```java
@Entity
@Table(name = "aircraft")
public class Aircraft extends PanacheEntityBase {
    @Id @GeneratedValue
    public UUID aircraftId;

    @Column(unique = true, nullable = false)
    public String tailNumber;

    @ManyToOne
    @JoinColumn(name = "model_id")
    public AircraftModel model;

    @Enumerated(EnumType.STRING)
    public AircraftStatus status;

    // Active Record queries
    public static Aircraft findByTailNumber(String tail) {
        return find("tailNumber", tail).firstResult();
    }

    public static List<Aircraft> findActive() {
        return list("status", AircraftStatus.ACTIVE);
    }
}
```

### REST Resource with OpenAPI
```java
@Path("/visits")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@Authenticated
@Tag(name = "Maintenance Visits", description = "Schedule and manage maintenance visits")
public class MaintenanceVisitResource {

    @Inject MaintenancePlanningService service;

    @GET
    @Operation(summary = "List maintenance visits")
    @APIResponse(responseCode = "200", description = "List of visits")
    public Response listVisits(
        @QueryParam("aircraftId") UUID aircraftId,
        @QueryParam("status") String status,
        @QueryParam("page") @DefaultValue("0") int page,
        @QueryParam("size") @DefaultValue("20") int size
    ) {
        return Response.ok(service.listVisits(aircraftId, status, page, size)).build();
    }

    @POST
    @RolesAllowed({"PLANNER", "MANAGER", "ADMIN"})
    @Operation(summary = "Create maintenance visit")
    @APIResponse(responseCode = "201", description = "Visit created")
    @APIResponse(responseCode = "409", description = "Overlapping visit exists")
    public Response createVisit(@Valid @RequestBody CreateMaintenanceVisitRequest request) {
        MaintenanceVisitResponse visit = service.createVisit(request);
        return Response.status(201).entity(visit).build();
    }
}
```

### Service with Business Rules
```java
@ApplicationScoped
public class MaintenancePlanningService {

    @Transactional
    public MaintenanceVisitResponse createVisit(CreateMaintenanceVisitRequest req) {
        // 1. Validate aircraft exists and is active
        Aircraft ac = Aircraft.findById(req.aircraftId());
        if (ac == null) throw new NotFoundException("Aircraft not found");
        if (ac.status != AircraftStatus.ACTIVE) 
            throw new ConflictException("Aircraft must be ACTIVE");

        // 2. Validate check package applies to model
        CheckPackage pkg = CheckPackage.findById(req.packageId());
        if (!pkg.model.modelId.equals(ac.model.modelId))
            throw new ConflictException("Package does not apply to this model");

        // 3. Check for overlapping visits
        if (!MaintenanceVisit.findOverlapping(req.aircraftId(), req.plannedStart(), req.plannedEnd()).isEmpty())
            throw new ConflictException("Overlapping visit exists");

        // 4. Create visit
        MaintenanceVisit visit = new MaintenanceVisit();
        visit.visitReference = generateReference();
        visit.aircraft = ac;
        visit.checkPackage = pkg;
        visit.status = VisitStatus.PLANNED;
        visit.persist();

        // 5. Generate task cards
        MaintenanceTask.findByPackage(pkg.packageId).forEach(task -> {
            TaskCard card = new TaskCard();
            card.visit = visit;
            card.task = task;
            card.cardReference = generateCardRef(visit.visitReference, task.sequenceOrder);
            card.status = TaskCardStatus.PENDING;
            card.persist();
        });

        return toResponse(visit);
    }
}
```

## Running the Application

```bash
# Development (hot reload)
./mvnw quarkus:dev

# Access:
# API:          http://localhost:8080/api/v1
# OpenAPI JSON: http://localhost:8080/api/v1/openapi
# Swagger UI:   http://localhost:8080/api/v1/swagger-ui
# Scalar Docs:  http://localhost:8080/api/v1/scalar
# Health:       http://localhost:8080/api/v1/health
# Metrics:      http://localhost:8080/api/v1/metrics

# Build & Deploy
./mvnw package -Pnative
./mvnw package -Dquarkus.container-image.build=true
```

## Scalar Documentation

Scalar is served at `/api/v1/scalar` with auto-generated OpenAPI spec. Features:
- Interactive request/response testing
- Dark mode default
- JWT token input
- Code generation (curl, Python, JavaScript)
- Request history

---

# DELIVERABLES SUMMARY

| # | File | Description |
|---|------|-------------|
| 1 | `01_postgresql_schema.sql` | Complete PostgreSQL DDL (38 tables, 42 indexes, 2 views) |
| 2 | `01_cosmosdb_containers.json` | Cosmos DB container definitions (3 containers) |
| 3 | `02_api_design.md` | Complete API specification (60+ endpoints) |
| 4 | `03_quarkus_implementation.md` | Quarkus code, services, entities, config |
| 5 | `MMS_Complete_Package.md` | This combined document |

---

*Generated: 2026-06-17 | For: Airline MMS API Development | Framework: Quarkus 3.15+*
