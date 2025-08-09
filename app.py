import streamlit as st
import requests
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta

# --- Configuration and Setup ---
load_dotenv()

try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error configuring Gemini: Please check your GOOGLE_API_KEY in the .env file. Error: {e}")
    st.stop()

API_BASE_URL = "http://localhost:8547/api/ConsumerApi/v1/Restaurant/TheHungryUnicorn"
API_BEARER_TOKEN = os.getenv("API_BEARER_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8")

# --- API Functions ---

def check_restaurant_availability(date: str, party_size: int):
    """Calls the mock API to check for available time slots."""
    endpoint = f"{API_BASE_URL}/AvailabilitySearch"
    headers = {"Authorization": f"Bearer {API_BEARER_TOKEN}"}
    data = {"VisitDate": date, "PartySize": party_size, "ChannelCode": "ONLINE"}
    try:
        response = requests.post(endpoint, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def create_new_booking(date: str, time: str, party_size: int):
    """Calls the mock API to create a new booking."""
    endpoint = f"{API_BASE_URL}/BookingWithStripeToken"
    headers = {"Authorization": f"Bearer {API_BEARER_TOKEN}"}
    data = {
        "VisitDate": date, "VisitTime": time, "PartySize": party_size, "ChannelCode": "ONLINE",
        "Customer[FirstName]": "George", "Customer[Surname]": "Drayson",
        "Customer[Email]": "george.drayson@locailabs.com", "Customer[Mobile]": "07123456789"
    }
    try:
        response = requests.post(endpoint, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_booking_details(booking_reference: str):
    """Calls the mock API to get details for an existing booking."""
    endpoint = f"{API_BASE_URL}/Booking/{booking_reference}"
    headers = {"Authorization": f"Bearer {API_BEARER_TOKEN}"}
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 404:
            return {"error": "Booking not found."}
        return {"error": str(e)}

def update_booking(booking_reference: str, updates: dict):
    """Calls the mock API to update an existing booking."""
    endpoint = f"{API_BASE_URL}/Booking/{booking_reference}"
    headers = {"Authorization": f"Bearer {API_BEARER_TOKEN}"}
    data = {key: value for key, value in updates.items() if value is not None}
    try:
        response = requests.patch(endpoint, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def cancel_booking(booking_reference: str):
    """Calls the mock API to cancel an existing booking."""
    endpoint = f"{API_BASE_URL}/Booking/{booking_reference}/Cancel"
    headers = {"Authorization": f"Bearer {API_BEARER_TOKEN}"}
    data = {
        "cancellationReasonId": 1, # 1 = Customer Request
        "micrositeName": "TheHungryUnicorn",
        "bookingReference": booking_reference
    }
    try:
        response = requests.post(endpoint, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# --- NLU Function ---

def get_intent_and_entities(prompt: str):
    """Uses Gemini to extract intent and entities from the user's prompt."""
    system_prompt = f"""
    You are an NLU (Natural Language Understanding) engine for a restaurant booking system.
    Analyze the user's text and identify their intent and any relevant entities.
    The current date is {datetime.now().strftime('%Y-%m-%d')}.
    Your response MUST be a raw JSON string without any markdown formatting (i.e., no ```json).
    
    Possible intents are: 'check_availability', 'book_reservation', 'check_booking', 'modify_booking', 'cancel_booking', 'unknown'.
    
    Possible entities are:
    - 'date': The specific date for the booking, formatted as 'YYYY-MM-DD'.
    - 'time': The specific time, formatted as 'HH:MM:SS'.
    - 'party_size': The number of people as an integer.
    - 'booking_reference': The booking reference code.
    
    Here are some examples:
    User: "show me tables for 2 people this Friday"
    You: {{"intent": "check_availability", "entities": {{"party_size": 2, "date": "{(datetime.now() + timedelta(days=(4 - datetime.now().weekday()) % 7)).strftime('%Y-%m-%d')}"}}}}

    User: "7:30pm sounds good"
    You: {{"intent": "book_reservation", "entities": {{"time": "19:30:00"}}}}

    User: "can you check my reservation ABC1234?"
    You: {{"intent": "check_booking", "entities": {{"booking_reference": "ABC1234"}}}}

    User: "change my booking XYZ987 to 4 people"
    You: {{"intent": "modify_booking", "entities": {{"booking_reference": "XYZ987", "party_size": 4}}}}

    User: "please cancel booking GHI456"
    You: {{"intent": "cancel_booking", "entities": {{"booking_reference": "GHI456"}}}}
    """
    full_prompt = f"{system_prompt}\nUser: \"{prompt}\"\nYou:"
    try:
        response = gemini_model.generate_content(full_prompt)
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response_text)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return {"intent": "unknown", "entities": {}}

# --- Streamlit App ---

st.set_page_config(page_title="The HungryUnicorn Bookings", page_icon="🦄")
st.title("🦄 The HungryUnicorn Booking Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.context = {} 
    st.session_state.messages.append({"role": "assistant", "content": "Hello! How can I help you book a table at The HungryUnicorn?"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What would you like to do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            nlu_response = get_intent_and_entities(prompt)
            intent = nlu_response.get("intent")
            entities = nlu_response.get("entities", {})
            
            response_text = "I'm not sure how to help with that. Please ask about booking a table."

            if intent == "check_availability":
                date = entities.get("date")
                party_size = entities.get("party_size")
                if date and party_size:
                    st.session_state.context = {"date": date, "party_size": party_size}
                    availability_data = check_restaurant_availability(date=date, party_size=party_size)
                    if availability_data and not availability_data.get("error"):
                        available_times = [slot["time"] for slot in availability_data.get("available_slots", []) if slot["available"]]
                        if available_times:
                            response_text = f"For a party of {party_size} on {date}, the following times are available: {', '.join(available_times)}"
                        else:
                            response_text = f"Sorry, no tables are available for that party size on {date}."
                    else:
                        response_text = "Sorry, I couldn't retrieve availability at the moment."
                else:
                    response_text = "To check availability, I need to know the date and the number of people."
            
            elif intent == "book_reservation":
                date = st.session_state.context.get("date")
                party_size = st.session_state.context.get("party_size")
                time = entities.get("time")
                if date and party_size and time:
                    booking_data = create_new_booking(date=date, time=time, party_size=party_size)
                    if booking_data and not booking_data.get("error"):
                        booking_ref = booking_data.get("booking_reference")
                        response_text = f"Great! Your table is booked. Your booking reference is **{booking_ref}**. We look forward to seeing you!"
                        st.session_state.context = {} 
                    else:
                        response_text = "Sorry, I was unable to complete your booking at that time. It may have just been taken."
                else:
                    response_text = "I'm missing some details. Please confirm the time you'd like to book from the available slots."

            elif intent == "check_booking":
                booking_ref = entities.get("booking_reference")
                if booking_ref:
                    details = get_booking_details(booking_ref)
                    if details and not details.get("error"):
                        booking_status = details.get("status")
                        if booking_status == "cancelled":
                            response_text = f"I found a booking with the reference **{booking_ref}**, but it has already been cancelled."
                        else:
                            response_text = f"I found your booking. It's for **{details.get('party_size')} people** on **{details.get('visit_date')}** at **{details.get('visit_time')}**."
                    else:
                        response_text = f"I couldn't find a booking with the reference **{booking_ref}**. Please double-check the reference number."
                else:
                    response_text = "I can help with that. What is your booking reference number?"

            elif intent == "modify_booking":
                booking_ref = entities.get("booking_reference")
                if booking_ref:
                    updates = {
                        "VisitDate": entities.get("date"),
                        "VisitTime": entities.get("time"),
                        "PartySize": entities.get("party_size")
                    }
                    update_result = update_booking(booking_ref, updates)
                    if update_result and not update_result.get("error"):
                        response_text = f"Your booking **{booking_ref}** has been successfully updated."
                    else:
                        response_text = f"Sorry, I was unable to update booking **{booking_ref}**."
                else:
                    response_text = "I can help with that, but I need your booking reference to find the reservation you want to change."

            elif intent == "cancel_booking":
                booking_ref = entities.get("booking_reference")
                if booking_ref:
                    cancel_result = cancel_booking(booking_ref)
                    if cancel_result and not cancel_result.get("error"):
                        response_text = f"Your booking **{booking_ref}** has been successfully cancelled."
                    else:
                        response_text = f"Sorry, I was unable to cancel booking **{booking_ref}**. Please check the reference number."
                else:
                    response_text = "I can help with that, but I need your booking reference to find the reservation you want to cancel."

            st.markdown(response_text)
            
    st.session_state.messages.append({"role": "assistant", "content": response_text})