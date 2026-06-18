
# ============================================================
# MMS API DESIGN
# Quarkus REST API with OpenAPI / Scalar Documentation
# ============================================================

## Base URL
```
https://api.mms.airline.com/v1
```

## Authentication
- **Type**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <token>`
- **Scopes**: `mms:read`, `mms:write`, `mms:admin`, `mms:certify`

## Content-Type
- `application/json` (default)
- `multipart/form-data` (for document uploads)

---

# 1. AIRCRAFT MAINTENANCE PLANNING & SCHEDULING

## 1.1 Maintenance Program Check Management

### GET /planning/check-packages
**Description**: List all maintenance check packages with filters
**Query Params**:
- `modelId` (UUID) - Filter by aircraft model
- `checkType` (enum: A_CHECK, B_CHECK, C_CHECK, D_CHECK)
- `isActive` (boolean)
- `page` (int, default: 0)
- `size` (int, default: 20)
**Response**: `200 OK` → Page<CheckPackageResponse>
**Use Case**: Planner views available check packages for scheduling

### GET /planning/check-packages/{packageId}
**Description**: Get single check package with tasks
**Path Params**: `packageId` (UUID)
**Response**: `200 OK` → CheckPackageDetailResponse (includes task list)
**Use Case**: Planner reviews check scope before scheduling

### POST /planning/check-packages
**Description**: Create new check package
**Body**: CheckPackageRequest
**Response**: `201 Created` → CheckPackageResponse
**Auth**: `mms:write`
**Use Case**: Engineering creates new maintenance program revision

### PUT /planning/check-packages/{packageId}
**Description**: Update check package (creates new version)
**Path Params**: `packageId` (UUID)
**Body**: CheckPackageRequest
**Response**: `200 OK` → CheckPackageResponse (new version)
**Auth**: `mms:write`
**Use Case**: Engineering revises check intervals per manufacturer update

---

## 1.2 Flight Hour & Cycle Accumulation Tracker

### POST /planning/utilization
**Description**: Record daily flight utilization data
**Body**: FlightUtilizationRequest
**Response**: `201 Created` → FlightUtilizationResponse
**Auth**: `mms:write`
**Use Case**: Flight ops system pushes daily block hours/cycles

### GET /planning/utilization/{aircraftId}
**Description**: Get utilization history for an aircraft
**Path Params**: `aircraftId` (UUID)
**Query Params**:
- `startDate` (date)
- `endDate` (date)
- `page` (int)
- `size` (int)
**Response**: `200 OK` → Page<FlightUtilizationResponse>
**Use Case**: Reliability engineer reviews utilization trends

### GET /planning/utilization/{aircraftId}/accumulated
**Description**: Get current accumulated flight hours/cycles
**Path Params**: `aircraftId` (UUID)
**Response**: `200 OK` → AccumulatedUtilizationResponse
**Use Case**: Planner checks trigger thresholds for next check

### POST /planning/utilization/{utilizationId}/adjust
**Description**: Manual adjustment with justification
**Path Params**: `utilizationId` (UUID)
**Body**: UtilizationAdjustmentRequest (adjustmentValue, reasonCode, justification)
**Response**: `200 OK` → FlightUtilizationResponse
**Auth**: `mms:admin`
**Use Case**: Technical records officer corrects data discrepancy

---

## 1.3 Maintenance Visit Forecasting Engine

### GET /planning/forecasts
**Description**: Get maintenance visit forecasts for fleet
**Query Params**:
- `aircraftId` (UUID, optional)
- `periodStart` (date)
- `periodEnd` (date)
- `confidenceLevel` (enum: HIGH, MEDIUM, LOW)
**Response**: `200 OK` → List<MaintenanceForecastResponse>
**Use Case**: Fleet manager plans hangar capacity 12 months ahead

### POST /planning/forecasts/generate
**Description**: Generate new forecast based on parameters
**Body**: ForecastGenerationRequest (scenario parameters)
**Response**: `202 Accepted` → ForecastJobResponse (async job ID)
**Auth**: `mms:write`
**Use Case**: Planner models fleet expansion impact on maintenance

### GET /planning/forecasts/{forecastId}/scenario
**Description**: Compare forecast scenarios
**Path Params**: `forecastId` (UUID)
**Query Params**: `compareWith` (UUID of another forecast)
**Response**: `200 OK` → ForecastComparisonResponse
**Use Case**: Management evaluates different fleet utilization plans

---

## 1.4 Task Card Generation & Sequencing

### GET /planning/visits/{visitId}/task-cards
**Description**: Get all task cards for a maintenance visit
**Path Params**: `visitId` (UUID)
**Query Params**:
- `status` (enum filter)
- `assignedMechanicId` (UUID)
**Response**: `200 OK` → List<TaskCardResponse>
**Use Case**: Hangar supervisor views daily work assignments

### POST /planning/visits/{visitId}/task-cards/{taskCardId}/assign
**Description**: Assign task card to mechanic
**Path Params**: `visitId` (UUID), `taskCardId` (UUID)
**Body**: TaskCardAssignmentRequest (mechanicId)
**Response**: `200 OK` → TaskCardResponse
**Auth**: `mms:write`
**Use Case**: Supervisor assigns qualified mechanic to task

### POST /planning/visits/{visitId}/task-cards/{taskCardId}/complete
**Description**: Mark task card as complete with findings
**Path Params**: `visitId` (UUID), `taskCardId` (UUID)
**Body**: TaskCardCompletionRequest (actualHours, findings, signOff)
**Response**: `200 OK` → TaskCardResponse
**Auth**: `mms:write`
**Use Case**: Mechanic completes task and signs off

### POST /planning/visits/{visitId}/task-cards/{taskCardId}/defer
**Description**: Defer task card with reason
**Path Params**: `visitId` (UUID), `taskCardId` (UUID)
**Body**: TaskCardDeferralRequest (reason, deferredToVisitId)
**Response**: `200 OK` → TaskCardResponse
**Auth**: `mms:write`
**Use Case**: Task cannot be completed; moved to next visit

---

## 1.5 Line vs Base Maintenance Routing

### GET /planning/routing/recommendation
**Description**: Get routing recommendation for tasks
**Query Params**:
- `taskIds` (List<UUID>)
- `aircraftId` (UUID)
- `currentStation` (string)
**Response**: `200 OK` → RoutingRecommendationResponse
**Use Case**: Controller decides if defect can be fixed at gate or needs hangar

### GET /planning/stations/{stationCode}/capabilities
**Description**: Get maintenance capabilities of a station
**Path Params**: `stationCode` (string)
**Response**: `200 OK` → StationCapabilityResponse
**Use Case**: Network ops routes aircraft to capable station

---

# 2. RELIABILITY & AIRWORTHINESS MONITORING

## 2.1 Fleet Reliability Dashboard

### GET /reliability/metrics
**Description**: Get reliability metrics for fleet
**Query Params**:
- `metricType` (enum: MTBUR, MTBF, DEFECT_RATE, DELAY_RATE, CANCELLATION_RATE)
- `aircraftModelId` (UUID)
- `componentCategory` (string)
- `periodStart` (date)
- `periodEnd` (date)
**Response**: `200 OK` → List<ReliabilityMetricResponse>
**Use Case**: Reliability engineer reviews fleet health trends

### GET /reliability/metrics/alerts
**Description**: Get active reliability alerts
**Query Params**:
- `severity` (enum: LOW, MEDIUM, HIGH, CRITICAL)
- `investigationStatus` (enum: OPEN, IN_PROGRESS, CLOSED)
**Response**: `200 OK` → List<ReliabilityAlertResponse>
**Use Case**: Safety manager reviews open alert investigations

### POST /reliability/metrics/{metricId}/investigate
**Description**: Start investigation on reliability alert
**Path Params**: `metricId` (UUID)
**Body**: InvestigationRequest (assignedTo, priority)
**Response**: `200 OK` → ReliabilityMetricResponse
**Auth**: `mms:write`
**Use Case**: Quality manager assigns investigation team

### GET /reliability/reports/monthly
**Description**: Generate monthly reliability report
**Query Params**:
- `year` (int)
- `month` (int)
- `format` (enum: PDF, EXCEL, JSON)
**Response**: `200 OK` → ReportDownloadResponse (URL)
**Use Case**: Compliance officer submits report to regulator

---

## 2.2 Airworthiness Directive & Service Bulletin Tracker

### GET /reliability/ads
**Description**: List all airworthiness directives
**Query Params**:
- `authority` (enum: EASA, FAA, CAAC, TCCA)
- `status` (enum: ACTIVE, SUPERSEDED, CANCELLED)
- `affectedModelId` (UUID)
**Response**: `200 OK` → Page<AirworthinessDirectiveResponse>
**Use Case**: Airworthiness engineer reviews new ADs

### GET /reliability/ads/{adId}/applicability
**Description**: Check AD applicability to fleet
**Path Params**: `adId` (UUID)
**Response**: `200 OK` → List<ADApplicabilityResponse> (per aircraft)
**Use Case**: Compliance officer identifies affected aircraft

### GET /reliability/compliance
**Description**: Get compliance status across fleet
**Query Params**:
- `aircraftId` (UUID)
- `complianceStatus` (enum)
- `overdueOnly` (boolean)
**Response**: `200 OK` → List<ComplianceStatusResponse>
**Use Case**: Manager reviews fleet compliance health

### POST /reliability/compliance/{complianceId}/update
**Description**: Update compliance status
**Path Params**: `complianceId` (UUID)
**Body**: ComplianceUpdateRequest (status, completionDate, method)
**Response**: `200 OK` → ComplianceStatusResponse
**Auth**: `mms:write`
**Use Case**: Engineer records AD embodiment completion

---

## 2.3 Life-Limited Part Monitoring

### GET /reliability/llp
**Description**: List life-limited parts
**Query Params**:
- `engineId` (UUID)
- `status` (enum)
- `thresholdAlert` (boolean) - Only parts below alert threshold
**Response**: `200 OK` → List<LifeLimitedPartResponse>
**Use Case**: Component engineer reviews upcoming replacements

### GET /reliability/llp/{llpId}/forecast
**Description**: Get replacement forecast for LLP
**Path Params**: `llpId` (UUID)
**Query Params**: `projectionMonths` (int, default: 12)
**Response**: `200 OK` → LLPReplacementForecastResponse
**Use Case**: Planner schedules shop visit around LLP limits

---

## 2.4 Deferred Defect Management

### GET /reliability/defects
**Description**: List deferred defects
**Query Params**:
- `aircraftId` (UUID)
- `status` (enum: ACTIVE, EXPIRED, RECTIFIED, EXTENDED)
- `expiringWithinDays` (int)
**Response**: `200 OK` → List<DeferredDefectResponse>
**Use Case**: Line manager reviews active deferrals before flight

### POST /reliability/defects
**Description**: Create new deferred defect
**Body**: DeferredDefectRequest (aircraftId, melReference, description, restrictions)
**Response**: `201 Created` → DeferredDefectResponse
**Auth**: `mms:write`
**Use Case**: Mechanic defers non-critical defect per MEL

### POST /reliability/defects/{defectId}/rectify
**Description**: Mark defect as rectified
**Path Params**: `defectId` (UUID)
**Body**: DefectRectificationRequest (taskCardId, rectifiedBy)
**Response**: `200 OK` → DeferredDefectResponse
**Auth**: `mms:write`
**Use Case**: Mechanic completes rectification work

### POST /reliability/defects/{defectId}/extend
**Description**: Request extension on deferred defect
**Path Params**: `defectId` (UUID)
**Body**: DefectExtensionRequest (extensionDays, justification, authorizedBy)
**Response**: `200 OK` → DeferredDefectResponse
**Auth**: `mms:admin`
**Use Case**: Manager approves extension for parts availability delay

---

# 3. COMPONENT & INVENTORY CONTROL

## 3.1 Rotable & Repairable Pool Management

### GET /inventory/rotables
**Description**: List rotable components
**Query Params**:
- `partMasterId` (UUID)
- `status` (enum)
- `stationId` (UUID)
- `serialNumber` (string)
**Response**: `200 OK` → Page<RotableComponentResponse>
**Use Case**: Inventory controller locates spare component

### GET /inventory/rotables/{componentId}
**Description**: Get rotable with full history
**Path Params**: `componentId` (UUID)
**Response**: `200 OK` → RotableComponentDetailResponse
**Use Case**: Engineer reviews component pedigree before installation

### POST /inventory/rotables/{componentId}/move
**Description**: Move component between stations
**Path Params**: `componentId` (UUID)
**Body**: ComponentMoveRequest (toStationId, reason, authorizedBy)
**Response**: `200 OK` → RotableComponentResponse
**Auth**: `mms:write`
**Use Case**: Controller transfers spare to line station

### GET /inventory/pools
**Description**: Get pool allocation across network
**Query Params**:
- `partMasterId` (UUID)
- `stationId` (UUID)
**Response**: `200 OK` → List<PoolAllocationResponse>
**Use Case**: Supply chain manager reviews stock distribution

### POST /inventory/pools/rebalance
**Description**: Trigger pool rebalancing analysis
**Body**: PoolRebalanceRequest (stationIds, partMasterIds)
**Response**: `202 Accepted` → RebalanceJobResponse
**Auth**: `mms:write`
**Use Case**: Manager optimizes spare distribution across stations

---

## 3.2 Repair Order & Shop Visit Coordination

### GET /inventory/repair-orders
**Description**: List repair orders
**Query Params**:
- `componentId` (UUID)
- `vendorId` (UUID)
- `status` (enum)
- `overdueOnly` (boolean)
**Response**: `200 OK` → Page<RepairOrderResponse>
**Use Case**: Component manager tracks shop visit status

### POST /inventory/repair-orders
**Description**: Create new repair order
**Body**: RepairOrderRequest (componentId, vendorId, issueDescription, promisedTat)
**Response**: `201 Created` → RepairOrderResponse
**Auth**: `mms:write`
**Use Case**: Controller sends unserviceable component to repair shop

### GET /inventory/repair-orders/{roId}/status
**Description**: Get repair order status with timeline
**Path Params**: `roId` (UUID)
**Response**: `200 OK` → RepairOrderStatusResponse
**Use Case**: Planner checks if component will return before next visit

### POST /inventory/repair-orders/{roId}/receive
**Description**: Receive repaired component back
**Path Params**: `roId` (UUID)
**Body**: RepairReceiptRequest (receivedDate, actualCost, certificateRef)
**Response**: `200 OK` → RepairOrderResponse
**Auth**: `mms:write`
**Use Case**: Storekeeper checks in serviceable component

### GET /inventory/vendors/{vendorId}/performance
**Description**: Get vendor performance scorecard
**Path Params**: `vendorId` (UUID)
**Query Params**: `periodMonths` (int, default: 12)
**Response**: `200 OK` → VendorPerformanceResponse
**Use Case**: Procurement manager evaluates repair shop performance

---

## 3.3 Shelf-Life & Calibration Control

### GET /inventory/shelf-life
**Description**: List shelf-life materials
**Query Params**:
- `stationId` (UUID)
- `status` (enum)
- `expiringWithinDays` (int)
**Response**: `200 OK` → List<ShelfLifeMaterialResponse>
**Use Case**: Storekeeper identifies materials to use before expiry

### GET /inventory/calibration-tools
**Description**: List calibration tools
**Query Params**:
- `stationId` (UUID)
- `status` (enum)
- `dueWithinDays` (int)
**Response**: `200 OK` → List<CalibrationToolResponse>
**Use Case**: Quality inspector ensures tools are current

### POST /inventory/calibration-tools/{toolId}/calibrate
**Description**: Record calibration completion
**Path Params**: `toolId` (UUID)
**Body**: CalibrationRecordRequest (calibrationDate, certificateId, performedBy)
**Response**: `200 OK` → CalibrationToolResponse
**Auth**: `mms:write`
**Use Case**: Inspector records tool calibration

---

# 4. TECHNICAL RECORDS & DOCUMENTATION

## 4.1 Digital Logbook Management

### GET /records/logbooks
**Description**: List logbooks
**Query Params**:
- `aircraftId` (UUID)
- `engineId` (UUID)
- `logbookType` (enum)
**Response**: `200 OK` → List<LogbookResponse>
**Use Case**: Records officer locates correct logbook

### GET /records/logbooks/{logbookId}/entries
**Description**: Get logbook entries
**Path Params**: `logbookId` (UUID)
**Query Params**:
- `entryType` (enum)
- `startDate` (date)
- `endDate` (date)
- `page` (int)
- `size` (int)
**Response**: `200 OK` → Page<LogbookEntryResponse>
**Use Case**: Auditor reviews maintenance history

### POST /records/logbooks/{logbookId}/entries
**Description**: Create new logbook entry
**Path Params**: `logbookId` (UUID)
**Body**: LogbookEntryRequest (entryType, description, flightHours, cycles, digitalSignature)
**Response**: `201 Created` → LogbookEntryResponse
**Auth**: `mms:write`
**Use Case**: Licensed engineer makes maintenance entry

### POST /records/logbooks/{logbookId}/entries/{entryId}/amend
**Description**: Amend existing logbook entry
**Path Params**: `logbookId` (UUID), `entryId` (UUID)
**Body**: LogbookAmendmentRequest (amendedDescription, reason)
**Response**: `200 OK` → LogbookEntryResponse
**Auth**: `mms:admin`
**Use Case**: Supervisor corrects entry error with full traceability

---

## 4.2 Maintenance Release & Certificate Generation

### POST /records/crs/generate
**Description**: Generate Certificate of Release to Service
**Body**: CRSGenerationRequest (visitId, certifyingStaffId, scopeDescription)
**Response**: `201 Created` → CertificateReleaseResponse
**Auth**: `mms:certify`
**Use Case**: Certifying staff signs off completed maintenance

### GET /records/crs/{crsId}/validate
**Description**: Validate CRS before flight
**Path Params**: `crsId` (UUID)
**Response**: `200 OK` → CRSValidationResponse (isValid, blockingIssues)
**Use Case**: Flight dispatch verifies aircraft is released

### GET /records/crs/{crsId}/download
**Description**: Download CRS as PDF
**Path Params**: `crsId` (UUID)
**Response**: `200 OK` → File (application/pdf)
**Use Case**: Ground handling prints CRS for flight folder

---

## 4.3 Back-to-Birth Traceability

### GET /records/traceability/{componentId}
**Description**: Get complete component history
**Path Params**: `componentId` (UUID)
**Query Params**:
- `includeDocuments` (boolean)
- `format` (enum: SUMMARY, DETAILED, TIMELINE)
**Response**: `200 OK` → ComponentTraceabilityResponse
**Use Case**: Buyer inspects component history before purchase

### GET /records/traceability/{componentId}/pedigree
**Description**: Generate pedigree certificate
**Path Params**: `componentId` (UUID)
**Response**: `200 OK` → PedigreeCertificateResponse (PDF URL)
**Use Case**: Resale or lease return documentation

### GET /records/traceability/gaps
**Description**: Find traceability gaps in component history
**Query Params**:
- `componentId` (UUID, optional - if null, checks all)
**Response**: `200 OK` → List<TraceabilityGapResponse>
**Use Case**: Quality auditor identifies missing history before audit

---

# 5. WORKFORCE & HANGAR RESOURCE MANAGEMENT

## 5.1 Mechanic Qualification & Authorization Matrix

### GET /workforce/mechanics
**Description**: List mechanics
**Query Params**:
- `stationId` (UUID)
- `employmentStatus` (enum)
- `isCertifyingStaff` (boolean)
- `licenseType` (enum)
**Response**: `200 OK` → Page<MechanicResponse>
**Use Case**: Manager reviews workforce availability

### GET /workforce/mechanics/{mechanicId}/qualifications
**Description**: Get mechanic qualifications
**Path Params**: `mechanicId` (UUID)
**Response**: `200 OK` → List<MechanicQualificationResponse>
**Use Case**: Supervisor verifies mechanic can perform task

### GET /workforce/mechanics/{mechanicId}/authorization-check
**Description**: Check if mechanic is authorized for task
**Path Params**: `mechanicId` (UUID)
**Query Params**:
- `taskId` (UUID)
- `aircraftType` (string)
**Response**: `200 OK` → AuthorizationCheckResponse (isAuthorized, missingQualifications)
**Use Case**: System prevents unqualified mechanic assignment

### GET /workforce/qualifications/expiring
**Description**: Get qualifications expiring soon
**Query Params**:
- `withinDays` (int, default: 30)
- `licenseType` (enum)
**Response**: `200 OK` → List<QualificationExpiryResponse>
**Use Case**: HR schedules recurrent training

---

## 5.2 Hangar Capacity & Slot Planning

### GET /workforce/hangars
**Description**: List hangars
**Query Params**:
- `stationId` (UUID)
- `hasAvailability` (boolean)
- `maxAircraftSize` (enum)
**Response**: `200 OK` → List<HangarResponse>
**Use Case**: Planner finds available hangar for C-check

### GET /workforce/hangars/{hangarId}/bays
**Description**: Get hangar bays with status
**Path Params**: `hangarId` (UUID)
**Response**: `200 OK` → List<HangarBayResponse>
**Use Case**: Supervisor views bay occupancy

### GET /workforce/hangars/{hangarId}/schedule
**Description**: Get hangar schedule (Gantt view data)
**Path Params**: `hangarId` (UUID)
**Query Params**:
- `startDate` (date)
- `endDate` (date)
**Response**: `200 OK` → HangarScheduleResponse
**Use Case**: Planner visualizes hangar utilization

### POST /workforce/hangars/{hangarId}/slots
**Description**: Reserve hangar slot
**Path Params**: `hangarId` (UUID)
**Body**: HangarSlotReservationRequest (bayId, visitId, slotStart, slotEnd, tooling)
**Response**: `201 Created` → HangarSlotResponse
**Auth**: `mms:write`
**Use Case**: Planner books bay for maintenance visit

### POST /workforce/hangars/{hangarId}/slots/{slotId}/release
**Description**: Release hangar slot early
**Path Params**: `hangarId` (UUID), `slotId` (UUID)
**Body**: SlotReleaseRequest (reason, releasedBy)
**Response**: `200 OK` → HangarSlotResponse
**Auth**: `mms:write`
**Use Case**: Aircraft released early; bay freed for next visit

---

# 6. CROSS-CUTTING / SUPPORTING

## 6.1 Maintenance Visits (Aggregate Operations)

### GET /visits
**Description**: List maintenance visits
**Query Params**:
- `aircraftId` (UUID)
- `status` (enum)
- `stationId` (UUID)
- `checkType` (enum)
- `startDate` (date)
- `endDate` (date)
**Response**: `200 OK` → Page<MaintenanceVisitResponse>
**Use Case**: Controller reviews all active visits

### POST /visits
**Description**: Create new maintenance visit
**Body**: MaintenanceVisitRequest (aircraftId, packageId, plannedDates, stationId)
**Response**: `201 Created` → MaintenanceVisitResponse
**Auth**: `mms:write`
**Use Case**: Planner schedules C-check for aircraft

### GET /visits/{visitId}
**Description**: Get visit with full details
**Path Params**: `visitId` (UUID)
**Response**: `200 OK` → MaintenanceVisitDetailResponse (includes task cards, findings, CRS)
**Use Case**: Manager reviews visit progress

### POST /visits/{visitId}/start
**Description**: Start maintenance visit
**Path Params**: `visitId` (UUID)
**Body**: VisitStartRequest (actualStartDate, assignedTeam)
**Response**: `200 OK` → MaintenanceVisitResponse
**Auth**: `mms:write`
**Use Case**: Aircraft enters hangar; work begins

### POST /visits/{visitId}/complete
**Description**: Complete maintenance visit
**Path Params**: `visitId` (UUID)
**Body**: VisitCompletionRequest (actualEndDate, findingsSummary)
**Response**: `200 OK` → MaintenanceVisitResponse
**Auth**: `mms:write`
**Use Case**: All tasks complete; ready for CRS generation

---

## 6.2 Aircraft (Aggregate Operations)

### GET /aircraft
**Description**: List aircraft in fleet
**Query Params**:
- `status` (enum)
- `modelId` (UUID)
- `currentLocation` (string)
**Response**: `200 OK` → Page<AircraftResponse>
**Use Case**: Operations views fleet status

### GET /aircraft/{aircraftId}
**Description**: Get aircraft with full status
**Path Params**: `aircraftId` (UUID)
**Response**: `200 OK` → AircraftDetailResponse (includes engines, active defects, pending compliance)
**Use Case**: Dispatcher checks aircraft airworthiness before flight

### GET /aircraft/{aircraftId}/status
**Description**: Get aircraft airworthiness status
**Path Params**: `aircraftId` (UUID)
**Response**: `200 OK` → AircraftAirworthinessResponse (isAirworthy, blockingItems)
**Use Case**: Flight operations system checks if aircraft can fly

---

## 6.3 Documents (Cosmos DB Integration)

### POST /documents/upload
**Description**: Upload maintenance document
**Content-Type**: multipart/form-data
**Form Data**:
- `file` (File)
- `documentCategory` (enum: crs_certificate, oem_bulletin, task_attachment, repair_certificate)
- `aircraftId` (UUID, optional)
- `visitId` (UUID, optional)
- `tags` (List<string>)
**Response**: `201 Created` → DocumentUploadResponse
**Auth**: `mms:write`
**Use Case**: Mechanic uploads CRS PDF

### GET /documents/{documentId}
**Description**: Get document metadata
**Path Params**: `documentId` (UUID)
**Response**: `200 OK` → DocumentMetadataResponse
**Use Case**: System retrieves document info

### GET /documents/{documentId}/download
**Description**: Download document
**Path Params**: `documentId` (UUID)
**Response**: `200 OK` → File (various MIME types)
**Use Case**: User downloads OEM bulletin

### GET /documents/search
**Description**: Search documents by content (OCR)
**Query Params**:
- `query` (string)
- `documentCategory` (enum)
- `aircraftId` (UUID)
**Response**: `200 OK` → List<DocumentSearchResult>
**Use Case**: AI agent searches for specific procedure in documents

---

## 6.4 Events / Audit (Cosmos DB Integration)

### GET /events/component/{componentId}
**Description**: Get component lifecycle events
**Path Params**: `componentId` (UUID)
**Query Params**:
- `eventType` (enum)
- `startDate` (date)
- `endDate` (date)
**Response**: `200 OK` → List<ComponentEventResponse>
**Use Case**: Trace component history

### GET /audit/{entityType}/{entityId}
**Description**: Get audit trail for entity
**Path Params**: `entityType` (string), `entityId` (UUID)
**Query Params**:
- `action` (enum: CREATE, UPDATE, DELETE, STATUS_CHANGED)
- `startDate` (date)
- `endDate` (date)
**Response**: `200 OK` → List<AuditLogEntryResponse>
**Use Case**: Regulator reviews who changed what and when

### GET /audit/stream
**Description**: Stream real-time audit events (SSE)
**Query Params**:
- `entityTypes` (List<string>)
**Response**: `text/event-stream`
**Use Case**: AI agent listens for real-time changes

---

# ERROR RESPONSES

All endpoints return standardized error responses:

```json
{
  "timestamp": "2026-06-17T14:30:00Z",
  "status": 400,
  "error": "BAD_REQUEST",
  "message": "Validation failed: field 'plannedEndDate' must be after 'plannedStartDate'",
  "path": "/api/v1/planning/visits",
  "traceId": "abc123-def456"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad Request - Validation error |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Business rule violation (e.g., mechanic not qualified) |
| 422 | Unprocessable Entity - Semantic error (e.g., CRS cannot be generated with open defects) |
| 500 | Internal Server Error |

---

# PAGINATION

All list endpoints support pagination:

```json
{
  "content": [...],
  "page": 0,
  "size": 20,
  "totalElements": 156,
  "totalPages": 8,
  "first": true,
  "last": false
}
```

Query params: `page`, `size`, `sort` (e.g., `sort=createdAt,desc`)
