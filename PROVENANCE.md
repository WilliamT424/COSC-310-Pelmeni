Student: William Tang
Artifact: tests/test_authentication.py, tests/test_authorization.py, tests/auth_support.py, tests/conftest.py
Provenance label: AI-GENERATED
AI tool: Claude
Purpose: Generate the authentication and authorization test suite, including shared fixtures and helpers, for the customer login, JWT handling, and role-based access endpoints.
Influence: Used the AI-generated tests and fixtures as the basis for the test suite, then adjusted variable names and fixtures to match the authentication/authorization implementation.
Validation: Ran the tests locally with pytest and confirmed they passed, then checked that the tests covered valid and invalid logins, missing or invalid tokens, and unauthorized access. Confirmed the CI check passed.
PR or commit: PR #71 (commits 92d92d8, 94656eb)

Student: William Tang
Artifact: app/services/checkout_services.py, app/services/order_services.py, app/repositories/order_repositories.py, app/schemas/order.py, app/main.py (checkout and order endpoints)
Provenance label: AI-ASSISTED
AI tool: Claude
Purpose: Get help designing and implementing checkout and initial order creation, including the order schemas, the checkout service logic, and the order endpoints.
Influence: Used AI suggestions for the structure of the checkout flow and the order schemas, and wrote and modified the code to fit the existing cart, customer, and repository layers.
Validation: Ran the checkout and order tests with pytest, tested the checkout endpoint manually, and checked that created orders were saved to data/orders.json. Confirmed the CI check passed.
PR or commit: PR #70 and PR #78 (commit c5dec31)

Student: William Tang
Artifact: frontend/app.js, frontend/auth.js, frontend/index.html, frontend/style.css
Provenance label: AI-ASSISTED
AI tool: Claude
Purpose: Get help building the frontend for restaurant browsing, login and JWT handling, customer accounts, cart, and checkout.
Influence: Used AI-generated code as a starting point for the pages and API calls, then edited it to match the backend endpoints and the existing page structure.
Validation: Ran the app locally and tested each flow in the browser (login, browsing, cart, checkout), checked that API calls matched the backend responses, and ran tests/test_frontend.py and the CI check.
PR or commit: PR #35, #78, #79 and #82


Student: Gurnoor Chawla
Artifact: app/main.py (customer routes), app/schemas/customer.py, app/services/customer_services.py, app/repositories/customer_repositories.py, tests/test_customer_accounts.py
Provenance label: AI-ASSISTED
AI tool: ChatGPT
Purpose: Help diagnose failures in customer account registration, profile updates, deactivation, and JSON persistence tests.
Influence: Used AI suggestions to trace fixture isolation and serialization issues, clarify how customer records were saved, and improve assertions for nested delivery address updates.
Validation: Reviewed the customer service and repository code and traced the integration-test setup. Local pytest execution was unavailable during that review.
PR or commit: PR #62 (8f1c579)

Student: Gurnoor Chawla
Artifact: frontend/app.js, frontend/index.html, frontend/style.css
Provenance label: AI-ASSISTED
AI tool: ChatGPT (Codex)
Purpose: Bring the existing customer account frontend onto current main and connect it to the authentication API.
Influence: Used Codex to port the existing customer UI and generate the changes for password registration, sign-in, bearer-authenticated profile requests, and account deactivation.
Validation: Verified that the PR diff contained only the three frontend files. JavaScript syntax and the blocking flake8 check passed. Local pytest on Python 3.12 reported 157 passed and 4 expected failures. Browser interaction was not verified.
PR or commit: PR #79 (ed5fab3)

Student: Gurnoor Chawla
Artifact: app/repositories/menu_repositories.py, app/services/menu_services.py, tests/conftest.py, tests/test_cart.py, tests/test_orders.py, tests/test_menu_repository.py
Provenance label: AI-GENERATED
AI tool: ChatGPT (Codex)
Purpose: Move menu-item persistence into the menu repository and prevent concurrent writes within a single server process from losing updates.
Influence: Used Codex to implement repository-owned menu lookup, item ID allocation, and writes. Codex also updated the affected test fixtures and added a concurrent-write regression test.
Validation: The blocking flake8 check passed. Local pytest on Python 3.12 reported 158 passed and 4 pre-existing expected failures. The new test verified that concurrent additions received unique IDs and preserved existing items and unrelated menus. Verified that the branch had no frontend changes.
PR or commit: e5c41ea
9:46 PM


Frontend implementation
Student(s): Nicki Gadirova
Artifact: frontend/app.js, frontend/index.html, frontend/style.css
Label: AI-ASSISTED
AI tool: ChatGPT (GPT-6)
Purpose: Generate and assist with implementing frontend functionality for shopping cart and orders features, including cart display, quantity updates, item removal, checkout, order history, and navigation.
Influence: AI-generated code and implementation suggestions were used and adapted in the frontend implementation
Validation: Manually tested the implemented functionality, including adding items to the cart, updating quantities, removing items, clearing the cart, checkout, and displaying completed orders. Verified that the frontend functionality worked as expected
PR or commit: Commit faea7d9 — Implement frontend cart and orders; PR #85

Pull Request description
Student(s): Nicki Gadirova
Artifact: Pull Request description for the frontend cart and orders implementation
Label: AI-GENERATED
AI tool: ChatGPT (GPT-6)
Purpose: Generate a structured pull request description summarizing the implementation, changes made, testing performed, and relevant notes.
Influence: The generated description was used/adapted to document the changes in the pull request.
Validation: Reviewed the description and verified that the described features and testing accurately reflected the implemented functionality.
PR or commit: PR #85, 78

Pull Request review descriptions/comments
Student(s): Nicki Gadirova
Artifact: Pull Request review descriptions/comments
Label: AI-ASSISTED
AI tool: ChatGPT (GPT-6)
Purpose: Help draft pull request review descriptions and comments, including feedback, explanations, and wording for code reviews.
Influence: AI suggestions were used to help formulate review comments and descriptions.
Validation: Reviewed the generated text before posting and ensured that it accurately reflected the code and my intended feedback.
PR or commit: PR #80, 79, 70

Tests for customer accounts implementation
Student(s): Nicki Gadirova
Artifact: test_customer_accounts.py
Label: AI-ASSISTED
AI tool: ChatGPT (GPT-6)
Purpose: Assist with developing test cases for customer accounts implementation, identifying relevant scenarios and expected behavior, and helping structure tests.
Influence: AI suggestions helped develop the tests, while the final tests were reviewed and incorporated into the project.
Validation: Reviewed the tests, ran them, and verified that their results were consistent with the expected behavior
PR or commit: PR #62
