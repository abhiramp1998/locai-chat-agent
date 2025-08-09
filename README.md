# Restaurant Booking Conversational Agent

A conversational agent built for the Locai Labs Graduate Forward Deployed Engineer technical assessment. This application provides a chat interface for users to manage restaurant bookings by interacting with a provided mock API.

---

## Features

- **Check Availability:** Ask in natural language about table availability for a specific date and party size.
- **Book a Reservation:** Guide the user through the process of making a new reservation.
- **Check Reservation Details:** Retrieve details of an existing booking using a reference number.
- **Modify Reservation:** Change the party size for an existing booking with built-in validation.
- **Cancel Reservation:** Process a booking cancellation.
- **Contextual Conversation:** The agent remembers the booking reference from a recent query to allow for smoother follow-up actions like "ok, now cancel it."

---

## Tech Stack

- **Language:** Python
- **UI Framework:** Streamlit
- **NLU / Language Model:** Google Gemini API
- **API Interaction:** Requests library

---

## Getting Started

To get a local copy up and running, follow these steps.

### Prerequisites

- Python 3.9 or higher
- A Python environment manager like Conda or venv
- A Google AI Studio API Key

### Setup Instructions

The system consists of two main parts: the **Mock API Server** and this **Conversational Agent**. They must both be running at the same time in separate terminals.

**1. Run the Mock API Server**

First, set up and run the provided backend server.

```bash
# Clone the server repository
git clone [https://github.com/AppellaAl/Restaurant-Booking-Mock-API-Server.git](https://github.com/AppellaAl/Restaurant-Booking-Mock-API-Server.git)

# Navigate into the server directory
cd Restaurant-Booking-Mock-API-Server

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m app
```

The server will now be running on `http://localhost:8547`.

**2. Run the Conversational Agent (This Project)**

In a **new terminal window**, set up and run this Streamlit application.

```bash
# Clone this repository
git clone [https://github.com/your-username/locai-chat-agent.git](https://github.com/your-username/locai-chat-agent.git)

# Navigate into the agent directory
cd locai-chat-agent

# Install dependencies
pip install -r requirements.txt

# Create a .env file for your API key
touch .env

# Add your Google API Key to the new .env file:
# GOOGLE_API_KEY="your-google-api-key"

# Run the Streamlit application
streamlit run app.py
```

The application will open in your web browser.

---

## Design Rationale

This section details the design choices, trade-offs, and considerations made during the development of this agent.

### Frameworks and Tools

I selected **Streamlit** for the user interface. As a Python-native framework, it allowed for a consistent technology stack and enabled rapid development of an interactive front-end. This choice let me concentrate on the core challenge of the assessment—the agent's logic and its integration with the booking API—rather than on complex front-end technologies. My familiarity with the framework and its straightforward hosting options also made it an efficient and practical choice.

The agent's Natural Language Understanding (NLU) is powered by **Google's Gemini API**. It was chosen for its powerful language processing capabilities, which are essential for accurately identifying user intents and extracting entities from unstructured text. The accessibility of the API via a free tier and my prior experience with it made it an effective solution for this project.

### Design Decisions and Trade-offs

The agent's core architecture was a deliberate design choice. It operates as a stateless application that relies on a powerful NLU function to process each user message, rather than using a traditional, stateful dialogue manager.

A stateful approach, such as a rigid state machine, would require explicitly coding the conversational flow. While this offers granular control, it can be brittle and significantly slower to develop.

For this assessment, the chosen stateless architecture was more effective for several key reasons:

- **Rapid Development:** It was significantly faster to implement, allowing the focus to remain on delivering the core user stories required by the assessment within a tight deadline.
- **Flexibility & Robustness:** The agent leverages the LLM's inherent ability to understand conversational context. This makes it more flexible and robust in handling unexpected user queries compared to a rigid, pre-defined flow.
- **Modern, AI-Centric Approach:** This design puts the LLM at the core of the agent's logic, showcasing a modern approach that plays to the primary strengths of today's powerful language models.

### Scalability

To prepare this prototype for a production environment capable of handling thousands of users, I would focus on three core areas:

1.  **Containerization & Auto-Scaling Deployment:** I would first containerize the Streamlit application using **Docker**. This ensures a consistent, portable, and reproducible environment. The container would then be deployed to a managed cloud platform like **AWS Elastic Beanstalk** or **Google Cloud Run**, which automatically handles load balancing and auto-scaling, spinning up more instances during peak traffic and scaling down to save costs during quiet periods.
2.  **Robust Testing & CI/CD:** I would establish a comprehensive, automated testing strategy, including **unit tests** for individual functions and **integration tests** to verify the connection between the agent and the booking API. This test suite would be integrated into a **CI/CD (Continuous Integration/Continuous Deployment)** pipeline using a tool like GitHub Actions to automatically test and deploy new code, ensuring reliability and high code quality.
3.  **Implementing a Caching Layer:** To improve performance and reduce the load on the booking API, I would introduce a caching layer using an in-memory data store like **Redis**. Frequently requested data, such as daily table availability, could be cached for a short period. This would mean that if 1,000 users ask for availability on the same day, we would only need to hit the main API once, providing near-instant responses to the other 999 users.

### Identified Limitations and Potential Improvements

The primary limitation of the current implementation is its simple **conversational memory**. While the agent can remember context for a direct follow-up action (like checking a booking and then immediately cancelling it), it does not maintain a long-term memory across multiple, unrelated turns. A future improvement would be to integrate a more sophisticated state management system to handle more complex dialogues.

A key improvement made during development was the addition of a **proactive validation layer** in the agent. During testing, I discovered a logical flaw in the mock API: the update endpoint would allow a booking's party size to be changed to a number that exceeded the slot's maximum capacity. To mitigate this, the agent was enhanced to first perform its own availability check to verify the new party size is valid _before_ sending the update request. This ensures the agent is robust and maintains data integrity, even when interacting with an external system that has its own limitations.

### Security Considerations

1.  **Secure API Key Management:** The current method of using a `.env` file is appropriate for local development. For a production environment, all secrets, including the `GOOGLE_API_KEY` and the booking server's `API_BEARER_TOKEN`, would be managed using a dedicated secrets management service like **AWS Secrets Manager** or **HashiCorp Vault**. This ensures that credentials are never exposed in the codebase and can be securely rotated and accessed by authorized services only.
2.  **Input Validation and Sanitization:** All user-provided input, especially data that will be sent to the backend API (such as a booking reference), must be rigorously validated on the server side. This is a critical defense against potential injection attacks and ensures that only properly formatted and expected data is processed by the system.
3.  **Rate Limiting and Access Control:** To protect the service from abuse (e.g., automated bots spamming the booking system), a **rate limiter** would be implemented on the agent's endpoint. Furthermore, the system would benefit from **Role-Based Access Control (RBAC)** to create different views and permissions, such as an administrative interface for restaurant managers to manually adjust time slots, separate from the customer-facing chat interface.
