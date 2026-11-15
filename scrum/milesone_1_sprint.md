
# Sprint Planning 010

## Sprint Information

- **Sprint / Milestone:** 1
- **Sprint dates:** 2026-10-05 - 2026-10-16
- **Planning meeting date:** 2026-10-06
- **Facilitator:** William

### Team Members

- William
- Gurnoor
- Bega
- Nikki

---

## 1. Sprint Goal

**Sprint Goal:**

Deliver the first integrated and testable vertical slice of the restaurant application, allowing customers to discover and search restaurants, view restaurant details and menus, and allowing restaurant information to be created and updated. The implementation will follow the route → service → repository → JSON/CSV architecture and include Pydantic models, automated tests, API documentation, and GitHub Actions CI. A basic frontend will connect to the REST API to demonstrate the core workflow.

---

## 2. Sprint Backlog

| User Story | Description | Priority | Primary Owner | Dependencies |
|---|---|---|---|---|
| #1 – Restaurant Discovery and Search | As a customer, I want to view and search/filter restaurants so that I can discover restaurants that meet my preferences. | High | William | Restaurant data model, repository, and API contract |
| #2 – Restaurant Details and Menu Browsing | As a customer, I want to view a restaurant's details, menu, and menu items so that I can decide what the restaurant offers. | High | Bega | Restaurant discovery endpoints, restaurant identifiers, and menu data structure |
| #3 – Restaurant Management and Persistence | As a restaurant manager, I want to create and update restaurant information so that the restaurant data remains accurate and persists between application restarts. | High | Gurnoor | Agreed data models, repository interfaces, and JSON/CSV persistence strategy |
| #4 – Frontend, Testing, CI, and Integration | As a user and developer, I want a frontend connected to the REST API and an automated test workflow so that the core functionality can be demonstrated and verified reliably. | High | William and Nikki | Stable API contracts, implemented endpoints, testable service/repository layers, and project dependencies |

**Ownership clarification:** Primary ownership means coordinating implementation, tracking progress, and ensuring the story meets its acceptance criteria. Team members may collaborate on implementation, testing, and reviews.

---

## 3. Task Decomposition

### User Story #1 – Restaurant Discovery and Search (William)

- [ ] Define restaurant-listing and search/filter requirements and acceptance criteria.
- [ ] Define Pydantic response models for restaurant data.
- [ ] Implement the restaurant-list endpoint using the route → service → repository architecture.
- [ ] Implement search/filter logic in the service layer.
- [ ] Retrieve restaurant records from the repository rather than hard-coding them in route handlers.
- [ ] Handle empty results, invalid parameters, and other appropriate error scenarios.
- [ ] Add unit tests for restaurant listing and search/filter behavior.
- [ ] Add API/integration tests for successful requests and failure scenarios.
- [ ] Document endpoint parameters, response models, and expected status codes in FastAPI's OpenAPI documentation.
- [ ] Create a feature branch and submit a pull request for teammate review.

### User Story #2 – Restaurant Details and Menu Browsing (Bega)

- [ ] Define requirements for retrieving an individual restaurant and its menu.
- [ ] Agree on the restaurant identifier and menu-item data structures with William and Gurnoor.
- [ ] Implement the restaurant-details endpoint.
- [ ] Implement endpoints for retrieving a restaurant's menu and menu items.
- [ ] Define appropriate Pydantic models for menu and menu-item responses.
- [ ] Retrieve restaurant and menu data through the service and repository layers.
- [ ] Handle invalid restaurant identifiers, missing restaurants, and restaurants with empty menus.
- [ ] Add unit tests for menu retrieval and restaurant-details logic.
- [ ] Add API/integration tests for valid and invalid restaurant identifiers.
- [ ] Document endpoint behavior, response models, and error responses.
- [ ] Create a feature branch and submit a pull request for teammate review.

### User Story #3 – Restaurant Management and Persistence (Gurnoor)

- [ ] Establish the repository interface and JSON/CSV persistence approach for restaurant data.
- [ ] Implement repository operations for retrieving, creating, and updating restaurants.
- [ ] Implement service-layer business logic for creating and updating restaurant information.
- [ ] Define Pydantic request models and validate incoming restaurant data.
- [ ] Implement the create-restaurant endpoint.
- [ ] Implement the update-restaurant endpoint.
- [ ] Ensure restaurant identifiers remain stable and records are saved to persistent storage.
- [ ] Verify that changes remain available after the application is restarted.
- [ ] Handle invalid input, duplicate identifiers where applicable, and attempts to update nonexistent restaurants.
- [ ] Add unit tests for repository and service operations.
- [ ] Add integration/API tests for successful creation, updating, and failure scenarios.
- [ ] Document persistence decisions and update relevant architecture documentation.
- [ ] Create a feature branch and submit a pull request for teammate review.

### User Story #4 – Frontend, Testing, CI, and Integration (William and Nikki)

- [ ] Agree on API contracts and coordinate integration with William, Bega, and Gurnoor.
- [ ] Implement a basic frontend view that retrieves and displays restaurants from the REST API.
- [ ] Implement restaurant selection and a restaurant-details view.
- [ ] Connect the frontend to the menu and menu-item endpoints.
- [ ] Implement the frontend interface for the selected restaurant create/update operation.
- [ ] Ensure restaurant information is fetched from the API rather than hard-coded into the frontend.
- [ ] Implement or verify the application health endpoint.
- [ ] Establish a working pytest suite covering health, restaurant-list operations, repository behavior, and at least one invalid or failure scenario.
- [ ] Configure isolated test data so automated tests do not modify real application data.
- [ ] Configure GitHub Actions to install dependencies and run pytest automatically on pushes and/or pull requests.
- [ ] Integrate feature branches through pull requests and resolve merge conflicts.
- [ ] Verify that all implemented endpoints have appropriate FastAPI/OpenAPI documentation.
- [ ] Run end-to-end checks of the restaurant discovery → details → menu workflow.
- [ ] Verify the frontend's restaurant-management workflow against the API.
- [ ] Update the README, `docs/PROVENANCE.md`, and scrum meeting notes.
- [ ] Verify the final submission requirements, including the `m1-vertical-slice` tag, full commit SHA, and agreed contribution statement.

---

## 4. Dependencies and Integration

| Dependency | Related User Stories | Who is Responsible? | Planned Resolution |
|---|---|---|---|
| Agreement on restaurant and menu data models | #1, #2, #3, #4 | William, Bega, Gurnoor | Agree on field names, identifiers, Pydantic models, and relationships before dependent endpoints are finalized. |
| Repository interfaces and persistent data format | #1, #2, #3 | Gurnoor | Establish consistent repository methods and JSON/CSV storage conventions; share the interfaces with the feature owners. |
| Restaurant identifiers and menu relationships | #1, #2, #3 | William, Bega, Gurnoor | Use stable restaurant identifiers and agree on how menu records reference their parent restaurant. |
| API endpoints and response contracts | #1, #2, #3, #4 | William, Bega, Gurnoor, Nikki | Document endpoint paths, request/response models, status codes, and errors; coordinate changes before frontend integration. |
| Frontend integration with backend | #1, #2, #3, #4 | William and Nikki | Integrate incrementally as endpoints become available and test both successful requests and API failures. |
| Automated testing and CI | #1, #2, #3, #4 | William and Nikki, with support from all owners | Add tests alongside feature implementation and use GitHub Actions to verify the integrated application on pushes and/or pull requests. |
| Final documentation and release | #1, #2, #3, #4 | All team members; William and Nikki coordinate | Update the README, provenance documentation, scrum notes, contribution percentages, and submission metadata before the deadline. |

### Integration Plan

1. **Agree on the API contract:** Confirm restaurant and menu data models, endpoint paths, identifiers, request/response formats, and error-handling conventions.
2. **Develop in feature branches:** Each feature owner implements their assigned story using the agreed layered architecture. Changes are submitted through pull requests, with at least one teammate reviewing each code contribution.
3. **Integrate backend functionality incrementally:** Establish restaurant listing and persistence first, then integrate restaurant details and menu browsing. Implement restaurant creation and updating through the same service and repository architecture.
4. **Connect the frontend:** William and Nikki integrate the frontend with the available REST endpoints, verifying that restaurant data comes from the backend.
5. **Validate continuously:** Run unit and API/integration tests during development. Configure GitHub Actions to install dependencies and execute pytest in a clean environment.
6. **Complete the vertical slice:** Verify the restaurant list → search/filter → restaurant details → menu → menu items workflow, alongside the selected restaurant-management operation.
7. **Prepare the submission:** Review the working version, update documentation, agree on contribution percentages, and create the immutable `m1-vertical-slice` tag with its associated full commit SHA.

---

## 5. Risks and Potential Blockers

| Risk / Blocker | Impact | Planned Action | Owner |
|---|---|---|---|
| Unclear or inconsistent API contracts | Frontend and backend components may not integrate correctly. | Agree on endpoint names, Pydantic models, identifiers, and error responses early; communicate contract changes to dependent owners. | William, Bega, Gurnoor |
| Persistence or repository implementation delays | Restaurant creation, updates, and data retrieval may fail or become inconsistent. | Establish the repository interface and storage format early; test persistence and application restarts with isolated test data. | Gurnoor |
| Integration issues between backend and frontend | The required customer-facing workflow may not be demonstrable. | Integrate endpoints incrementally, test against the actual API, and avoid relying on hard-coded frontend data. | William and Nikki |
| Inadequate test coverage or unstable tests | Defects may go undetected, and CI may fail. | Write tests alongside features, cover success and failure scenarios, isolate test data, and run pytest locally and through GitHub Actions. | All feature owners; William and Nikki coordinate CI |
| Merge conflicts or delayed code reviews | Integration and completion may be delayed. | Use focused feature branches, small pull requests, timely peer reviews, and frequent integration with the working branch. | All team members |
| Incomplete documentation or release preparation | The final submission may not satisfy milestone requirements even if the application works. | Track README, provenance, scrum notes, contribution percentages, repository access, release tagging, and commit SHA as explicit completion tasks. | All team members |

---

## 6. Definition of Done

For work to be considered **DONE**, the team agrees that it must satisfy the following:

- [ ] Requirements and acceptance criteria are satisfied.
- [ ] Business logic is implemented in the appropriate service layer.
- [ ] Persistence is handled through the repository layer.
- [ ] Restaurant data is persisted using JSON and/or CSV and remains available after application restarts.
- [ ] Appropriate Pydantic models are used for API responses and applicable request data.
- [ ] Appropriate unit tests are included.
- [ ] Appropriate integration/API tests are included.
- [ ] The pytest suite covers the health endpoint, restaurant-list operations, repository behavior, and an invalid or failure scenario.
- [ ] Tests pass.
- [ ] Code has been reviewed by at least one teammate through a pull request.
- [ ] Review feedback has been addressed.
- [ ] Documentation has been updated where necessary, including API documentation.
- [ ] GitHub Actions automatically installs dependencies and runs pytest on the configured triggers.
- [ ] The change is integrated into the team's working version.
- [ ] The customer-facing vertical slice can be demonstrated through the frontend and REST API.
- [ ] The selected restaurant create/update operation is implemented and testable.
- [ ] No known critical defects remain.

### Milestone Submission Checks

- [ ] README reflects the milestone implementation.
- [ ] `docs/PROVENANCE.md` is updated.
- [ ] Scrum meeting notes are committed under `scrum/`.
- [ ] GitHub repository and Project Board URLs are ready for submission.
- [ ] Contribution percentages are agreed upon by all team members and add up to 100%.
- [ ] The `m1-vertical-slice` tag identifies the version to be assessed.
- [ ] The full commit SHA associated with that tag is recorded.

---

## 7. Sprint Commitment

Before ending the meeting, each team member should confirm their understanding of the sprint plan.

| Team Member | Initial Responsibilities | Confirmed |
|---|---|---|
| William | Restaurant discovery and search; shared frontend, testing, CI, and integration responsibilities. | ☐ |
| Gurnoor | Restaurant management, repository implementation, JSON/CSV persistence, and create/update functionality. | ☐ |
| Bega | Restaurant details, menu browsing, menu-item retrieval, and associated models and tests. | ☐ |
| Nikki | Shared frontend, testing, CI, and integration responsibilities; support end-to-end validation and documentation. | ☐ |

---

## Meeting Notes

- **Sprint objective:** Complete the first integrated, testable backend vertical slice for restaurant discovery, details, menu browsing, and restaurant management.
- **Architecture decision:** Follow the route → service → repository → JSON/CSV architecture, keeping business logic out of route handlers and avoiding hard-coded restaurant data.
- **API contract:** The team should agree on restaurant and menu data structures, identifiers, endpoint names, response models, and error-handling conventions before dependent components are finalized.
- **Testing strategy:** Use pytest, representative unit and integration/API tests, and isolated test data. GitHub Actions must automatically install dependencies and run the test suite.
- **Collaboration:** All feature work should use meaningful feature branches and pull requests. Each merged feature requires review by another team member, and review feedback should be addressed.
- **Scope control:** Authentication, authorization, carts, checkout, orders, and deliveries are outside the required Milestone 1 scope and should not take priority over the vertical slice.
- **Documentation and submission:** Update the README, `docs/PROVENANCE.md`, and scrum notes. Prepare the required repository and Project Board URLs, contribution statement, `m1-vertical-slice` tag, and associated commit SHA.
- **Follow-up:** Each owner should track implementation, tests, blockers, and review status throughout the sprint. The team should coordinate integration frequently rather than waiting until the deadline.

**Planning note:** Update the meeting notes, commitment confirmations, and task completion checkboxes to reflect what the team actually agreed on and completed.
