# 🦄 The HungryUnicorn Booking Agent

A conversational agent for the Locai Labs Graduate Forward Deployed Engineer technical assessment. This chatbot, built with Streamlit and Google's Gemini, handles restaurant bookings by interacting with a mock API.

---

## ✨ Features

* **Check Availability:** Ask in natural language about table availability for a specific date and party size.
* **Make Bookings:** Guide the user through the process of making a new reservation.
* **Check Reservations:** Retrieve details of an existing booking using a reference number.
* **Modify & Cancel:** Support for changing or cancelling existing reservations.

---

## 🛠️ Tech Stack

* **Language:** Python 3.9+
* **UI Framework:** Streamlit
* **NLU / Language Model:** Google Gemini API
* **API Interaction:** Requests

---

## 🚀 Getting Started

### Prerequisites

* Python 3.9 or higher
* Conda or another virtual environment tool
* A Google AI Studio API Key

### Setup Instructions

```bash
# Clone this repository
git clone [https://github.com/abhiramp1998/locai-chat-agent.git]

# Navigate into the agent directory
cd locai-chat-agent

# Install dependencies
pip install -r requirements.txt

# Create a .env file and add your Google API Key:
# GOOGLE_API_KEY="your-google-api-key"

# Run the Streamlit application
streamlit run app.py