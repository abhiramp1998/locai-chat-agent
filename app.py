import streamlit as st
import requests
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from the .env file
load_dotenv()

# --- Configuration and Setup ---

# Configure the Gemini client with the API key, with a friendly error if not found
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("Google Gemini API key not found. Please add your key to a .env file.")
    st.stop()

try:
    genai.configure(api_key=API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error configuring Gemini: {e}")
    st.stop()

# Constants for the mock API
API_BASE_URL = "http://localhost:8547/api/ConsumerApi/v1/Restaurant/TheHungryUnicorn"
API_BEARER_TOKEN = os.getenv("API_BEARER_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8")


# --- Helper & API Functions ---

def format_time_for_display(time_str: str) -> str:
    """Converts 'HH:MM:SS' to 'HH:MM AM/PM' format."""
    if not time_str: return ""
    try:
        t = datetime.strptime(time_str, "%H:%M:%S")
        return t.strftime("%I:%M %p").strip()
    except ValueError:
        return time_str

def check_restaurant_availability(date: str, party_size: int):
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
    endpoint = f"{API_BASE_URL}/Booking/{booking_reference}/Cancel"
    headers = {"Authorization": f"Bearer {API_BEARER_TOKEN}"}
    data = {
        "cancellationReasonId": 1, 
        "micrositeName": "TheHungryUnicorn",
        "bookingReference": booking_reference
    }
    try:
        response = requests.post(endpoint, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_intent_and_entities(prompt: str):
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
    - 'time_of_day': Can be 'morning', 'afternoon', or 'evening'. Infer this from context like 'tonight' or 'lunch'.

    Here are some examples:
    User: "show me tables for 2 people this Friday evening"
    You: {{"intent": "check_availability", "entities": {{"party_size": 2, "date": "{(datetime.now() + timedelta(days=(4 - datetime.now().weekday()) % 7)).strftime('%Y-%m-%d')}", "time_of_day": "evening"}}}}

    User: "7:30pm sounds good"
    You: {{"intent": "book_reservation", "entities": {{"time": "19:30:00"}}}}

    User: "can you check my reservation ABC1234?"
    You: {{"intent": "check_booking", "entities": {{"booking_reference": "ABC1234"}}}}

    User: "change my booking XYZ987 to 4 people at 8pm"
    You: {{"intent": "modify_booking", "entities": {{"booking_reference": "XYZ987", "party_size": 4, "time": "20:00:00"}}}}

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

st.set_page_config(page_title="Restaurant Booking Agent")
st.title("Restaurant Booking Agent")

with st.sidebar:
    if st.button("New Chat"):
        # Reset the chat history to include the initial greeting
        st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you book a table at The HungryUnicorn?"}]
        # Clear any stored context
        st.session_state.context = {}
        # Rerun the app to show the changes
        st.rerun()

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
                        available_slots = [slot for slot in availability_data.get("available_slots", []) if slot["available"]]
                        
                        time_of_day = entities.get("time_of_day")
                        if time_of_day == "evening":
                            available_slots = [slot for slot in available_slots if int(slot["time"][:2]) >= 18]
                        elif time_of_day == "afternoon":
                            available_slots = [slot for slot in available_slots if 12 <= int(slot["time"][:2]) < 18]
                        
                        display_times = [format_time_for_display(slot["time"]) for slot in available_slots]

                        if display_times:
                            response_text = f"For a party of {party_size} on {date}, the following times are available: {', '.join(display_times)}"
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
                        st.session_state.context = {"booking_reference": booking_ref}
                        booking_status = details.get("status")
                        if booking_status == "cancelled":
                            response_text = f"I found a booking with the reference **{booking_ref}**, but it has already been cancelled."
                        else:
                            party = details.get('party_size')
                            visit_date = details.get('visit_date')
                            visit_time = format_time_for_display(details.get('visit_time'))
                            response_text = f"I found your booking. It's for **{party} people** on **{visit_date}** at **{visit_time}**."
                    else:
                        response_text = f"I couldn't find a booking with the reference **{booking_ref}**. Please double-check the reference number."
                else:
                    response_text = "I can help with that. What is your booking reference number?"

            elif intent == "modify_booking":
                booking_ref = entities.get("booking_reference") or st.session_state.context.get("booking_reference")
                updates_from_user = {
                    "VisitDate": entities.get("date"),
                    "VisitTime": entities.get("time"),
                    "PartySize": entities.get("party_size")
                }
                updates = {key: value for key, value in updates_from_user.items() if value is not None}

                if booking_ref and updates:
                    original_details = get_booking_details(booking_ref)
                    if original_details and not original_details.get("error"):
                        
                        new_party_size = updates.get("PartySize")
                        if new_party_size:
                            visit_date = updates.get("VisitDate") or original_details.get("visit_date")
                            visit_time = updates.get("VisitTime") or original_details.get("visit_time")
                            
                            availability_data = check_restaurant_availability(date=visit_date, party_size=1)
                            slot_info = next((s for s in availability_data.get("available_slots", []) if s["time"] == visit_time), None)
                            
                            if slot_info:
                                max_size = slot_info.get("max_party_size", 0)
                                if new_party_size > max_size:
                                    response_text = f"I'm sorry, but we cannot accommodate a party of {new_party_size} at that time. The maximum for that slot is {max_size}."
                                    st.markdown(response_text)
                                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                                    st.stop()
                            else:
                                response_text = "Sorry, I couldn't find the original time slot to verify the new party size."
                                st.markdown(response_text)
                                st.session_state.messages.append({"role": "assistant", "content": response_text})
                                st.stop()

                        update_result = update_booking(booking_ref, updates)
                        if update_result and not update_result.get("error"):
                            update_fragments = []
                            if "VisitDate" in updates: update_fragments.append(f"date to {updates['VisitDate']}")
                            if "VisitTime" in updates: update_fragments.append(f"time to {format_time_for_display(updates['VisitTime'])}")
                            if "PartySize" in updates: update_fragments.append(f"party size to {updates['PartySize']}")
                            response_text = f"Your booking **{booking_ref}** has been successfully updated: " + ", ".join(update_fragments) + "."
                            st.session_state.context = {}
                        else:
                            response_text = f"Sorry, I was unable to update booking **{booking_ref}** with those details."
                    else:
                        response_text = f"I couldn't find the booking **{booking_ref}** to modify it."
                else:
                    response_text = "To modify a booking, please tell me the booking reference and what you'd like to change."

            elif intent == "cancel_booking":
                booking_ref = entities.get("booking_reference") or st.session_state.context.get("booking_reference")
                if booking_ref:
                    cancel_result = cancel_booking(booking_ref)
                    if cancel_result and not cancel_result.get("error"):
                        response_text = f"Your booking **{booking_ref}** has been successfully cancelled."
                        st.session_state.context = {}
                    else:
                        response_text = f"Sorry, I was unable to cancel booking **{booking_ref}**. Please check the reference number."
                else:
                    response_text = "I can help with that, but I need your booking reference to find the reservation you want to cancel."

            st.markdown(response_text)
            
    st.session_state.messages.append({"role": "assistant", "content": response_text})