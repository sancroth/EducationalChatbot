# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.events import UserUtteranceReverted
from rasa_sdk.types import DomainDict
import psycopg2
import os
import json
import requests
from datetime import datetime, timedelta
from openai import OpenAI
from rasa_sdk.events import EventType

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "ice"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "mysecretpassword"),
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432")
}

days = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή"]

api_key = os.getenv("OPENAI_API_KEY",None)
client = OpenAI(api_key=api_key)

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8000")

def fetch_rag_context(question: str) -> str:
    try:
        resp = requests.post(
            f"{RAG_SERVICE_URL}/get_context",
            json={"question": question},
            timeout=15
        )
        resp.raise_for_status()
        return resp.json().get("context", "")
    except Exception as e:
        print(f"Error calling RAG API: {e}")
        return ""

def get_user_team(user_semester: int,user_id: int) -> int:
    if user_semester == 1:
        if user_id % 10 in (7, 8, 9):
            return 2
    else:
        if user_id % 2 == 1:
            return 2
    return 1


class ActionDefaultFallback(Action):
    def name(self) -> str:
        return "action_default_fallback"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Send fallback message
        dispatcher.utter_message(response="utter_default_fallback")
        # Revert the user's input to allow them to rephrase
        return [UserUtteranceReverted()]

class ActionAnswerFromPDF(Action):
    def name(self) -> str:
        return "action_answer_from_pdf"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_q = tracker.latest_message.get("text", "")
        
        # Call the RAG service
        context = fetch_rag_context(user_q)

        # Construct the prompt as before
        prompt = f"""Use only this information to answer. 
                     Do not access your personal knowledge base or internet.
                     You take the role of a college teacher that answers to their student.
 
                     Context:
                     {context}
 
                     Question: {user_q}
 
                     Answer:"""

        try:
            resp = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful college teacher teaching their student."},
                    {"role": "user", "content": prompt}
                ]
            )
            answer = resp.choices[0].message.content.strip()
            dispatcher.utter_message(text=answer)

        except Exception as e:
            print(f"Error during OpenAI call: {e}")
            dispatcher.utter_message(
                text="Λυπάμαι, δεν κατάφερα να δημιουργήσω απάντηση αυτή τη στιγμή. Δοκίμασε ξανά!"
            )

        return []

class ActionOfferedFollowUpHelp(Action):
    def name(self) -> str:
        return "action_bot_offered_followup_help"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Send fallback message
        # Revert the user's input to allow them to rephrase
        return [SlotSet("offered_follow_up_help_once", True)]

class ActionInitializeUser(Action):

    def name(self) -> str:
        return "action_initialize_user"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        custom_data = tracker.latest_message.get("metadata", {})
        print(tracker.latest_message)
        print("init user data")
        print(custom_data)
        if not custom_data:
            raw_text = tracker.latest_message.get("text", "")
            try:
                # /initialize{"custom_data":{"uid":2,"department_key":"ice","authenticated":"True"}}
                parsed_text = json.loads(raw_text.split('/initialize')[1])
                custom_data = parsed_text.get("custom_data", {})
            except (IndexError, json.JSONDecodeError):
                custom_data = {}
        uid = custom_data.get("uid", "unknown")
        role_id = custom_data.get("role_id", "unknown")
        department_id = custom_data.get("department_id", None)
        department_key = custom_data.get("department_key", "unknown")
        authenticated = custom_data.get("authenticated", False)

        dispatcher.utter_message(response="utter_first_message")

        if authenticated:
            dispatcher.utter_message(response="utter_authenticated")
        else:
            dispatcher.utter_message(response="utter_not_authenticated")

        return [
            SlotSet("uid", uid),
            SlotSet("role_id", role_id),
            SlotSet("department_id", department_id),
            SlotSet("department_key", department_key),
            SlotSet("authenticated", authenticated)
        ]

class ActionSetUserRequiresBotOptions(Action):
    def name(self) -> str:
        return "action_set_user_requires_bot_options"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Detect user intent from the last message
        last_intent = tracker.latest_message['intent'].get('name')
        # Determine slot value based on the detected intent
        if last_intent == "user_affirm":
            return [SlotSet("requested_bot_options", True)]
        elif last_intent == "user_deny":
            return [SlotSet("requested_bot_options", False)]
        elif last_intent == "user_deny_options":
            return [SlotSet("requested_bot_options", False)]
        else:
            dispatcher.utter_message(text="Συγγνώμη, δεν σε κατάλαβα.")
            return []

class ActionGetCourseTeacher(Action):
    def name(self) -> str:
        return "action_fetch_course_teacher_by_course_name"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        course_name = next(tracker.get_latest_entity_values("course_name"), None)
        if course_name == None:
            return[
                SlotSet("last_teacher_name_list_provided_by_bot",None),
                SlotSet("last_teacher_name_provided_by_bot",None),
                SlotSet("course_teacher_name_found",False),
                SlotSet("course_teacher_name_found_multiple",False),
                SlotSet("course_name",None)
            ]
        cur.execute(f"SELECT class_id FROM classes where class_name='{course_name}';")
        class_id = cur.fetchone()[0]
        if class_id:
            query = """
            SELECT u.last_name FROM
            class_schedules cs 
            JOIN users u on cs.teacher_id=u.user_id 
            WHERE cs.class_id=%s
            GROUP BY u.last_name;
            """
            print(class_id)
            formatted_query = cur.mogrify(
                query, 
                (class_id,)
            ).decode("utf-8")
            print("Executing query:\n", formatted_query)
            cur.execute(query, (class_id,))
            teacher_names = cur.fetchall()
            if len(teacher_names)>1:
                return[
                    SlotSet("last_teacher_name_list_provided_by_bot",teacher_names),
                    SlotSet("last_teacher_name_provided_by_bot",None),
                    SlotSet("course_teacher_name_found",True),
                    SlotSet("course_teacher_name_found_multiple",True),
                    SlotSet("last_course_name_provided_by_bot", course_name)
                ]
            else:
                return[
                    SlotSet("last_teacher_name_list_provided_by_bot",None),
                    SlotSet("last_teacher_name_provided_by_bot",teacher_names[0]),
                    SlotSet("course_teacher_name_found",True),
                    SlotSet("course_teacher_name_found_multiple",False),
                    SlotSet("last_course_name_provided_by_bot", course_name)
                ]
        else:
            return [
                SlotSet("course_teacher_name_found",False),
                SlotSet("course_teacher_name_found_multiple",False),
                SlotSet("course_name",None)
            ]

class ActionGetCourseClassroom(Action):
    def name(self) -> str:
        return "action_fetch_course_classroom_by_course_name"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_id = tracker.get_slot("uid")
        print(f"user {user_id} requested the date of next course")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(f"SELECT semester FROM student_info WHERE user_id = {user_id};")
        user_semester = cur.fetchone()[0]
        user_team = get_user_team(user_semester,user_id)
        course_name = next(tracker.get_latest_entity_values("course_name"), None)
        
        # If no course name entity found, check if we have a previous course in context
        if course_name == None:
            course_name = tracker.get_slot("last_course_name_provided_by_bot")
            
        if course_name == None:
            return[
                SlotSet("last_classroom_provided_by_bot",None),
                SlotSet("course_classroom_found",False),
                SlotSet("course_name",None)
            ]
        cur.execute(f"SELECT class_id FROM classes WHERE class_name = '{course_name}';")
        course_id = cur.fetchone()[0]
        if course_id:
            cur.execute(f"SELECT classroom FROM class_schedules WHERE class_id = {course_id} AND class_team = {user_team} GROUP BY classroom;")
            classroom = cur.fetchone()[0]
            return[
                SlotSet("last_classroom_provided_by_bot",classroom),
                SlotSet("course_classroom_found",True)
            ]
        else:
            return [SlotSet("course_classroom_found",False)]


class ActionGetNextCourseDate(Action):
    def name(self) -> str:
        return "action_get_date_of_next_course"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_id = tracker.get_slot("uid")
        print(f"user {user_id} requested the date of next course")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(f"SELECT semester FROM student_info WHERE user_id = {user_id};")
        user_semester = cur.fetchone()[0]
        user_team = get_user_team(user_semester,user_id)
        today = datetime.now()
        course_name = next(tracker.get_latest_entity_values("course_name"), None)
        last_intent = tracker.latest_message['intent'].get('name')

        print(f"user_team:{user_team}")
        print(f'date against {today.time()}')
        print(f'user intent: {last_intent}')
        print(f'course name: {course_name if course_name else "None"}')
        
        if last_intent=='ask_next_schedule_of_course_by_course_name':
            if course_name:
                query = """
                SELECT c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
                FROM student_enrollments se
                JOIN class_schedules cs ON se.class_id = cs.class_id
                JOIN classes c ON cs.class_id = c.class_id
                WHERE se.user_id = %s
                AND cs.day_of_week = %s
                AND cs.class_team = %s
                AND c.class_name= %s
                GROUP BY c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
                ORDER BY cs.day_of_week, cs.start_time;
                """
        else:
            query = """
            SELECT c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
            FROM student_enrollments se
            JOIN class_schedules cs ON se.class_id = cs.class_id
            JOIN classes c ON cs.class_id = c.class_id
            WHERE se.user_id = %s 
            AND cs.day_of_week = %s
            AND cs.class_team = %s
            GROUP BY c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
            ORDER BY cs.day_of_week, cs.start_time;
            """

        course_day_found = False
        check_against_current_time = True
        query_date=today.weekday()+1
        total_days_checked=0

        if today.weekday()>4:
            query_date=1
            check_against_current_time=False

        while(not course_day_found):
            if last_intent=='ask_next_schedule_of_course_by_course_name':
                response = f"Σου παραθέτω τις πληροφορίες για το επόμενο μάθημα ({course_name}) που βρήκα στο πρόγραμμα σου!"
                # formatted_query = cur.mogrify(
                #     query, 
                #     (user_id, query_date,user_team,course_name)
                # ).decode("utf-8")
                # print("Executing query:\n", formatted_query)
                cur.execute(query, (user_id, query_date,user_team,course_name))
            else:
                response = "Σου παραθέτω τις πληροφορίες για το επόμενο μάθημα που βρήκα στο πρόγραμμα σου!"
                # formatted_query = cur.mogrify(
                #     query, 
                #     (user_id, query_date,user_team)
                # ).decode("utf-8")
                # print("Executing query:\n", formatted_query)
                cur.execute(query, (user_id, query_date,user_team))

            schedule = cur.fetchall()

            print(query_date)

            if schedule and total_days_checked<5:
                for class_name, classroom, day_of_week, start_time, end_time in schedule:
                    if (today.time()>start_time and check_against_current_time):
                        continue
                    days_ahead = ((day_of_week-1) - today.weekday() + 7) % 7
                    query_date = today + timedelta(days=days_ahead)
                    dispatcher.utter_message(text=response)
                    dispatcher.utter_message(text=f'Ημερομηνία: {query_date.strftime("%d/%m/%Y")}')
                    dispatcher.utter_message(text=f"{days[day_of_week-1]}: {class_name}")
                    dispatcher.utter_message(text=f"Αίθουσα: {classroom}, {start_time} με {end_time}")
                    course_day_found=True
                    cur.close()
                    conn.close()
                    return []
                if not course_day_found:
                    print(f"scheduled course not found on day {query_date}. incrementing")
                    query_date+=1
                    total_days_checked+=1
                    print(query_date)
                    check_against_current_time=False
                    if query_date>5:
                        query_date=1
            else:
                if course_name:
                    print(f"scheduled course not found on day {query_date}. incrementing")
                    query_date+=1
                    total_days_checked+=1
                    print(query_date)
                    check_against_current_time=False
                    if query_date>5:
                        query_date=1
                else:
                    response = "Δεν βρήκα κάποιο μάθημα στο πρόγραμμα σου! Αν πιστεύεις ότι αυτό είναι λάθος, παρακαλώ επικοινώνησε με τη γραμματεία του τμήματος."
                    dispatcher.utter_message(text=response)
        cur.close()
        conn.close()
        return []

class ActionGetWeeklySchedule(Action):
    def name(self) -> str:
        return "action_get_weekly_schedule"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_id = tracker.get_slot("uid")
        print(f"user {user_id} requested the weekly program")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute(f"SELECT semester FROM student_info WHERE user_id = {user_id};")
        user_semester=cur.fetchone()[0]
        user_team = get_user_team(user_semester,user_id)

        today = datetime.now()
        print(f"user_team:{user_team}")
        print(f'date against {today.time()}')
        
        query = """
        SELECT c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
        FROM student_enrollments se
        JOIN class_schedules cs ON se.class_id = cs.class_id
        JOIN classes c ON cs.class_id = c.class_id
        WHERE se.user_id = %s 
        AND cs.day_of_week BETWEEN %s AND 6
        AND cs.class_team = %s
        GROUP BY c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
        ORDER BY cs.day_of_week, cs.start_time;
        """

        # Print the final query with parameters
        formatted_query = cur.mogrify(
            query, 
            (user_id, today.weekday()+1,user_team)
        ).decode("utf-8")
        print("Executing query:\n", formatted_query)

        cur.execute(query, (user_id, today.weekday()+1,user_team))
        schedule = cur.fetchall()

        if schedule:
            response = "Παρακάτω είναι το πρόγραμμα της υπόλοιπης εβδομάδας:\n"
            dispatcher.utter_message(text=response)
            total=0
            for class_name, classroom, day_of_week, start_time, end_time in schedule:
                if (today.time()>start_time and day_of_week==today.weekday()) or today.weekday()>day_of_week-1:
                    continue
                dispatcher.utter_message(text=f"{days[day_of_week-1]}: {class_name}")
                dispatcher.utter_message(text=f"Αίθουσα: {classroom}, {start_time} με {end_time}")
                total+=1
            if total==0:
                response = "Νομίζω πως δεν έχεις κάποιο άλλο μάθημα για την υπόλοιπη εβδομάδα! Καλή ξεκούραση και καλή μελέτη!"
                dispatcher.utter_message(text=response)
            cur.close()
            conn.close()
            #response += f"{days[day_of_week-1]}: {class_name}\n\nΑίθουσα: {classroom}, {start_time} με {end_time}\n"
        else:
            response = "Νομίζω πως δεν έχεις κάποιο άλλο μάθημα για την υπόλοιπη εβδομάδα! Καλή ξεκούραση και καλή μελέτη!"
            dispatcher.utter_message(text=response)
        cur.close()
        conn.close()

        return []

class ActionGetDepartmentSecretariat(Action):
    def name(self) -> str:
        return "action_get_department_secretariat_info"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            user_id = tracker.get_slot("uid")
            last_intent = tracker.latest_message['intent'].get('name')

            print(user_id)
            get_user_department_query = """
            SELECT department_id FROM users WHERE user_id=%s;
            """
            cur.execute(get_user_department_query, (user_id,))
            department_id = cur.fetchone()
            print(department_id)
            get_department_info_query = """
            SELECT email, contact_phone, address, working_hours, website_url
            FROM department_secretariats s
            WHERE s.department_id=%s;
            """
            cur.execute(get_department_info_query, (department_id,))
            result = cur.fetchone()
            print(result)

            if result:
                email, contact_phone, address, working_hours ,website_url = result
                if last_intent=="get_department_secretariat_info":
                    dispatcher.utter_message(text=f"- Email: {email}")
                    dispatcher.utter_message(text=f"- Τηλ.Επικοινωνίας: {contact_phone}")
                    if address:
                        dispatcher.utter_message(text=f"- Διεύθυνση: {address}")
                    dispatcher.utter_message(text=f"- Ώρες Κοινού: {working_hours or 'Δεν βρέθηκε'}")
                    dispatcher.utter_message(text=f"- Website Τμήματος: {website_url or 'Δεν βρέθηκε'}")
                elif last_intent=="get_department_secretariat_phone":
                    dispatcher.utter_message(text=f"- Τηλ.Επικοινωνίας: {contact_phone}")
                elif last_intent=="get_department_secretariat_availability":
                    dispatcher.utter_message(text=f"- Ώρες Κοινού: {working_hours or 'Δεν βρέθηκε'}")
                elif last_intent=="get_department_secretariat_email":
                    dispatcher.utter_message(text=f"- Email: {email or 'Δεν βρέθηκε'}")
                elif last_intent=="get_department_website_url":
                    dispatcher.utter_message(text=f"- Website Τμήματος: {website_url or 'Δεν βρέθηκε'}")

            else:
                dispatcher.utter_message(text=f"Δεν βρέθηκαν στοιχεία για τη γραμματεία που ζήτησες! Ζητώ συγγνώμη.")
        except Exception as e:
            dispatcher.utter_message(text="Ουπς! Κάτι πήγε λάθος με το σύστημα! Προσπάθησε ξανά αργότερα...")
            print(f"Database error: {e}")
        return []

class ActionAskEducationalQuestion(Action):
    def name(self) -> str:
        return "action_ask_educational_question"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        INTENT_CONFIG = {
            "detailed": {
                "max_tokens": 1500,
                "temperature": 0.8,
                "system_message": "You are an assistant providing detailed and technical explanations. Answer the question in depth and using technical terms if needed.\
                                    Use up to 1500 tokens.\
                                    If the request is not of programming or educational nature reply with:\
                                    'Αν και θα ήθελα πολύ να απαντήσω στο ερώτημα σου, δεν θεωρώ ότι είναι εκπαιδευτικής φύσης!'"
            },
            "less_complicated": {
                "max_tokens": 500,
                "temperature": 0.4,
                "system_message": "You are an assistant explaining topics in a simple and easy-to-understand manner.\
                                    Use up to 300 tokens.\
                                    If the request is not of programming or educational nature reply with:\
                                    'Αν και θα ήθελα πολύ να απαντήσω στο ερώτημα σου, δεν θεωρώ ότι είναι εκπαιδευτικής φύσης!'"
            },
            "default" : {
                "max_tokens": 700,
                "temperature": 0.5,
                "system_message": "You are an assistant answering questions and providing helpful information.\
                                    Use up to 700 tokens.\
                                    If the request is not of programming or educational nature reply with:\
                                    'Αν και θα ήθελα πολύ να απαντήσω στο ερώτημα σου, δεν θεωρώ ότι είναι εκπαιδευτικής φύσης!'"
            }
        }

        DETAIL_INTENT_TO_LEVEL = {
            "follow_up_more_detailed_information":"detailed",
            "follow_up_less_complicated":"less_complicated",
            "follow_up_tell_me_more":"default",
            "default": "default"
        }

        offer_persist_detail_level=False

        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found in environment variables.")
                

            client = OpenAI(api_key=api_key)

            last_intent = tracker.latest_message['intent'].get('name')
            user_message = tracker.latest_message.get("text")
            user_detail_level_preference = tracker.get_slot("user_detail_level_preference")

            config = INTENT_CONFIG.get(user_detail_level_preference,INTENT_CONFIG.get("default"))
            if last_intent in ["follow_up_less_complicated","follow_up_more_detailed_information"]:
              if not tracker.get_slot("offered_to_persist_level_of_detail"):
                # flag to ask user to save the detail level preference
                offer_persist_detail_level=True
              if not tracker.get_slot("user_replied_to_persist_level_of_detail"):
                # run only the first time the user requests additional/less details but slot is not yet configured
                config = INTENT_CONFIG.get(DETAIL_INTENT_TO_LEVEL[last_intent],INTENT_CONFIG.get("default"))

            history = []
            for event in tracker.events[-4:]:
                if event["event"] == "user" and "text" in event:
                    history.append({"role": "user", "content": event["text"]})
                elif event["event"] == "bot" and "text" in event:
                    history.append({"role": "assistant", "content": event["text"]})
            history = history[-4:]  # Keep only the last 4 messages
            history.append({"role": "user", "content": f"{user_message}"})
            messages = [{"role": "assistant","content":config['system_message'].replace('\t',' ')}] + history

            print(messages)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"]
            )
            print(response)
            answer = response.choices[0].message.content.strip()
            print(answer)
        except Exception as e:
            answer = "Λυπάμαι αλλα δεν κατάφερα να δημιουργήσω μια απάντηση για το ερώτημά σου. Ξαναδοκίμασε αναδιατυπώνοντας την ερώτηση σου"
            print(f"OpenAI API error: {e}")

        dispatcher.utter_message(text=answer)
        if offer_persist_detail_level:
            dispatcher.utter_message(response="utter_offer_persist_level_of_detail")
            return [SlotSet("offered_to_persist_level_of_detail", True),SlotSet("latest_user_intent",last_intent)]
        return []

class ActionUpdateOpenAIDetailLevel(Action):
    def name(self) -> str:
        return "action_update_level_of_detail_user_preference"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        DETAIL_INTENT_TO_LEVEL = {
            "follow_up_more_detailed_information":"detailed",
            "follow_up_less_complicated":"less_complicated",
            "follow_up_tell_me_more":"default",
            "default": "default"
        }

        last_intent = tracker.get_slot('latest_user_intent')
        if last_intent!=None:
            return [SlotSet("user_detail_level_preference",DETAIL_INTENT_TO_LEVEL[last_intent])]
        
        return []

class ValidateScheduledMeetingWithTeacherForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_scheduled_meeting_with_teacher_form"

    # async def required_slots(self, domain_slots, dispatcher, tracker, domain):
    #     updated_slots = domain_slots.copy()
    #     if tracker.get_slot("scheduled_meeting_correct_teacher_email"):
    #         print("Preparing minx/max date slots")
    #         updated_slots = ["scheduled_meeting_min_date","scheduled_meeting_max_date"] + updated_slots
    #     print(updated_slots)
    #     return updated_slots

    async def extract_scheduled_meeting_min_date(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict
    ) -> Dict[Text, Any]:
        today = datetime.today()
        min_date = (today + timedelta(days=1)).strftime("%d/%m/%Y")
        print(f"Min Date: {min_date}")
        return {
            "scheduled_meeting_min_date": min_date,
        }

    def validate_scheduled_meeting_min_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        today = datetime.today()
        min_date = (today + timedelta(days=1)).strftime("%d/%m/%Y")
        max_date = (today + timedelta(days=30)).strftime("%d/%m/%Y")
        return {
            "scheduled_meeting_min_date": slot_value
        }

    async def extract_scheduled_meeting_max_date(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict
    ) -> Dict[Text, Any]:
        today = datetime.today()
        max_date = (today + timedelta(days=30)).strftime("%d/%m/%Y")
        print(f"Max Date: {max_date}")
        return {
            "scheduled_meeting_max_date": max_date,
        }

    def validate_scheduled_meeting_max_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        return {
            "scheduled_meeting_max_date": slot_value
        }

    def validate_scheduled_meeting_teacher_email(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        try:
            if "@uniwa.gr" in slot_value:
                return {"scheduled_meeting_teacher_email": slot_value}
            else:
                dispatcher.utter_message(response="utter_scheluded_meeting_teach_email_deny")
                return {"scheduled_meeting_teacher_email": None}
        except ValueError:
            return {"scheduled_meeting_teacher_email": None}

    def validate_scheduled_meeting_correct_teacher_email(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        try:
            if tracker.get_slot("scheduled_meeting_correct_teacher_email"):

                conn = psycopg2.connect(**DB_CONFIG)
                cur = conn.cursor()

                department_id = tracker.get_slot("department_id")
                teacher_email = tracker.get_slot("scheduled_meeting_teacher_email")

                # Query to check if the email exists with role_id=2 and department_id
                query = """
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE email = %s AND role_id = 2 AND department_id = %s;
                """
                print("fetching teacher with given email")
                cur.execute(query, (teacher_email, department_id))
                result = cur.fetchone()
                if result and result[0] > 0:
                    print(f"total found: {result[0]}")
                    dispatcher.utter_message(response="utter_scheduled_meeting_teach_email_found")
                    return {"scheduled_meeting_teacher_email": tracker.get_slot("scheduled_meeting_teacher_email"), "scheduled_meeting_correct_teacher_email": True}
                else:
                    print("teacher not found")
                    dispatcher.utter_message(response="utter_scheduled_meeting_teach_email_not_found")
                    return {"scheduled_meeting_teacher_email": None, "scheduled_meeting_correct_teacher_email": None}
            else:
                return {"scheduled_meeting_teacher_email": None, "scheduled_meeting_correct_teacher_email": None}
        except Exception as e:
            dispatcher.utter_message(text="Υπήρξε ένα σφάλμα κατά την επαλήθευση του email.")
            print(f"Database error: {e}")
            return {"scheduled_meeting_teacher_email": None, "scheduled_meeting_correct_teacher_email": None}

    def validate_scheduled_meeting_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate cuisine value."""
        try:
            date_obj = datetime.strptime(slot_value, "%d/%m/%Y")
            today = datetime.today()
            min_date = today + timedelta(days=1)
            max_date = today + timedelta(days=30)
            if  min_date > date_obj or max_date < date_obj:
                dispatcher.utter_message(response="utter_schedule_date_lt_gt_available")
                return {"scheduled_meeting_date": None ,
                        "scheduled_meeting_correct_date": None,
                        "scheduled_meeting_min_date": None,
                        "scheduled_meeting_max_date": None
                       }
            else:
                return {"scheduled_meeting_date": slot_value}
        except ValueError:
            return {"scheduled_meeting_date": None ,
                    "scheduled_meeting_correct_date": None,
                    "scheduled_meeting_min_date": None,
                    "scheduled_meeting_max_date": None
                    }

    def validate_scheduled_meeting_correct_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if tracker.get_slot("scheduled_meeting_correct_date"):
            return {"scheduled_meeting_date": tracker.get_slot("scheduled_meeting_teacher_email"), "scheduled_meeting_correct_date": True}
        return {"scheduled_meeting_date": None, 
                "scheduled_meeting_correct_date": None, 
                "scheduled_meeting_min_date": None, 
                "scheduled_meeting_max_date": None
                }

class ActionScheduleMeetingWithTeacher(Action):
    def name(self) -> str:
        return "action_schedule_meeting_with_teacher"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_confirm_meeting_with_teacher_scheduled")
        return []

class ActionScheduleMeetingWithTeacherReset(Action):
    def name(self) -> str:
        return "action_schedule_meeting_with_teacher_reset"

    def run(self,  dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # reset all related slots
        print("resetting form data for schedule_meeting_with_teacher")
        
        return [
            SlotSet("scheduled_meeting_teacher_email", None),
            SlotSet("scheduled_meeting_correct_teacher_email", None),
            SlotSet("scheduled_meeting_date", None),
            SlotSet("scheduled_meeting_correct_date",None),
            SlotSet("scheduled_meeting_min_date", None),
            SlotSet("scheduled_meeting_max_date", None)
        ]

class ActionGetNextAvailableCourse(Action):
    def name(self) -> str:
        return "action_get_next_available_course"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_id = tracker.get_slot("uid")
        print(f"user {user_id} requested the next available course")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(f"SELECT semester FROM student_info WHERE user_id = {user_id};")
        user_semester = cur.fetchone()[0]
        user_team = get_user_team(user_semester, user_id)
        
        today = datetime.now()
        current_time = today.time()
        current_day = today.weekday() + 1  # Monday = 1, Sunday = 7
        
        print(f"user_team: {user_team}")
        print(f"current_time: {current_time}")
        print(f"current_day: {current_day}")
        
        # First, check for courses today that haven't started yet
        query_today = """
        SELECT c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
        FROM student_enrollments se
        JOIN class_schedules cs ON se.class_id = cs.class_id
        JOIN classes c ON cs.class_id = c.class_id
        WHERE se.user_id = %s 
        AND cs.day_of_week = %s
        AND cs.class_team = %s
        AND cs.start_time > %s
        GROUP BY c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
        ORDER BY cs.start_time ASC
        LIMIT 1;
        """
        
        cur.execute(query_today, (user_id, current_day, user_team, current_time))
        course_today = cur.fetchone()
        
        if course_today:
            class_name, classroom, day_of_week, start_time, end_time = course_today
            dispatcher.utter_message(text="Βρήκα το επόμενο διαθέσιμο μάθημά σου για σήμερα!")
            dispatcher.utter_message(text=f"Μάθημα: {class_name}")
            dispatcher.utter_message(text=f"Αίθουσα: {classroom}")
            dispatcher.utter_message(text=f"Ώρα: {start_time} - {end_time}")
            dispatcher.utter_message(text=f"Σήμερα ({days[day_of_week-1]})")
            cur.close()
            conn.close()
            return [
                SlotSet("last_course_name_provided_by_bot", class_name),
                SlotSet("conversation_context", "course_schedule")
            ]
        
        # If no course today, find the next available course on subsequent days
        query_next_days = """
        SELECT c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
        FROM student_enrollments se
        JOIN class_schedules cs ON se.class_id = cs.class_id
        JOIN classes c ON cs.class_id = c.class_id
        WHERE se.user_id = %s 
        AND cs.day_of_week > %s
        AND cs.class_team = %s
        GROUP BY c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
        ORDER BY cs.day_of_week ASC, cs.start_time ASC
        LIMIT 1;
        """
        
        cur.execute(query_next_days, (user_id, current_day, user_team))
        course_next_days = cur.fetchone()
        
        if course_next_days:
            class_name, classroom, day_of_week, start_time, end_time = course_next_days
            days_ahead = (day_of_week - 1) - today.weekday()
            if days_ahead < 0:
                days_ahead += 7  # Next week
            target_date = today + timedelta(days=days_ahead)
            
            dispatcher.utter_message(text="Βρήκα το επόμενο διαθέσιμο μάθημά σου!")
            dispatcher.utter_message(text=f"Μάθημα: {class_name}")
            dispatcher.utter_message(text=f"Αίθουσα: {classroom}")
            dispatcher.utter_message(text=f"Ώρα: {start_time} - {end_time}")
            dispatcher.utter_message(text=f"Ημερομηνία: {target_date.strftime('%d/%m/%Y')} ({days[day_of_week-1]})")
            cur.close()
            conn.close()
            return [
                SlotSet("last_course_name_provided_by_bot", class_name),
                SlotSet("conversation_context", "course_schedule")
            ]
        
        # If no course this week, check next week starting from Monday
        query_next_week = """
        SELECT c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
        FROM student_enrollments se
        JOIN class_schedules cs ON se.class_id = cs.class_id
        JOIN classes c ON cs.class_id = c.class_id
        WHERE se.user_id = %s 
        AND cs.class_team = %s
        GROUP BY c.class_name, cs.classroom, cs.day_of_week, cs.start_time, cs.end_time
        ORDER BY cs.day_of_week ASC, cs.start_time ASC
        LIMIT 1;
        """
        
        cur.execute(query_next_week, (user_id, user_team))
        course_next_week = cur.fetchone()
        
        if course_next_week:
            class_name, classroom, day_of_week, start_time, end_time = course_next_week
            days_ahead = (day_of_week - 1) - today.weekday() + 7  # Next week
            target_date = today + timedelta(days=days_ahead)
            
            dispatcher.utter_message(text="Βρήκα το επόμενο διαθέσιμο μάθημά σου για την επόμενη εβδομάδα!")
            dispatcher.utter_message(text=f"Μάθημα: {class_name}")
            dispatcher.utter_message(text=f"Αίθουσα: {classroom}")
            dispatcher.utter_message(text=f"Ώρα: {start_time} - {end_time}")
            dispatcher.utter_message(text=f"Ημερομηνία: {target_date.strftime('%d/%m/%Y')} ({days[day_of_week-1]})")
            cur.close()
            conn.close()
            return [
                SlotSet("last_course_name_provided_by_bot", class_name),
                SlotSet("conversation_context", "course_schedule")
            ]
        
        # If no courses found at all
        dispatcher.utter_message(text="Δεν βρήκα κάποιο διαθέσιμο μάθημα στο πρόγραμμά σου. Παρακαλώ επικοινώνησε με τη γραμματεία του τμήματος.")
        cur.close()
        conn.close()
        return []

class ActionGetTeacherOfThisCourse(Action):
    def name(self) -> str:
        return "action_get_teacher_of_this_course"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the last course name that was provided by the bot
        last_course_name = tracker.get_slot("last_course_name_provided_by_bot")
        
        if not last_course_name:
            dispatcher.utter_message(text="Δεν έχω αναφέρει κάποιο συγκεκριμένο μάθημα πρόσφατα. Παρακαλώ ρώτησε για συγκεκριμένο μάθημα.")
            return []
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        try:
            # Get class_id from course name
            cur.execute("SELECT class_id FROM classes WHERE class_name = %s;", (last_course_name,))
            result = cur.fetchone()
            
            if not result:
                dispatcher.utter_message(text=f"Δεν βρήκα στοιχεία για το μάθημα '{last_course_name}'.")
                cur.close()
                conn.close()
                return []
            
            class_id = result[0]
            
            # Get teachers for this course
            query = """
            SELECT u.first_name, u.last_name FROM
            class_schedules cs 
            JOIN users u on cs.teacher_id = u.user_id 
            WHERE cs.class_id = %s
            GROUP BY u.first_name, u.last_name;
            """
            
            cur.execute(query, (class_id,))
            teachers = cur.fetchall()
            
            if not teachers:
                dispatcher.utter_message(text=f"Δεν βρήκα καθηγητή για το μάθημα '{last_course_name}'.")
                cur.close()
                conn.close()
                return []
            
            if len(teachers) == 1:
                first_name, last_name = teachers[0]
                teacher_name = f"{first_name} {last_name}" if first_name else last_name
                dispatcher.utter_message(text=f"Το μάθημα '{last_course_name}' διδάσκεται από τον/την {teacher_name}.")
                
                # Update slots to track this information
                return [
                    SlotSet("last_teacher_name_provided_by_bot", teacher_name),
                    SlotSet("last_teacher_name_list_provided_by_bot", None),
                    SlotSet("course_teacher_name_found", True),
                    SlotSet("course_teacher_name_found_multiple", False)
                ]
            else:
                # Multiple teachers
                teacher_names = []
                for first_name, last_name in teachers:
                    teacher_name = f"{first_name} {last_name}" if first_name else last_name
                    teacher_names.append(teacher_name)
                
                dispatcher.utter_message(text=f"Το μάθημα '{last_course_name}' διδάσκεται από τους: {', '.join(teacher_names)}.")
                
                # Update slots to track this information
                return [
                    SlotSet("last_teacher_name_provided_by_bot", None),
                    SlotSet("last_teacher_name_list_provided_by_bot", teacher_names),
                    SlotSet("course_teacher_name_found", True),
                    SlotSet("course_teacher_name_found_multiple", True)
                ]
                
        except Exception as e:
            print(f"Database error: {e}")
            dispatcher.utter_message(text="Υπήρξε ένα σφάλμα κατά την αναζήτηση του καθηγητή.")
            cur.close()
            conn.close()
            return []

class ActionOfferContextualHelp(Action):
    def name(self) -> str:
        return "action_offer_contextual_help"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        last_course_name = tracker.get_slot("last_course_name_provided_by_bot")
        conversation_context = tracker.get_slot("conversation_context")
        last_successful_query_type = tracker.get_slot("last_successful_query_type")
        
        # Offer contextual help based on what was just discussed
        if last_course_name and conversation_context == "course_schedule":
            dispatcher.utter_message(
                text=f"Θέλεις να μάθεις κι άλλα στοιχεία για το μάθημα '{last_course_name}'; "
                     f"Μπορώ να σου πω ποιος είναι ο καθηγητής ή σε ποια αίθουσα γίνεται."
            )
        elif conversation_context == "course_teacher":
            dispatcher.utter_message(
                text="Θέλεις να μάθεις κάτι άλλο για αυτό το μάθημα; "
                     "Μπορώ να σου δώσω πληροφορίες για το πρόγραμμα ή την αίθουσα."
            )
        elif conversation_context == "course_classroom":
            dispatcher.utter_message(
                text="Υπάρχει κάτι άλλο που θα ήθελες να μάθεις για αυτό το μάθημα; "
                     "Μπορώ να σου πω πότε είναι το επόμενο ή ποιος είναι ο καθηγητής."
            )
        else:
            # Default contextual help
            dispatcher.utter_message(text="Υπάρχει κάτι άλλο που μπορώ να κάνω για εσένα;")
        
        return []

class ActionSuggestCourseRelatedInfo(Action):
    def name(self) -> str:
        return "action_suggest_course_related_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        last_course_name = tracker.get_slot("last_course_name_provided_by_bot")
        
        if last_course_name:
            dispatcher.utter_message(
                text=f"Για το μάθημα '{last_course_name}' μπορώ επίσης να σου δώσω:",
                buttons=[
                    {"title": "Ποιος είναι ο καθηγητής;", "payload": "/ask_teacher_of_this_course"},
                    {"title": "Σε ποια αίθουσα γίνεται;", "payload": f"/ask_course_classroom_by_course_name{{\"course_name\":\"{last_course_name}\"}}"},
                    {"title": "Πότε είναι το επόμενο;", "payload": f"/ask_next_schedule_of_course_by_course_name{{\"course_name\":\"{last_course_name}\"}}"}
                ]
            )
        else:
            dispatcher.utter_message(text="Τι άλλο θα ήθελες να μάθεις;")
        
        return []

class ActionTrackConversationContext(Action):
    def name(self) -> str:
        return "action_track_conversation_context"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        last_intent = tracker.latest_message['intent'].get('name')
        
        context_mapping = {
            "ask_next_course_schedule_today": "course_schedule", 
            "ask_next_available_course": "course_schedule",
            "ask_next_schedule_of_course_by_course_name": "course_schedule",
            "ask_course_teacher_by_course_name": "course_teacher",
            "ask_teacher_of_this_course": "course_teacher",
            "ask_course_classroom_by_course_name": "course_classroom",
            "ask_educational_question": "educational_help",
            "ask_educational_question_from_pdf": "educational_help"
        }
        
        conversation_context = context_mapping.get(last_intent, "general")
        
        events = tracker.events[-5:]
        user_events = [e for e in events if e.get("event") == "user"]
        
        if len(user_events) >= 3:
            engagement_level = "high"
        elif len(user_events) >= 2:
            engagement_level = "medium" 
        else:
            engagement_level = "low"
        
        return [
            SlotSet("conversation_context", conversation_context),
            SlotSet("last_successful_query_type", last_intent),
            SlotSet("user_engagement_level", engagement_level)
        ]

class ActionSuggestSimilarCourses(Action):
    def name(self) -> str:
        return "action_suggest_similar_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        course_name = next(tracker.get_latest_entity_values("course_name"), None)
        
        if course_name:
            dispatcher.utter_message(
                text=f"Δεν βρήκα το μάθημα '{course_name}'. Μήπως εννοούσες κάποιο από αυτά:",
                buttons=[
                    {"title": "Δείξε μου όλα τα μαθήματα", "payload": "/ask_bot_supplied_services"},
                    {"title": "Βοήθεια", "payload": "/ask_help"},
                    {"title": "Δοκίμασε ξανά", "payload": "/ask_course_classroom_by_course_name"}
                ]
            )
        else:
            dispatcher.utter_message(
                text="Δεν κατάφερα να καταλάβω ποιο μάθημα θέλεις. Μπορείς να το ξαναπείς;",
                buttons=[
                    {"title": "Δείξε μου τις επιλογές", "payload": "/ask_bot_supplied_services"}
                ]
            )
        
        return []

class ActionOfferCourseAlternatives(Action):
    def name(self) -> str:
        return "action_offer_course_alternatives"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="Μπορώ να σε βοηθήσω με άλλες πληροφορίες:",
            buttons=[
                {"title": "Επόμενο διαθέσιμο μάθημα", "payload": "/ask_next_available_course"},
                {"title": "Πρόγραμμα εβδομάδας", "payload": "/user_asks_schedule_rest_of_the_week"},
                {"title": "Γραμματεία τμήματος", "payload": "/get_department_secretariat_info"}
            ]
        )
        
        return []

class ActionClarifyCourseForTeacherQuery(Action):
    def name(self) -> str:
        return "action_clarify_course_for_teacher_query"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="Για να σου πω ποιος είναι ο καθηγητής, χρειάζομαι να ξέρω για ποιο μάθημα ρωτάς:",
            buttons=[
                {"title": "Πες μου το επόμενο μάθημα", "payload": "/ask_next_available_course"},
                {"title": "Ρώτησε για συγκεκριμένο μάθημα", "payload": "/ask_course_teacher_by_course_name"}
            ]
        )
        
        return []
