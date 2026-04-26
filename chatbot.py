import re
import sqlite3
from datetime import datetime, timedelta
from database import Database
import calendar

class AttendanceChatbot:
    def __init__(self, db_instance=None):
        self.db = db_instance if db_instance else Database()
        self.current_user = None  # Will be set based on login
        self.user_role = "student"  # "student" or "teacher"
        
        # Define intent patterns
        self.intent_patterns = {
            'attendance_check': [
                r'did i attend.*',
                r'was i present.*',
                r'my attendance.*yesterday.*',
                r'attendance.*yesterday.*',
                r'present.*yesterday.*'
            ],
            'student_attendance_check': [
                r'tell me.*attendance.*',
                r'show.*attendance.*',
                r'.*attendance.*for.*',
                r'check.*attendance.*',
                r'get.*attendance.*'
            ],
            'student_percentage': [
                r'.*percentage.*for.*',
                r'.*attendance.*rate.*for.*',
                r'show.*percentage.*'
            ],
            'student_absence_count': [
                r'how many.*absent.*for.*',
                r'.*absence.*count.*for.*',
                r'.*missed.*classes.*for.*'
            ],
            'absence_count': [
                r'how many.*absent.*',
                r'total.*absent.*',
                r'absent.*days.*',
                r'missed.*classes.*'
            ],
            'attendance_percentage': [
                r'attendance.*percentage.*',
                r'my.*percentage.*',
                r'attendance.*rate.*',
                r'what.*percentage.*'
            ],
            'class_attendance': [
                r'who.*absent.*today.*',
                r'class.*attendance.*',
                r'attendance.*report.*',
                r'show.*attendance.*class.*'
            ],
            'help': [
                r'help.*',
                r'how.*work.*',
                r'what.*do.*',
                r'commands.*',
                r'support.*'
            ],
            'greeting': [
                r'^hi$|^hello$|^hey$',
                r'good morning|good afternoon|good evening'
            ]
        }
        
    def set_user(self, user_id, role="student"):
        """Set the current user context"""
        self.current_user = user_id
        self.user_role = role
    
    def classify_intent(self, message):
        """Classify user message intent using regex patterns"""
        message = message.lower().strip()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return intent
        
        return 'unknown'
    
    def extract_entities(self, message):
        """Extract entities like dates, class names, student names, etc."""
        entities = {}
        
        # Extract dates
        today_patterns = r'today|now'
        yesterday_patterns = r'yesterday'
        month_patterns = r'this month|current month'
        week_patterns = r'this week|current week'
        
        if re.search(today_patterns, message, re.IGNORECASE):
            entities['date'] = datetime.now().strftime('%Y-%m-%d')
        elif re.search(yesterday_patterns, message, re.IGNORECASE):
            entities['date'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif re.search(month_patterns, message, re.IGNORECASE):
            entities['period'] = 'month'
        elif re.search(week_patterns, message, re.IGNORECASE):
            entities['period'] = 'week'
        
        # Extract class names (assuming format like "Class 10-A", "Grade 5", etc.)
        class_pattern = r'class\s+(\d+[-]?[A-Z]?)|grade\s+(\d+)'
        class_match = re.search(class_pattern, message, re.IGNORECASE)
        if class_match:
            entities['class'] = class_match.group(0)
        
        # Extract student names - look for names in common patterns
        student_name = self.extract_student_name(message)
        if student_name:
            entities['student_name'] = student_name
        
        return entities
    
    def extract_student_name(self, message):
        """Extract student name from the message"""
        # Common patterns for mentioning student names
        patterns = [
            r'tell me (.+?)(?:\s+attendance|\s+percentage|$)',
            r'show (.+?)(?:\s+attendance|\s+percentage|$)', 
            r'check (.+?)(?:\s+attendance|\s+percentage|$)',
            r'get (.+?)(?:\s+attendance|\s+percentage|$)',
            r'(.+?)(?:\'s|s)\s+attendance',
            r'(.+?)(?:\'s|s)\s+percentage',
            r'attendance.*for\s+(.+?)(?:\s|$)',
            r'percentage.*for\s+(.+?)(?:\s|$)',
            r'absent.*for\s+(.+?)(?:\s|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up common words that aren't names
                stop_words = ['me', 'my', 'the', 'a', 'an', 'attendance', 'percentage', 'today', 'yesterday']
                if name.lower() not in stop_words and len(name) > 1:
                    return name.title()  # Capitalize properly
        
        return None
    
    def find_student_by_name(self, name):
        """Find student by name (fuzzy matching)"""
        try:
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()
            
            # First try exact match
            cursor.execute("SELECT id, name, class FROM students WHERE LOWER(name) = ?", (name.lower(),))
            result = cursor.fetchone()
            
            if result:
                conn.close()
                return result
            
            # Try partial match (contains)
            cursor.execute("SELECT id, name, class FROM students WHERE LOWER(name) LIKE ?", (f'%{name.lower()}%',))
            results = cursor.fetchall()
            
            conn.close()
            
            if results:
                # Return the first match if multiple found
                return results[0]
            
            return None
        except Exception as e:
            print(f"Error finding student: {e}")
            return None
    
    def get_student_attendance_status(self, student_id, date):
        """Get attendance status for a specific student and date"""
        try:
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status, time FROM attendance 
                WHERE student_id = ? AND date = ?
            """, (student_id, date))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0], result[1]
            else:
                return None, None
        except Exception as e:
            print(f"Error getting attendance: {e}")
            return None, None
    
    def get_student_absence_count(self, student_id, period='month'):
        """Get absence count for a student in specified period"""
        try:
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()
            
            if period == 'month':
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
            elif period == 'week':
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
            else:
                # Default to current month
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT COUNT(*) FROM attendance 
                WHERE student_id = ? AND date BETWEEN ? AND ? AND status = 'absent'
            """, (student_id, start_date, end_date))
            
            absent_count = cursor.fetchone()[0]
            
            # Get total days
            cursor.execute("""
                SELECT COUNT(*) FROM attendance 
                WHERE student_id = ? AND date BETWEEN ? AND ?
            """, (student_id, start_date, end_date))
            
            total_days = cursor.fetchone()[0]
            conn.close()
            
            return absent_count, total_days
        except Exception as e:
            print(f"Error getting absence count: {e}")
            return 0, 0
    
    def get_attendance_percentage(self, student_id):
        """Calculate attendance percentage for a student"""
        try:
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()
            
            # Get total attendance records
            cursor.execute("""
                SELECT COUNT(*) FROM attendance WHERE student_id = ?
            """, (student_id,))
            total_records = cursor.fetchone()[0]
            
            if total_records == 0:
                return 0
            
            # Get present days
            cursor.execute("""
                SELECT COUNT(*) FROM attendance 
                WHERE student_id = ? AND status IN ('present', 'late')
            """, (student_id,))
            present_days = cursor.fetchone()[0]
            
            conn.close()
            percentage = (present_days / total_records) * 100
            return round(percentage, 2)
        except Exception as e:
            print(f"Error calculating percentage: {e}")
            return 0
    
    def get_class_absent_students(self, class_name, date):
        """Get list of absent students for a class on specific date"""
        try:
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT s.id, s.name FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
                WHERE s.class = ? AND (a.status = 'absent' OR a.status IS NULL)
            """, (date, class_name))
            
            absent_students = cursor.fetchall()
            conn.close()
            return absent_students
        except Exception as e:
            print(f"Error getting absent students: {e}")
            return []
    
    def generate_response(self, message):
        """Generate response based on user message"""
        if not self.current_user:
            return "Please login first to access attendance information."
        
        intent = self.classify_intent(message)
        entities = self.extract_entities(message)
        
        if intent == 'greeting':
            return f"Hello! I'm your attendance assistant. How can I help you today?"
        
        elif intent == 'attendance_check':
            date = entities.get('date', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
            status, time = self.get_student_attendance_status(self.current_user, date)
            
            if status:
                return f"Yes, you were marked as '{status}' on {date} at {time}."
            else:
                return f"No attendance record found for {date}. You might have been absent."
        
        elif intent == 'absence_count':
            period = entities.get('period', 'month')
            absent_count, total_days = self.get_student_absence_count(self.current_user, period)
            
            if total_days > 0:
                return f"You have been absent for {absent_count} days out of {total_days} total days this {period}."
            else:
                return f"No attendance records found for this {period}."
        
        elif intent == 'attendance_percentage':
            percentage = self.get_attendance_percentage(self.current_user)
            
            if percentage >= 75:
                status_msg = "Great! You have good attendance. 👍"
            elif percentage >= 60:
                status_msg = "Your attendance is okay, but try to improve it. ⚠️"
            else:
                status_msg = "Your attendance is low. Please attend classes regularly. ❌"
            
            return f"Your attendance percentage is {percentage}%. {status_msg}"
        
        elif intent == 'student_attendance_check':
            student_name = entities.get('student_name')
            if not student_name:
                return "Please specify a student name. Example: 'Tell me Rakshit attendance'"
            
            student = self.find_student_by_name(student_name)
            if not student:
                return f"Sorry, I couldn't find a student named '{student_name}'. Please check the spelling and try again."
            
            student_id, full_name, class_name = student
            date = entities.get('date', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
            status, time = self.get_student_attendance_status(student_id, date)
            
            if status:
                return f"📊 Attendance for {full_name} ({student_id}) from {class_name}:\n\n📅 Date: {date}\n✅ Status: {status}\n⏰ Time: {time if time else 'N/A'}"
            else:
                return f"📊 Attendance for {full_name} ({student_id}) from {class_name}:\n\n📅 Date: {date}\n❌ No attendance record found (likely absent)"
        
        elif intent == 'student_percentage':
            student_name = entities.get('student_name')
            if not student_name:
                return "Please specify a student name. Example: 'Show John's percentage'"
            
            student = self.find_student_by_name(student_name)
            if not student:
                return f"Sorry, I couldn't find a student named '{student_name}'. Please check the spelling and try again."
            
            student_id, full_name, class_name = student
            percentage = self.get_attendance_percentage(student_id)
            
            if percentage >= 75:
                status_msg = "Excellent attendance! 🌟"
                emoji = "✅"
            elif percentage >= 60:
                status_msg = "Good attendance, but can improve 📈"
                emoji = "⚠️"
            else:
                status_msg = "Needs improvement - attend regularly 📚"
                emoji = "❌"
            
            return f"📊 Attendance Report for {full_name}\n\n👤 Student ID: {student_id}\n🏫 Class: {class_name}\n{emoji} Attendance: {percentage}%\n💡 {status_msg}"
        
        elif intent == 'student_absence_count':
            student_name = entities.get('student_name')
            if not student_name:
                return "Please specify a student name. Example: 'How many days absent for Sarah this month?'"
            
            student = self.find_student_by_name(student_name)
            if not student:
                return f"Sorry, I couldn't find a student named '{student_name}'. Please check the spelling and try again."
            
            student_id, full_name, class_name = student
            period = entities.get('period', 'month')
            absent_count, total_days = self.get_student_absence_count(student_id, period)
            
            if total_days > 0:
                present_days = total_days - absent_count
                return f"📊 Absence Report for {full_name}\n\n👤 Student ID: {student_id}\n🏫 Class: {class_name}\n📅 Period: This {period}\n\n❌ Absent: {absent_count} days\n✅ Present: {present_days} days\n📈 Total: {total_days} days"
            else:
                return f"📊 No attendance records found for {full_name} this {period}."
        
        elif intent == 'class_attendance' and self.user_role == 'teacher':
            class_name = entities.get('class', '')
            date = entities.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            if class_name:
                absent_students = self.get_class_absent_students(class_name, date)
                if absent_students:
                    names = [f"{student[1]} ({student[0]})" for student in absent_students]
                    return f"Absent students in {class_name} on {date}:\n" + "\n".join(names)
                else:
                    return f"All students were present in {class_name} on {date}! 🎉"
            else:
                return "Please specify the class name (e.g., 'Class 10-A')."
        
        elif intent == 'help':
            if self.user_role == 'student':
                return """I can help you with:
                
📊 Your Attendance Queries:
• "Did I attend yesterday's class?"
• "How many days have I been absent this month?"
• "What's my attendance percentage?"

👥 Other Students' Attendance:
• "Tell me Rakshit attendance"
• "Show John's percentage"
• "How many days absent for Sarah this month?"
• "Check attendance for Mike yesterday"

❓ General Help:
• Ask me about any student's attendance status
• Get attendance statistics for anyone
• Check attendance for specific dates

Just ask me naturally! I'll understand and help you. 😊"""
            else:
                return """Teacher Commands:
                
📊 Class Management:
• "Who was absent today?"
• "Show attendance for Class 10-A"
• "Attendance report for yesterday"

👥 Student Queries:
• "Tell me Rakshit attendance"
• "Show Emma's attendance percentage"
• "Check attendance for David yesterday"
• "How many days absent for Lisa this month?"

📈 Reports:
• Get class-wise attendance
• Check individual student status
• Generate attendance summaries

Ask me anything about attendance management! 👩‍🏫"""
        
        else:
            return """I didn't understand that. Try asking:
• "Did I attend yesterday?"
• "My attendance percentage"
• "How many days absent this month?"
• "Help" for more options"""
    
    def get_low_attendance_students(self, threshold=75):
        """Get students with attendance below threshold"""
        try:
            students = self.db.get_all_students()
            low_attendance = []
            
            for student in students:
                student_id = student[0]
                percentage = self.get_attendance_percentage(student_id)
                if percentage < threshold:
                    low_attendance.append({
                        'id': student_id,
                        'name': student[1],
                        'class': student[2],
                        'percentage': percentage
                    })
            
            return low_attendance
        except Exception as e:
            print(f"Error getting low attendance students: {e}")
            return []
    
    def generate_daily_summary(self):
        """Generate daily attendance summary"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()
            
            # Get today's attendance counts
            cursor.execute("""
                SELECT status, COUNT(*) FROM attendance 
                WHERE date = ? 
                GROUP BY status
            """, (today,))
            
            stats = dict(cursor.fetchall())
            conn.close()
            
            present = stats.get('present', 0)
            absent = stats.get('absent', 0)
            late = stats.get('late', 0)
            total = present + absent + late
            
            if total > 0:
                return f"""📊 Daily Attendance Summary ({today})
                
✅ Present: {present}
❌ Absent: {absent}
⏰ Late: {late}
📈 Total: {total}
📊 Attendance Rate: {(present + late)/total*100:.1f}%"""
            else:
                return "No attendance records found for today."
        
        except Exception as e:
            return f"Error generating summary: {e}"
