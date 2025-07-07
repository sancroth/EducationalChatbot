from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import psycopg2
import os
from datetime import datetime, timedelta

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "ice"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "mysecretpassword"),
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432")
}

days = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή"]

class ActionSmartScheduleQuery(Action):
    """Smart schedule query that clarifies vague requests"""
    
    def name(self) -> str:
        return "action_smart_schedule_query"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_id = tracker.get_slot("uid")
        course_name = next(tracker.get_latest_entity_values("course_name"), None)
        
        # Analyze the user's message for context clues
        user_message = tracker.latest_message.get("text", "").lower()
        
        # If no specific course mentioned, offer smart clarification
        if not course_name:
            # Check what kind of schedule they want
            if any(word in user_message for word in ["σήμερα", "today"]):
                return self._handle_today_schedule(dispatcher, user_id)
            elif any(word in user_message for word in ["αύριο", "tomorrow"]):
                return self._handle_tomorrow_schedule(dispatcher, user_id)
            elif any(word in user_message for word in ["επόμενο", "next"]):
                return self._handle_next_class(dispatcher, user_id, tracker, domain)
            else:
                # Offer clarification with smart suggestions
                return self._offer_schedule_clarification(dispatcher, user_id)
        else:
            # They mentioned a specific course - be more specific
            return self._handle_specific_course_query(dispatcher, user_id, course_name)
    
    def _handle_today_schedule(self, dispatcher, user_id):
        """Handle 'what classes do I have today?'"""
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        try:
            cur.execute(f"SELECT semester FROM student_info WHERE user_id = {user_id};")
            user_semester = cur.fetchone()[0]
            user_team = self._get_user_team(user_semester, user_id)
            
            today = datetime.now()
            current_day = today.weekday() + 1
            current_time = today.time()
            
            # Get remaining classes today
            query = """
            SELECT c.class_name, cs.classroom, cs.start_time, cs.end_time
            FROM student_enrollments se
            JOIN class_schedules cs ON se.class_id = cs.class_id
            JOIN classes c ON cs.class_id = c.class_id
            WHERE se.user_id = %s 
            AND cs.day_of_week = %s
            AND cs.class_team = %s
            AND cs.start_time > %s
            ORDER BY cs.start_time;
            """
            
            cur.execute(query, (user_id, current_day, user_team, current_time))
            remaining_classes = cur.fetchall()
            
            if not remaining_classes:
                dispatcher.utter_message(text="Δεν έχεις άλλα μαθήματα σήμερα! 🎉 Ελεύθερος για τον υπόλοιπο χρόνο!")
                
                # Suggest tomorrow's schedule
                dispatcher.utter_message(
                    text="Θέλεις να δεις το πρόγραμμα για αύριο;",
                    buttons=[
                        {"title": "Ναι, δείξε μου αύριο", "payload": "/ask_tomorrow_schedule"},
                        {"title": "Όχι, ευχαριστώ", "payload": "/user_deny"}
                    ]
                )
            else:
                response = f"Σήμερα έχεις ακόμη {len(remaining_classes)} μάθημα/τα:\n\n"
                for class_name, classroom, start_time, end_time in remaining_classes:
                    response += f"📚 {class_name}\n⏰ {start_time} - {end_time}\n📍 {classroom}\n\n"
                
                dispatcher.utter_message(text=response)
                
                # Smart follow-up
                next_class = remaining_classes[0]
                time_until = datetime.combine(today.date(), next_class[2]) - today
                minutes_until = int(time_until.total_seconds() / 60)
                
                if minutes_until > 60:
                    dispatcher.utter_message(
                        text=f"Το επόμενο μάθημα είναι σε {minutes_until // 60} ώρες. Θέλεις προτάσεις για το τι μπορείς να κάνεις στο μεταξύ;",
                        buttons=[
                            {"title": "Προτάσεις για διάλειμμα", "payload": "/ask_break_suggestions"},
                            {"title": "Όχι, ευχαριστώ", "payload": "/user_deny"}
                        ]
                    )
                elif minutes_until > 15:
                    dispatcher.utter_message(text=f"Το επόμενο μάθημα είναι σε {minutes_until} λεπτά. Καλή προετοιμασία! 📖")
                else:
                    dispatcher.utter_message(text=f"Το επόμενο μάθημα αρχίζει σε {minutes_until} λεπτά. Ώρα να πας! 🏃‍♂️")
            
            return [SlotSet("last_course_name_provided_by_bot", remaining_classes[0][0] if remaining_classes else None)]
            
        finally:
            cur.close()
            conn.close()
    
    def _handle_tomorrow_schedule(self, dispatcher, user_id):
        """Handle 'what classes do I have tomorrow?'"""
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        try:
            cur.execute(f"SELECT semester FROM student_info WHERE user_id = {user_id};")
            user_semester = cur.fetchone()[0]
            user_team = self._get_user_team(user_semester, user_id)
            
            today = datetime.now()
            tomorrow_day = (today.weekday() + 1) % 7 + 1
            
            if tomorrow_day > 5:  # Weekend
                dispatcher.utter_message(text="Αύριο είναι Σαββατοκύριακο! Δεν έχεις μαθήματα. 🎉")
                
                # Find next Monday
                days_until_monday = (7 - today.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                
                dispatcher.utter_message(
                    text=f"Τα μαθήματα συνεχίζονται σε {days_until_monday} μέρες (Δευτέρα). Θέλεις να δεις το πρόγραμμα;",
                    buttons=[
                        {"title": "Ναι, δείξε μου Δευτέρα", "payload": "/ask_monday_schedule"},
                        {"title": "Όχι, ευχαριστώ", "payload": "/user_deny"}
                    ]
                )
                return []
            
            query = """
            SELECT c.class_name, cs.classroom, cs.start_time, cs.end_time
            FROM student_enrollments se
            JOIN class_schedules cs ON se.class_id = cs.class_id
            JOIN classes c ON cs.class_id = c.class_id
            WHERE se.user_id = %s 
            AND cs.day_of_week = %s
            AND cs.class_team = %s
            ORDER BY cs.start_time;
            """
            
            cur.execute(query, (user_id, tomorrow_day, user_team))
            tomorrow_classes = cur.fetchall()
            
            if not tomorrow_classes:
                dispatcher.utter_message(text="Αύριο δεν έχεις μαθήματα! Ελεύθερη μέρα! 🎉")
            else:
                response = f"Αύριο ({days[tomorrow_day-1]}) έχεις {len(tomorrow_classes)} μάθημα/τα:\n\n"
                for class_name, classroom, start_time, end_time in tomorrow_classes:
                    response += f"📚 {class_name}\n⏰ {start_time} - {end_time}\n📍 {classroom}\n\n"
                
                dispatcher.utter_message(text=response)
                
                # Smart suggestions
                first_class = tomorrow_classes[0]
                dispatcher.utter_message(
                    text=f"Το πρώτο μάθημα αρχίζει στις {first_class[2]}. Θέλεις υπενθύμιση ή άλλες πληροφορίες;",
                    buttons=[
                        {"title": "Ποιος είναι ο καθηγητής;", "payload": f"/ask_course_teacher_by_course_name{{\"course_name\":\"{first_class[0]}\"}}"},
                        {"title": "Τι άλλο έχω αύριο;", "payload": "/ask_tomorrow_full_schedule"},
                        {"title": "Όχι, ευχαριστώ", "payload": "/user_deny"}
                    ]
                )
            
            return [SlotSet("last_course_name_provided_by_bot", tomorrow_classes[0][0] if tomorrow_classes else None)]
            
        finally:
            cur.close()
            conn.close()
    
    def _handle_next_class(self, dispatcher, user_id, tracker, domain):
        """Handle 'when is my next class?'"""
        # Use the existing next available course action but with smarter follow-up
        from actions import ActionGetNextAvailableCourse
        
        action = ActionGetNextAvailableCourse()
        result = action.run(dispatcher, tracker, domain)
        
        # Add smart follow-up based on timing
        today = datetime.now()
        if today.hour < 8:
            dispatcher.utter_message(text="Νωρίς ξύπνησες σήμερα! Καλή μέρα! ☀️")
        elif today.hour > 18:
            dispatcher.utter_message(text="Προγραμματίζεις για αύριο; Καλή ιδέα! 📅")
        
        return result
    
    def _offer_schedule_clarification(self, dispatcher, user_id):
        """Offer smart clarification when query is vague"""
        now = datetime.now()
        
        # Provide context-aware options
        if now.hour < 8:
            primary_suggestion = "Σήμερα"
            secondary = "Αύριο"
        elif now.hour > 17:
            primary_suggestion = "Αύριο"
            secondary = "Υπόλοιπη εβδομάδα"
        else:
            primary_suggestion = "Σήμερα (υπόλοιπο)"
            secondary = "Αύριο"
        
        dispatcher.utter_message(
            text="Για ποιο διάστημα θέλεις να δεις το πρόγραμμα;",
            buttons=[
                {"title": primary_suggestion, "payload": "/ask_today_remaining_schedule"},
                {"title": secondary, "payload": "/ask_tomorrow_schedule"},
                {"title": "Επόμενο μάθημα", "payload": "/ask_next_available_course"},
                {"title": "Όλη την εβδομάδα", "payload": "/user_asks_schedule_rest_of_the_week"}
            ]
        )
        
        return [SlotSet("conversation_context", "schedule_clarification")]
    
    def _handle_specific_course_query(self, dispatcher, user_id, course_name):
        """Handle queries about specific courses with smart follow-ups"""
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        try:
            # First try exact match
            cur.execute("SELECT class_id, class_name FROM classes WHERE class_name = %s", (course_name,))
            course = cur.fetchone()
            
            if not course:
                # Try fuzzy matching
                cur.execute("SELECT class_id, class_name FROM classes WHERE class_name ILIKE %s", (f"%{course_name}%",))
                matches = cur.fetchall()
                
                if not matches:
                    dispatcher.utter_message(text=f"Δεν βρήκα μάθημα με το όνομα '{course_name}'. Μπορείς να το πεις πιο συγκεκριμένα;")
                    
                    # Suggest similar courses
                    words = course_name.split()
                    if words:
                        cur.execute("SELECT DISTINCT class_name FROM classes WHERE class_name ILIKE %s LIMIT 3", (f"%{words[0]}%",))
                        suggestions = cur.fetchall()
                        
                        if suggestions:
                            dispatcher.utter_message(
                                text="Μήπως εννοούσες κάποιο από αυτά;",
                                buttons=[{"title": sug[0], "payload": f"/ask_course_info{{\"course_name\":\"{sug[0]}\"}}"} for sug in suggestions]
                            )
                elif len(matches) == 1:
                    course = matches[0]
                    dispatcher.utter_message(text=f"Βρήκα το μάθημα: {course[1]}")
                    return self._provide_course_info(dispatcher, user_id, course[1])
                else:
                    # Multiple matches - let user choose
                    dispatcher.utter_message(
                        text=f"Βρήκα {len(matches)} μαθήματα που περιέχουν '{course_name}'. Ποιο εννοούσες;",
                        buttons=[{"title": match[1], "payload": f"/ask_course_info{{\"course_name\":\"{match[1]}\"}}"} for match in matches[:3]]
                    )
                    return []
            
            return self._provide_course_info(dispatcher, user_id, course[1])
            
        finally:
            cur.close()
            conn.close()
    
    def _provide_course_info(self, dispatcher, user_id, course_name):
        """Provide comprehensive course information with smart follow-ups"""
        # This would integrate with existing course info actions
        # but provide smarter follow-up suggestions
        
        dispatcher.utter_message(
            text=f"Τι θέλεις να μάθεις για το μάθημα '{course_name}';",
            buttons=[
                {"title": "Πότε είναι το επόμενο;", "payload": f"/ask_next_schedule_of_course_by_course_name{{\"course_name\":\"{course_name}\"}}"},
                {"title": "Ποιος είναι ο καθηγητής;", "payload": f"/ask_course_teacher_by_course_name{{\"course_name\":\"{course_name}\"}}"},
                {"title": "Σε ποια αίθουσα;", "payload": f"/ask_course_classroom_by_course_name{{\"course_name\":\"{course_name}\"}}"},
                {"title": "Όλες τις πληροφορίες", "payload": f"/ask_course_full_info{{\"course_name\":\"{course_name}\"}}"}
            ]
        )
        
        return [SlotSet("last_course_name_provided_by_bot", course_name)]
    
    def _get_user_team(self, user_semester, user_id):
        """Calculate user team based on semester and ID"""
        if user_semester == 1:
            if user_id % 10 in (7, 8, 9):
                return 2
        else:
            if user_id % 2 == 1:
                return 2
        return 1


class ActionProvideBreakSuggestions(Action):
    """Provide intelligent break suggestions based on schedule and time"""
    
    def name(self) -> str:
        return "action_provide_break_suggestions"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_id = tracker.get_slot("uid")
        
        # Get current context
        now = datetime.now()
        current_time = now.time()
        current_day = now.weekday() + 1
        
        # Get user's next class timing
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        try:
            # Get user semester and team
            cur.execute(f"SELECT semester FROM student_info WHERE user_id = {user_id};")
            user_semester = cur.fetchone()[0]
            user_team = self._get_user_team(user_semester, user_id)
            
            # Find next class today
            query = """
            SELECT c.class_name, cs.classroom, cs.start_time, cs.end_time
            FROM student_enrollments se
            JOIN class_schedules cs ON se.class_id = cs.class_id
            JOIN classes c ON cs.class_id = c.class_id
            WHERE se.user_id = %s 
            AND cs.day_of_week = %s
            AND cs.class_team = %s
            AND cs.start_time > %s
            ORDER BY cs.start_time
            LIMIT 1;
            """
            
            cur.execute(query, (user_id, current_day, user_team, current_time))
            next_class = cur.fetchone()
            
            if next_class:
                # Calculate time until next class
                next_start = datetime.combine(now.date(), next_class[2])
                time_until = next_start - now
                minutes_until = int(time_until.total_seconds() / 60)
                
                suggestions = self._generate_break_suggestions(minutes_until, current_time)
                
                dispatcher.utter_message(
                    text=f"Έχεις {minutes_until} λεπτά μέχρι το επόμενο μάθημα ({next_class[0]}). Ιδέες για το διάλειμμα:"
                )
                
                for suggestion in suggestions:
                    dispatcher.utter_message(text=f"• {suggestion}")
                
                # Add contextual buttons
                if minutes_until > 30:
                    dispatcher.utter_message(
                        text="Θέλεις περισσότερες προτάσεις ή άλλες πληροφορίες;",
                        buttons=[
                            {"title": "Που είναι η βιβλιοθήκη;", "payload": "/ask_library_location"},
                            {"title": "Που μπορώ να φάω;", "payload": "/ask_food_options"},
                            {"title": "Τι άλλο έχω σήμερα;", "payload": "/ask_today_schedule"},
                            {"title": "Όχι, ευχαριστώ", "payload": "/user_deny"}
                        ]
                    )
                else:
                    dispatcher.utter_message(
                        text="Θέλεις να δεις που είναι η αίθουσα του επόμενου μαθήματος;",
                        buttons=[
                            {"title": "Ναι, δείξε μου", "payload": f"/ask_course_classroom_by_course_name{{\"course_name\":\"{next_class[0]}\"}"}"},
                            {"title": "Όχι, ευχαριστώ", "payload": "/user_deny"}
                        ]
                    )
            else:
                # No more classes today
                dispatcher.utter_message(text="Δεν έχεις άλλα μαθήματα σήμερα! Ελεύθερος χρόνος! 🎉")
                
                end_of_day_suggestions = [
                    "📚 Διάβασε για τα μαθήματα αύριο",
                    "🏃‍♂️ Κάνε μια βόλτα στον κήπο της σχολής",
                    "📖 Πήγαινε στη βιβλιοθήκη για μελέτη",
                    "👥 Συναντήσου με συμφοιτητές",
                    "🍕 Πήγαινε για φαγητό",
                    "🏠 Γύρνα σπίτι και ξεκουράσου"
                ]
                
                dispatcher.utter_message(text="Προτάσεις για τον ελεύθερο χρόνο:")
                for suggestion in end_of_day_suggestions:
                    dispatcher.utter_message(text=f"• {suggestion}")
                
                dispatcher.utter_message(
                    text="Θέλεις να δεις το πρόγραμμα για αύριο;",
                    buttons=[
                        {"title": "Ναι, δείξε μου αύριο", "payload": "/ask_tomorrow_schedule"},
                        {"title": "Όχι, ευχαριστώ", "payload": "/user_deny"}
                    ]
                )
            
            return [SlotSet("conversation_context", "break_suggestions")]
            
        finally:
            cur.close()
            conn.close()
    
    def _generate_break_suggestions(self, minutes_until, current_time):
        """Generate context-aware break suggestions"""
        suggestions = []
        
        if minutes_until <= 10:
            suggestions = [
                "🚶‍♂️ Πήγαινε στην αίθουσα νωρίς",
                "💧 Πάρε λίγο νερό",
                "📱 Έλεγξε τις σημειώσεις σου"
            ]
        elif minutes_until <= 30:
            suggestions = [
                "☕ Πάρε έναν καφέ από τη καφετέρια",
                "🚻 Πήγαινε στην τουαλέτα",
                "📚 Ρίξε μια ματιά στο επόμενο μάθημα",
                "🗣️ Μίλησε με συμφοιτητές"
            ]
        elif minutes_until <= 60:
            suggestions = [
                "🍽️ Πήγαινε για φαγητό στη καφετέρια",
                "📖 Πήγαινε στη βιβλιοθήκη για μελέτη",
                "🏃‍♂️ Κάνε μια μικρή βόλτα",
                "📱 Κάλεσε κάποιον φίλο",
                "✍️ Οργάνωσε τις σημειώσεις σου"
            ]
        else:
            suggestions = [
                "🍕 Πήγαινε για φαγητό έξω από τη σχολή",
                "🏪 Κάνε ψώνια στο κέντρο",
                "🏃‍♂️ Πήγαινε για γυμναστική",
                "📚 Μελέτη στη βιβλιοθήκη",
                "👥 Κάνε παρέα με φίλους",
                "🏠 Πήγαινε σπίτι για διάλειμμα"
            ]
        
        # Add time-specific suggestions
        hour = current_time.hour
        if 11 <= hour <= 13:
            suggestions.insert(0, "🥙 Ώρα για φαγητό!")
        elif 15 <= hour <= 17:
            suggestions.insert(0, "☕ Ώρα για απογευματινό καφέ!")
        elif hour >= 18:
            suggestions.insert(0, "🌅 Η μέρα τελειώνει, χαλάρωσε!")
        
        return suggestions
    
    def _get_user_team(self, user_semester, user_id):
        """Calculate user team based on semester and ID"""
        if user_semester == 1:
            if user_id % 10 in (7, 8, 9):
                return 2
        else:
            if user_id % 2 == 1:
                return 2
        return 1