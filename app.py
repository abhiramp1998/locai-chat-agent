import streamlit as st
import requests
import os

# --- Configuration ---
API_BASE_URL = "http://localhost:8547/api/ConsumerApi/v1/Restaurant/TheHungryUnicorn"
API_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8"

# --- API Functions ---

def check_restaurant_availability(date: str, party_size: int):
    """Calls the mock API to check for available time slots."""
    endpoint = f"{API_BASE_URL}/AvailabilitySearch"
    headers = {
        "Authorization": f"Bearer {API_BEARER_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "VisitDate": date,
        "PartySize": party_size,
        "ChannelCode": "ONLINE"
    }
    
    try:
        response = requests.post(endpoint, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

# --- Streamlit App ---

st.set_page_config(page_title="The HungryUnicorn Bookings", page_icon="🦄")
st.title("🦄 The HungryUnicorn Booking Agent")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you book a table at The HungryUnicorn?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What would you like to do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Assistant's Turn ---
    with st.chat_message("assistant"):
        with st.spinner("Checking for tables..."):
            # For this first test, we ignore the user's prompt and use fixed values
            availability_data = check_restaurant_availability(date="2025-08-09", party_size=2)
            
            if availability_data and availability_data.get("available_slots"):
                available_times = [slot["time"] for slot in availability_data["available_slots"] if slot["available"]]
                if available_times:
                    response_text = f"On that date, the following times are available: {', '.join(available_times)}"
                else:
                    response_text = "Sorry, there are no tables available for that date."
            else:
                response_text = "Sorry, I couldn't retrieve availability at the moment."

            st.markdown(response_text)
    
    st.session_state.messages.append({"role": "assistant", "content": response_text})