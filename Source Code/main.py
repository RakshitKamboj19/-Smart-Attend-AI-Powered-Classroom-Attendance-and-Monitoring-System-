import sys
import os
import cv2
import numpy as np
import face_recognition
import re
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
import pandas as pd
from geopy.distance import geodesic
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QComboBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QDateEdit, QSpinBox, QGroupBox, QFrame, QFileDialog, QMessageBox, QDialog,
    QGridLayout, QCheckBox, QSplitter, QProgressBar, QRadioButton, QButtonGroup,
    QScrollArea, QSizePolicy, QStackedWidget, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QDate, QDateTime, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QImage, QColor, QFont, QIcon, QPainter, QPainterPath
from database import Database
from geopy.geocoders import Nominatim
from chatbot import AttendanceChatbot
from ui_styles import ModernUIStyles

class LocationSettingsDialog(QDialog):
    def __init__(self, parent=None, current_school_name="", current_lat=None, current_lon=None, current_radius=500):
        super(LocationSettingsDialog, self).__init__(parent)
        self.setWindowTitle("🏫 School Location Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        # Store current values
        self.current_school_name = current_school_name
        self.current_lat = current_lat
        self.current_lon = current_lon
        self.current_radius = current_radius
        
        self.setup_ui()
        self.populate_current_values()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add header
        header = QLabel("🏫 Configure School Location for Attendance Verification")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Add separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #E0E0E0; margin: 10px 0px;")
        layout.addWidget(line)
        
        # Create form layout
        form_layout = QGridLayout()
        
        # School name input with search
        form_layout.addWidget(QLabel("🏫 School/University Name:"), 0, 0)
        self.school_name_input = QLineEdit()
        self.school_name_input.setPlaceholderText("Enter school name (e.g., 'Chitkara University', 'Delhi Public School')")
        self.school_name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #2196F3;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        form_layout.addWidget(self.school_name_input, 0, 1)
        
        # Search button
        self.search_btn = QPushButton("🔍 Find Location")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.search_btn.clicked.connect(self.search_school_location)
        form_layout.addWidget(self.search_btn, 0, 2)
        
        # Address display
        form_layout.addWidget(QLabel("📍 Found Address:"), 1, 0)
        self.address_label = QLabel("No location found yet")
        self.address_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background-color: #f5f5f5;
                color: #555;
            }
        """)
        self.address_label.setWordWrap(True)
        form_layout.addWidget(self.address_label, 1, 1, 1, 2)
        
        # GPS Coordinates (read-only, auto-filled)
        form_layout.addWidget(QLabel("🌍 Latitude:"), 2, 0)
        self.lat_input = QLineEdit()
        self.lat_input.setReadOnly(True)
        self.lat_input.setStyleSheet("background-color: #f0f0f0; color: #666;")
        form_layout.addWidget(self.lat_input, 2, 1)
        
        form_layout.addWidget(QLabel("🌍 Longitude:"), 3, 0)
        self.lon_input = QLineEdit()
        self.lon_input.setReadOnly(True)
        self.lon_input.setStyleSheet("background-color: #f0f0f0; color: #666;")
        form_layout.addWidget(self.lon_input, 3, 1)
        
        # Manual override checkbox
        self.manual_override = QCheckBox("📝 Enter coordinates manually")
        self.manual_override.stateChanged.connect(self.toggle_manual_input)
        form_layout.addWidget(self.manual_override, 3, 2)
        
        # Allowed radius
        form_layout.addWidget(QLabel("📏 Allowed Radius (meters):"), 4, 0)
        self.radius_input = QSpinBox()
        self.radius_input.setRange(10, 5000)  # 10m to 5km
        self.radius_input.setValue(500)  # Default 500m
        self.radius_input.setSuffix(" m")
        self.radius_input.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        form_layout.addWidget(self.radius_input, 4, 1)
        
        # Radius helper text
        radius_help = QLabel("💡 Recommended: 100-500m for small schools, 500-1000m for large universities")
        radius_help.setStyleSheet("color: #757575; font-size: 12px; font-style: italic;")
        radius_help.setWordWrap(True)
        form_layout.addWidget(radius_help, 5, 1, 1, 2)
        
        layout.addLayout(form_layout)
        
        # Popular schools quick selection
        popular_group = QGroupBox("🎓 Quick Select Popular Schools/Universities")
        popular_layout = QGridLayout(popular_group)
        
        popular_schools = [
            ("Chitkara University", "Chitkara University, Punjab, India"),
            ("Delhi University", "University of Delhi, Delhi, India"),
            ("IIT Delhi", "Indian Institute of Technology Delhi, New Delhi, India"),
            ("Lovely Professional University", "Lovely Professional University, Punjab, India"),
            ("Amity University", "Amity University, Noida, India"),
            ("Manipal University", "Manipal Academy of Higher Education, Karnataka, India")
        ]
        
        for i, (display_name, search_term) in enumerate(popular_schools):
            btn = QPushButton(display_name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E3F2FD;
                    color: #1565C0;
                    border: 1px solid #2196F3;
                    border-radius: 4px;
                    padding: 6px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #BBDEFB;
                }
            """)
            btn.clicked.connect(lambda checked, term=search_term: self.quick_select_school(term))
            popular_layout.addWidget(btn, i // 3, i % 3)
        
        layout.addWidget(popular_group)
        
        # Current location button
        current_location_btn = QPushButton("📍 Use My Current Location")
        current_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        current_location_btn.clicked.connect(self.get_current_location)
        layout.addWidget(current_location_btn)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Save Settings")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def populate_current_values(self):
        """Populate the dialog with current values"""
        if self.current_school_name:
            self.school_name_input.setText(self.current_school_name)
        if self.current_lat is not None:
            self.lat_input.setText(str(self.current_lat))
        if self.current_lon is not None:
            self.lon_input.setText(str(self.current_lon))
        if self.current_radius:
            self.radius_input.setValue(self.current_radius)
    
    def toggle_manual_input(self, checked):
        """Toggle manual coordinate input"""
        if checked:
            self.lat_input.setReadOnly(False)
            self.lon_input.setReadOnly(False)
            self.lat_input.setStyleSheet("background-color: white; color: black;")
            self.lon_input.setStyleSheet("background-color: white; color: black;")
        else:
            self.lat_input.setReadOnly(True)
            self.lon_input.setReadOnly(True)
            self.lat_input.setStyleSheet("background-color: #f0f0f0; color: #666;")
            self.lon_input.setStyleSheet("background-color: #f0f0f0; color: #666;")
    
    def quick_select_school(self, school_search_term):
        """Quick select a popular school"""
        self.school_name_input.setText(school_search_term.split(',')[0])  # Just the name part
        self.search_school_location_by_term(school_search_term)
    
    def search_school_location(self):
        """Search for school location by name"""
        school_name = self.school_name_input.text().strip()
        if not school_name:
            QMessageBox.warning(self, "Error", "Please enter a school/university name!")
            return
        
        self.search_school_location_by_term(school_name)
    
    def search_school_location_by_term(self, search_term):
        """Search for location by term"""
        try:
            # Show progress
            self.search_btn.setEnabled(False)
            self.search_btn.setText("🔍 Searching...")
            QApplication.processEvents()
            
            geolocator = Nominatim(user_agent="student_attendance_system")
            
            # Try multiple search variations for better results
            search_queries = [
                search_term,
                f"{search_term}, India",
                f"{search_term} campus",
                f"{search_term} university",
                f"{search_term} college"
            ]
            
            location = None
            for query in search_queries:
                try:
                    print(f"Searching for: {query}")
                    location = geolocator.geocode(query, timeout=10)
                    if location:
                        break
                except Exception as e:
                    print(f"Search failed for '{query}': {e}")
                    continue
            
            if location:
                # Update fields
                self.lat_input.setText(str(location.latitude))
                self.lon_input.setText(str(location.longitude))
                self.address_label.setText(f"📍 {location.address}")
                self.address_label.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        border: 2px solid #4CAF50;
                        border-radius: 4px;
                        background-color: #E8F5E9;
                        color: #2E7D32;
                    }
                """)
                
                QMessageBox.information(self, "Location Found! 🎉", 
                    f"✅ Successfully found location for:\n\n"
                    f"🏫 {search_term}\n\n"
                    f"📍 Address: {location.address}\n\n"
                    f"🌍 Coordinates: {location.latitude:.6f}, {location.longitude:.6f}")
                
            else:
                self.address_label.setText("❌ Location not found. Please try a different name or check spelling.")
                self.address_label.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        border: 2px solid #F44336;
                        border-radius: 4px;
                        background-color: #FFEBEE;
                        color: #C62828;
                    }
                """)
                
                QMessageBox.warning(self, "Location Not Found 😞", 
                    f"❌ Could not find location for '{search_term}'.\n\n"
                    f"💡 Tips:\n"
                    f"• Try the full official name\n"
                    f"• Include the city/state\n"
                    f"• Check spelling\n"
                    f"• Use English name if available\n\n"
                    f"Example: 'Chitkara University Punjab' instead of just 'Chitkara'")
        
        except Exception as e:
            QMessageBox.critical(self, "Search Error", 
                f"❌ An error occurred while searching:\n\n{str(e)}\n\n"
                f"Please check your internet connection and try again.")
        
        finally:
            self.search_btn.setEnabled(True)
            self.search_btn.setText("🔍 Find Location")

    def get_current_location(self):
        """Get the current device location"""
        try:
            # Show progress
            progress_dialog = QMessageBox()
            progress_dialog.setWindowTitle("Getting Location")
            progress_dialog.setText("📍 Getting your current location...\nThis may take a few seconds.")
            progress_dialog.setStandardButtons(QMessageBox.NoButton)
            progress_dialog.show()
            QApplication.processEvents()
            
            geolocator = Nominatim(user_agent="student_attendance_system")
            
            # Try to get real location first
            real_location = self.get_device_location()
            
            if real_location:
                lat, lon = real_location
                # Reverse geocode to get address
                location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
                address = location.address if location else f"Coordinates: {lat}, {lon}"
            else:
                # Fallback to IP-based location
                try:
                    import geocoder
                    g = geocoder.ip('me')
                    if g.ok:
                        lat, lon = g.latlng
                        location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
                        address = location.address if location else f"Approximate location: {lat}, {lon}"
                    else:
                        raise Exception("Could not determine location")
                except ImportError:
                    raise Exception("Install 'geocoder' library for location detection: pip install geocoder")
            
            progress_dialog.close()
            
            # Update fields
            self.lat_input.setText(str(lat))
            self.lon_input.setText(str(lon))
            self.address_label.setText(f"📍 {address}")
            self.address_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border: 2px solid #FF9800;
                    border-radius: 4px;
                    background-color: #FFF3E0;
                    color: #E65100;
                }
            """)
            self.school_name_input.setText("Current Location")
            
            QMessageBox.information(self, "Current Location Found! 📍", 
                f"✅ Successfully detected your current location:\n\n"
                f"📍 Address: {address}\n\n"
                f"🌍 Coordinates: {lat:.6f}, {lon:.6f}\n\n"
                f"⚠️ Note: Make sure this is your intended school location!")
        
        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(self, "Location Error", 
                f"❌ Could not get current location:\n\n{str(e)}")
    
    def get_device_location(self):
        """Try to get real device GPS location"""
        try:
            if sys.platform == "win32":
                import subprocess
                powershell_script = """
                Add-Type -AssemblyName System.Device
                $GeoWatcher = New-Object System.Device.Location.GeoCoordinateWatcher
                $GeoWatcher.Start()
                Start-Sleep -Seconds 3
                $Coord = $GeoWatcher.Position.Location
                if ($Coord.IsUnknown) {
                    Write-Output "UNKNOWN"
                } else {
                    Write-Output "$($Coord.Latitude),$($Coord.Longitude)"
                }
                $GeoWatcher.Stop()
                """
                
                result = subprocess.run(["powershell", "-Command", powershell_script], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout.strip() not in ["UNKNOWN", "ERROR", ""]:
                    coords = result.stdout.strip().split(',')
                    if len(coords) == 2:
                        return (float(coords[0]), float(coords[1]))
        except:
            pass
        return None
    
    def save_settings(self):
        """Save the location settings"""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                QMessageBox.warning(self, "Invalid Coordinates", 
                    "❌ Invalid GPS coordinates!\n\n"
                    "Latitude must be between -90 and 90\n"
                    "Longitude must be between -180 and 180")
                return
            
            school_name = self.school_name_input.text().strip()
            if not school_name:
                QMessageBox.warning(self, "Missing Information", 
                    "❌ Please enter a school/university name!")
                return
            
            # Store the values for retrieval
            self.school_name = school_name
            self.latitude = lat
            self.longitude = lon
            self.radius = self.radius_input.value()
            
            self.accept()
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", 
                "❌ Please enter valid GPS coordinates!\n\n"
                "Use the search function to find your school automatically.")

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.db = Database()
        
        # Initialize location settings
        self.school_location = (28.6139, 77.2090)  # Default location (Delhi)
        self.allowed_radius = 0.5  # Default radius in kilometers
        
        # Create photos directory if it doesn't exist
        if not os.path.exists("student_photos"):
            os.makedirs("student_photos")
        
        # Initialize camera variables
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera_frame)
        self.current_frame = None
        
        # Initialize camera control buttons
        self.start_camera_button = None
        self.stop_camera_button = None
        self.capture_photo_button = None
        self.attendance_camera_label = None
        
        # Initialize location variables
        self.location_verified = False
        self.current_location = None
        
        # Initialize face recognition variables
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.load_known_faces()
        
        # Initialize chatbot
        self.chatbot = AttendanceChatbot(self.db)
        self.chatbot.set_user("S12345", "student")  # Default user
        
        # Initialize UI
        self.init_ui()
        self.captured_photo = None

    def load_known_faces(self):
        """Load known faces from the student photos directory"""
        try:
            # Clear existing data
            self.known_face_encodings = []
            self.known_face_names = []
            self.known_face_ids = []
            
            # Get all students from database
            students = self.db.get_all_students()
            
            for student in students:
                student_id = student[0]
                student_name = student[1]
                photo_path = student[5]  # Photo path is at index 5 in the student tuple
                
                if photo_path and os.path.exists(photo_path):
                    # Load image and get face encoding
                    image = face_recognition.load_image_file(photo_path)
                    face_locations = face_recognition.face_locations(image)
                    
                    if face_locations:
                        face_encoding = face_recognition.face_encodings(image, face_locations)[0]
                        
                        # Add to known faces
                        self.known_face_encodings.append(face_encoding)
                        self.known_face_names.append(student_name)
                        self.known_face_ids.append(student_id)
                        
                        print(f"Loaded face for {student_name} ({student_id})")
                    else:
                        print(f"No face found in photo for {student_name} ({student_id})")
            
            print(f"Loaded {len(self.known_face_encodings)} known faces")
        except Exception as e:
            print(f"Error loading known faces: {str(e)}")

    def init_ui(self):
        # Set window properties
        self.setWindowTitle("🎓 Student Attendance System - Professional Edition")
        self.setGeometry(50, 50, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Apply modern UI styles
        self.setStyleSheet(ModernUIStyles.get_complete_stylesheet())

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create left sidebar for navigation with enhanced styling
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMaximumWidth(280)
        sidebar.setMinimumWidth(280)
        sidebar.setStyleSheet("""
            QWidget#sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FAFC);
                border-right: 2px solid #E2E8F0;
            }
            QPushButton {
                background: transparent;
                color: #334155;
                text-align: left;
                padding: 16px 24px;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                margin: 4px 16px;
                min-height: 52px;
                border-left: 4px solid transparent;
            }
            QPushButton:hover {
                background: #EFF6FF;
                color: #2563EB;
                border-left: 4px solid #3B82F6;
            }
            QPushButton:pressed {
                background: #DBEAFE;
                color: #1D4ED8;
                border-left: 4px solid #2563EB;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(2)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add professional logo section with enhanced visibility
        logo_section = QWidget()
        logo_section.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2563EB, stop:1 #1D4ED8);
                border-radius: 16px;
                margin: 20px 16px 30px 16px;
                padding: 24px;
                border: 2px solid rgba(255, 255, 255, 0.1);
            }
        """)
        logo_layout = QVBoxLayout(logo_section)
        
        # App icon with enhanced visibility
        app_icon = QLabel("🎓")
        app_icon.setAlignment(Qt.AlignCenter)
        app_icon.setStyleSheet("""
            color: #FFFFFF;
            font-size: 48px;
            margin-bottom: 12px;
        """)
        logo_layout.addWidget(app_icon)
        
        # App title with better typography
        title = QLabel("Student\nAttendance\nSystem")
        title.setStyleSheet("""
            color: #FFFFFF;
            font-size: 18px;
            font-weight: 700;
            text-align: center;
            line-height: 1.3;
            letter-spacing: 0.5px;
        """)
        title.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(title)
        
        # Version with better contrast
        version = QLabel("v2.0 Professional")
        version.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 12px;
            font-weight: 500;
            text-align: center;
            margin-top: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 4px 12px;
        """)
        version.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(version)
        
        sidebar_layout.addWidget(logo_section)
        
        # Add navigation section label with enhanced visibility
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet("""
            color: #64748B;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 20px 24px 12px 24px;
        """)
        sidebar_layout.addWidget(nav_label)
        
        # Add navigation buttons with modern styling
        nav_buttons = [
            ("🏠", "Dashboard", self.show_dashboard),
            ("👥", "Students", self.show_students),
            ("📸", "Attendance", self.show_attendance),
            ("📊", "Reports", self.show_reports),
            ("🤖", "AI Assistant", self.show_chatbot),
            ("⚙️", "Settings", self.show_settings)
        ]
        
        # Store buttons for active state management
        self.nav_buttons = []
        
        for icon, text, slot in nav_buttons:
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)
            
            button = QPushButton()
            button.setText(f"  {icon}   {text}")
            button.setMinimumHeight(55)
            button.clicked.connect(slot)
            
            self.nav_buttons.append(button)
            button_layout.addWidget(button)
            sidebar_layout.addWidget(button_widget)
        
        # Add some spacing
        sidebar_layout.addSpacing(20)
        
        # Add enhanced user section with professional styling
        user_section = QWidget()
        user_section.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F8FAFC, stop:1 #E2E8F0);
                border: 1px solid #CBD5E0;
                border-radius: 12px;
                margin: 16px;
                padding: 18px;
            }
        """)
        user_layout = QVBoxLayout(user_section)
        user_layout.setSpacing(8)
        
        # Enhanced user icon with background
        user_icon_container = QWidget()
        user_icon_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3B82F6, stop:1 #1D4ED8);
                border-radius: 24px;
                min-width: 48px;
                max-width: 48px;
                min-height: 48px;
                max-height: 48px;
                margin: 0px auto 8px auto;
            }
        """)
        user_icon_layout = QVBoxLayout(user_icon_container)
        user_icon_layout.setContentsMargins(0, 0, 0, 0)
        
        user_icon = QLabel("👤")
        user_icon.setAlignment(Qt.AlignCenter)
        user_icon.setStyleSheet("""
            font-size: 22px;
            color: #FFFFFF;
            background: transparent;
            border: none;
            margin: 0px;
            padding: 0px;
        """)
        user_icon_layout.addWidget(user_icon)
        user_layout.addWidget(user_icon_container)
        
        # Enhanced user name with better typography
        user_name = QLabel("Administrator")
        user_name.setStyleSheet("""
            color: #1E293B;
            font-size: 16px;
            font-weight: 700;
            text-align: center;
            margin: 0px;
            background: transparent;
            border: none;
        """)
        user_name.setAlignment(Qt.AlignCenter)
        user_layout.addWidget(user_name)
        
        # Enhanced user role with professional badge styling
        user_role = QLabel("System Admin")
        user_role.setStyleSheet("""
            color: #64748B;
            font-size: 12px;
            font-weight: 500;
            text-align: center;
            background: rgba(100, 116, 139, 0.1);
            border: 1px solid rgba(100, 116, 139, 0.2);
            border-radius: 10px;
            padding: 4px 8px;
            margin: 2px 8px;
        """)
        user_role.setAlignment(Qt.AlignCenter)
        user_layout.addWidget(user_role)
        
        sidebar_layout.addWidget(user_section)
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)

        # Create stacked widget for different pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: #f5f5f5;
            }
        """)
        main_layout.addWidget(self.stacked_widget)

        # Create different pages
        self.create_dashboard_page()
        self.create_students_page()
        self.create_attendance_page()
        self.create_reports_page()
        self.create_chatbot_page()
        
        # Show dashboard by default
        self.show_dashboard()

    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Minimal header
        header = QLabel("Dashboard")
        header.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(header)
        
        # Get real stats from database
        student_count = len(self.db.get_all_students())
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get today's attendance
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT student_id) 
                FROM attendance 
                WHERE date = ? AND status = 'Present'
            """, (today_date,))
            present_today = cursor.fetchone()[0] or 0
            conn.close()
        except:
            present_today = 0
        
        absent_today = student_count - present_today
        
        # Simple stats section
        stats_group = QGroupBox("Today's Summary")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0px;
            }
        """)
        stats_layout = QGridLayout(stats_group)
        
        # Simple stat cards
        stats_data = [
            ("Total Students", str(student_count), "#3498db"),
            ("Present Today", str(present_today), "#2ecc71"),
            ("Absent Today", str(absent_today), "#e74c3c"),
            ("Attendance Rate", f"{(present_today/student_count*100) if student_count > 0 else 0:.1f}%", "#f39c12")
        ]
        
        for i, (title, value, color) in enumerate(stats_data):
            card = self.create_simple_stats_card(title, value, color)
            row, col = divmod(i, 2)
            stats_layout.addWidget(card, row, col)
        
        layout.addWidget(stats_group)
        
        # Simple quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0px;
            }
        """)
        actions_layout = QGridLayout(actions_group)
        
        # Simple action buttons
        actions_data = [
            ("📸 Take Attendance", self.show_attendance),
            ("👥 Manage Students", self.show_students),
            ("📊 View Reports", self.show_reports),
            ("🤖 AI Assistant", self.show_chatbot)
        ]
        
        for i, (text, action) in enumerate(actions_data):
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #2196F3;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
            """)
            btn.clicked.connect(action)
            row, col = divmod(i, 2)
            actions_layout.addWidget(btn, row, col)
        
        layout.addWidget(actions_group)
        
        # Simple recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0px;
            }
        """)
        activity_layout = QVBoxLayout(activity_group)
        
        # Get recent activities
        activities = self.get_recent_activities()
        
        if not activities:
            no_activity = QLabel("No recent activities")
            no_activity.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
            activity_layout.addWidget(no_activity)
        else:
            for activity in activities[:3]:  # Show last 3 activities
                activity_item = QLabel(f"• {activity.get('description', 'Activity')} - {activity.get('time', 'Recently')}")
                activity_item.setStyleSheet("""
                    QLabel {
                        color: #333;
                        padding: 5px 10px;
                        border-bottom: 1px solid #eee;
                    }
                """)
                activity_layout.addWidget(activity_item)
        
        layout.addWidget(activity_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def create_simple_stats_card(self, title, value, color):
        """Create a simple stats card"""
        card = QWidget()
        card.setFixedHeight(120)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 1px solid #ddd;
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 10px;
            }}
            QWidget:hover {{
                border-color: {color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #666;
            margin: 0px;
        """)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {color};
            margin: 5px 0px;
        """)
        layout.addWidget(value_label)
        
        # Add stretch to center content
        layout.addStretch()
        
        return card
    
    def create_modern_card(self, title, value, icon, subtitle, gradient, glow_color):
        """Create a modern glassmorphism stats card"""
        card = QWidget()
        card.setFixedHeight(160)
        card.setStyleSheet("""
            QWidget {
                background: """ + gradient + """;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QWidget:hover {
                border: 1px solid rgba(255, 255, 255, 0.3);
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.15), stop:1 rgba(255, 255, 255, 0.05));
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Card header with icon and title
        header_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 28px;
            color: rgba(255, 255, 255, 0.9);
        """)
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.8);
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        title_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(title_label)
        
        layout.addLayout(header_layout)
        
        # Main value
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 36px;
            font-weight: 800;
            color: white;
            margin: 5px 0px;
        """)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.7);
            text-align: center;
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        return card
    
    def create_action_button(self, title, subtitle, action, color):
        """Create modern action button"""
        button = QPushButton()
        button.setFixedHeight(80)
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {color}99);
                border: none;
                border-radius: 15px;
                color: white;
                font-weight: 600;
                text-align: left;
                padding: 15px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}DD, stop:1 {color}BB);
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}AA, stop:1 {color}88);
            }}
        """)
        
        # Create button content
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 700;
            color: white;
            margin-bottom: 3px;
        """)
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("""
            font-size: 11px;
            color: rgba(255, 255, 255, 0.8);
        """)
        
        button_layout.addWidget(title_label)
        button_layout.addWidget(subtitle_label)
        
        # Set the widget as button content
        button_main_layout = QVBoxLayout(button)
        button_main_layout.addWidget(button_widget)
        
        button.clicked.connect(action)
        return button
    
    def create_activity_item(self, icon, activity, time_ago):
        """Create modern activity item"""
        item = QWidget()
        item.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 12px;
                margin: 5px 0px;
            }
            QWidget:hover {
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 18px;
            color: #64b5f6;
            margin-right: 10px;
        """)
        layout.addWidget(icon_label)
        
        # Activity text
        activity_label = QLabel(activity)
        activity_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            color: white;
        """)
        layout.addWidget(activity_label)
        
        layout.addStretch()
        
        # Time
        time_label = QLabel(time_ago)
        time_label.setStyleSheet("""
            font-size: 11px;
            color: rgba(255, 255, 255, 0.6);
            font-style: italic;
        """)
        layout.addWidget(time_label)
        
        return item
    
    def create_modern_stats_card(self, icon, title, value, subtitle, gradient):
        """Create a modern solid stats card"""
        card = QWidget()
        card.setFixedHeight(160)
        stylesheet = f"""
            QWidget {{
                background: {gradient};
                border-radius: 20px;
                border: 2px solid #ffffff;
            }}
            QWidget:hover {{
                border: 2px solid #f0f0f0;
                transform: translateY(-2px);
            }}
        """
        card.setStyleSheet(stylesheet)
        
        # Add subtle drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Card header with icon and title
        header_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 28px;
            color: white;
        """)
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: white;
        """)
        title_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(title_label)
        
        layout.addLayout(header_layout)
        
        # Main value
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 36px;
            font-weight: 800;
            color: white;
            margin: 5px 0px;
        """)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 500;
            color: white;
            text-align: center;
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        return card
    
    def create_modern_action_button(self, icon, title, subtitle, color, action):
        """Create modern action button"""
        button = QPushButton()
        button.setFixedHeight(100)
        stylesheet = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {color}99);
                border: none;
                border-radius: 15px;
                color: white;
                font-weight: 600;
                text-align: left;
                padding: 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}DD, stop:1 {color}BB);
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}AA, stop:1 {color}88);
            }}
        """
        button.setStyleSheet(stylesheet)
        
        # Create button content layout
        button_layout = QVBoxLayout(button)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        # Icon and title row
        top_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 24px;
            color: white;
        """)
        top_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
            color: white;
        """)
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        button_layout.addLayout(top_layout)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("""
            font-size: 12px;
            color: white;
        """)
        button_layout.addWidget(subtitle_label)
        
        button_layout.addStretch()
        
        if action:
            button.clicked.connect(action)
        
        return button
    
    def create_activity_timeline(self):
        """Create enhanced recent activity with timeline design"""
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-radius: 15px;
                border: 1px solid #dee2e6;
            }
        """)
        
        # Add subtle border instead of shadow
        container.setStyleSheet(container.styleSheet() + """
            QWidget {
                border: 2px solid #e9ecef;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # Get recent activities from database
        activities = self.get_recent_activities()
        
        if not activities:
            # Show placeholder if no activities
            placeholder = QLabel("📊 No recent activities to display")
            placeholder.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-size: 14px;
                    font-style: italic;
                    text-align: center;
                    padding: 20px;
                }
            """)
            placeholder.setAlignment(Qt.AlignCenter)
            layout.addWidget(placeholder)
        else:
            # Add activity items
            for activity in activities[:5]:  # Show last 5 activities
                item = self.create_activity_item(activity)
                layout.addWidget(item)
        
        return container
    
    def create_activity_item(self, activity):
        """Create modern activity timeline item"""
        item = QWidget()
        item.setStyleSheet("""
            QWidget {
                background: #ffffff;
                border-radius: 10px;
                padding: 15px;
                margin: 3px 0px;
                border: 1px solid #dee2e6;
            }
            QWidget:hover {
                background: #f8f9fa;
                border: 1px solid #64b5f6;
            }
        """)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # Activity icon based on type
        icon = "✅" if activity.get('type') == 'attendance' else "📝"
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 20px;
            color: #28a745;
        """)
        layout.addWidget(icon_label)
        
        # Activity details
        details_layout = QVBoxLayout()
        
        # Main text
        main_text = QLabel(activity.get('description', 'Activity'))
        main_text.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #212529;
            margin-bottom: 2px;
        """)
        details_layout.addWidget(main_text)
        
        # Subtitle with time
        subtitle = QLabel(activity.get('time', 'Just now'))
        subtitle.setStyleSheet("""
            font-size: 12px;
            color: #6c757d;
        """)
        details_layout.addWidget(subtitle)
        
        layout.addLayout(details_layout)
        layout.addStretch()
        
        # Status indicator
        status_dot = QLabel("●")
        status_dot.setStyleSheet("""
            font-size: 12px;
            color: #28a745;
        """)
        layout.addWidget(status_dot)
        
        return item
    
    def get_recent_activities(self):
        """Get recent activities from database"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Get recent attendance records
            cursor.execute("""
                SELECT s.name, a.date, a.time, a.status
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                ORDER BY a.date DESC, a.time DESC
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            activities = []
            
            for row in results:
                name, date, time, status = row
                desc = f"{name} marked {status.lower()}"
                time_ago = self.format_time_ago(date, time)
                
                activities.append({
                    'type': 'attendance',
                    'description': desc,
                    'time': time_ago
                })
            
            conn.close()
            return activities
            
        except Exception as e:
            print(f"Error getting recent activities: {e}")
            # Return sample activities for demo
            return [
                {'type': 'attendance', 'description': 'Rakshit marked present', 'time': '5 minutes ago'},
                {'type': 'student', 'description': 'New student added: John Doe', 'time': '1 hour ago'},
                {'type': 'report', 'description': 'Monthly report generated', 'time': '2 hours ago'}
            ]
    
    def format_time_ago(self, date_str, time_str):
        """Format time difference in human readable format"""
        try:
            if time_str:
                datetime_str = f"{date_str} {time_str}"
                record_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            else:
                record_time = datetime.strptime(date_str, "%Y-%m-%d")
            
            now = datetime.now()
            diff = now - record_time
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
                
        except Exception as e:
            print(f"Error formatting time: {e}")
            return "Recently"
        
        # Add quick actions section
        actions_group = QGroupBox("Quick Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
            }
        """)
        actions_layout = QHBoxLayout(actions_group)
        
        # Take attendance button
        take_attendance_btn = QPushButton("📸 Take Attendance")
        take_attendance_btn.clicked.connect(self.show_attendance)
        take_attendance_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 16px;
                padding: 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        actions_layout.addWidget(take_attendance_btn)
        
        # Manage students button
        manage_students_btn = QPushButton("👥 Manage Students")
        manage_students_btn.clicked.connect(self.show_students)
        manage_students_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        actions_layout.addWidget(manage_students_btn)
        
        # View reports button
        view_reports_btn = QPushButton("📈 View Reports")
        view_reports_btn.clicked.connect(self.show_reports)
        view_reports_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 16px;
                padding: 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        actions_layout.addWidget(view_reports_btn)
        
        layout.addWidget(actions_group)
        
        # Add recent activity section
        recent_group = QGroupBox("Recent Activity")
        recent_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
            }
        """)
        recent_layout = QVBoxLayout(recent_group)
        
        # This would be populated from the database
        # For demo, just add placeholder text
        for i in range(3):
            activity = QLabel(f"Student attendance recorded at {datetime.now().strftime('%H:%M:%S')}")
            activity.setStyleSheet("padding: 8px; border-bottom: 1px solid #E0E0E0;")
            recent_layout.addWidget(activity)
        
        layout.addWidget(recent_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)

    def show_dashboard(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_students(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_attendance(self):
        self.stacked_widget.setCurrentIndex(2)

    def show_reports(self):
        self.stacked_widget.setCurrentIndex(3)

    def show_chatbot(self):
        self.stacked_widget.setCurrentIndex(4)

    def show_settings(self):
        dialog = LocationSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                lat = float(dialog.lat_input.text())
                lon = float(dialog.lon_input.text())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    self.school_location = (lat, lon)
                    self.allowed_radius = dialog.radius_input.value() / 1000  # Convert to kilometers
                else:
                    QMessageBox.warning(self, "Error", "Invalid coordinates!")
            except ValueError:
                QMessageBox.warning(self, "Error", "Please enter valid numbers for coordinates!")

    def update_camera_frame(self):
        """Update the camera frame in the UI"""
        if self.camera is not None:
            ret, frame = self.camera.read()
            if ret:
                # Convert frame to RGB for display
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                
                # Convert to QImage and display
                image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.attendance_camera_label.setPixmap(QPixmap.fromImage(image))
                self.current_frame = frame

    def create_students_page(self):
        """Create the students management page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add header
        header_layout = QHBoxLayout()
        
        title = QLabel("Students Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Add student button
        add_button = QPushButton("➕ Add New Student")
        add_button.setFixedWidth(180)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        add_button.clicked.connect(self.add_student)
        header_layout.addWidget(add_button)
        
        # Search box
        search_box = QLineEdit()
        search_box.setPlaceholderText("🔍 Search students...")
        search_box.setFixedWidth(250)
        search_box.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #BDBDBD;
                border-radius: 20px;
                background-color: white;
            }
        """)
        search_box.textChanged.connect(self.filter_students)
        header_layout.addWidget(search_box)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Add a separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #E0E0E0; margin: 10px 0px;")
        layout.addWidget(line)
        
        # Add filter options
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 10)
        
        filter_layout.addWidget(QLabel("Filter by Class:"))
        
        class_combo = QComboBox()
        class_combo.addItem("All Classes")
        class_combo.addItems(["Class 1", "Class 2", "Class 3"])  # This would be populated from database
        class_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background-color: white;
                min-width: 150px;
            }
        """)
        filter_layout.addWidget(class_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Add students table in a group box
        table_group = QGroupBox("Student Records")
        table_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        table_layout = QVBoxLayout(table_group)
        
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(6)
        # Set the Actions column wider to accommodate the buttons
        self.students_table.setColumnWidth(5, 200)
        self.students_table.setHorizontalHeaderLabels(["ID", "Name", "Class", "Email", "Phone", "Actions"])
        
        # Resize columns to content
        self.students_table.resizeColumnsToContents()
        
        # Set the last column to stretch
        header = self.students_table.horizontalHeader()
        header.setSectionResizeMode(5, header.Stretch)
        
        # Don't stretch the last section to ensure proper width for action buttons
        self.students_table.horizontalHeader().setStretchLastSection(False)
        self.students_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.students_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.students_table.setAlternatingRowColors(True)
        self.students_table.verticalHeader().setDefaultSectionSize(60)
        self.students_table.horizontalHeader().setDefaultSectionSize(150)
        # Use default header height
        # self.students_table.horizontalHeader().setFixedHeight(50)
        self.students_table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #E0E0E0;
                background-color: white;
                color: black;
            }
            QTableWidget::item {
                padding: 10px;
                color: black;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #212121;
            }
            QTableWidget::item:alternate {
                background-color: #f5f5f5;
                color: black;
            }
        """)
        table_layout.addWidget(self.students_table)
        
        # Add pagination controls
        pagination_layout = QHBoxLayout()
        
        pagination_layout.addWidget(QLabel("Showing 1-10 of 0 students"))
        pagination_layout.addStretch()
        
        prev_btn = QPushButton("◀ Previous")
        prev_btn.setFixedWidth(100)
        pagination_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("Next ▶")
        next_btn.setFixedWidth(100)
        pagination_layout.addWidget(next_btn)
        
        table_layout.addLayout(pagination_layout)
        table_layout.addWidget(self.students_table)
        layout.addWidget(table_group)
        
        # Add status bar
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Last updated: " + datetime.now().strftime("%d-%m-%Y %H:%M:%S")))
        status_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_students_table)
        status_layout.addWidget(refresh_btn)
        
        layout.addLayout(status_layout)
        
        self.refresh_students_table()
        self.stacked_widget.addWidget(page)

    def refresh_students_table(self):
        """Refresh the students table with current data"""
        # Clear the table
        self.students_table.setRowCount(0)
        
        # Get all students from database
        students = self.db.get_all_students()
        
        # Add students to table
        for row, student in enumerate(students):
            self.students_table.insertRow(row)
            
            # Student ID
            id_item = QTableWidgetItem(student[0])
            self.students_table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(student[1])
            self.students_table.setItem(row, 1, name_item)
            
            # Class
            class_item = QTableWidgetItem(student[2])
            self.students_table.setItem(row, 2, class_item)
            
            # Email
            email_item = QTableWidgetItem(student[3] if student[3] else "")
            self.students_table.setItem(row, 3, email_item)
            
            # Phone
            phone_item = QTableWidgetItem(student[4] if student[4] else "")
            self.students_table.setItem(row, 4, phone_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            actions_layout.setSpacing(2)
            
            # View button
            view_btn = QPushButton("👁️")
            view_btn.setToolTip("View Student")
            view_btn.setFixedSize(30, 30)
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 15px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            view_btn.clicked.connect(lambda _, s=student: self.view_student(s))
            actions_layout.addWidget(view_btn)
            
            # Edit button
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Edit Student")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border-radius: 15px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            edit_btn.clicked.connect(lambda _, s=student: self.edit_student(s))
            actions_layout.addWidget(edit_btn)
            
            # Delete button
            delete_btn = QPushButton("❌")
            delete_btn.setToolTip("Delete Student")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border-radius: 15px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
            """)
            delete_btn.clicked.connect(lambda _, s=student: self.delete_student(s))
            actions_layout.addWidget(delete_btn)
            
            actions_layout.addStretch()
            
            self.students_table.setCellWidget(row, 5, actions_widget)
        
        # Resize columns to content
        self.students_table.resizeColumnsToContents()
        
        # Set the last column to stretch
        header = self.students_table.horizontalHeader()
        header.setSectionResizeMode(5, header.Stretch)

    def add_student(self):
        """Add a new student"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Student")
        dialog.setModal(True)
        dialog.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dialog)
        form_layout = QGridLayout()
        
        # Create input fields
        student_id = QLineEdit()
        name = QLineEdit()
        
        # Replace class_name LineEdit with ComboBox
        class_combo = QComboBox()
        class_combo.setEditable(True)  # Allow adding new classes
        
        # Add existing classes from database
        existing_classes = self.get_all_classes()
        if existing_classes:
            class_combo.addItems(existing_classes)
        else:
            # Add some default classes if none exist
            default_classes = ["Class 1", "Class 2", "Class 3", "Class 4"]
            class_combo.addItems(default_classes)
        
        email = QLineEdit()
        phone = QLineEdit()
        
        # Add fields to form
        form_layout.addWidget(QLabel("Student ID:"), 0, 0)
        form_layout.addWidget(student_id, 0, 1)
        form_layout.addWidget(QLabel("Name:"), 1, 0)
        form_layout.addWidget(name, 1, 1)
        form_layout.addWidget(QLabel("Class:"), 2, 0)
        form_layout.addWidget(class_combo, 2, 1)
        form_layout.addWidget(QLabel("Email:"), 3, 0)
        form_layout.addWidget(email, 3, 1)
        form_layout.addWidget(QLabel("Phone:"), 4, 0)
        form_layout.addWidget(phone, 4, 1)
        
        layout.addLayout(form_layout)
        
        # Add photo capture section
        photo_layout = QVBoxLayout()
        photo_label = QLabel("Student Photo")
        photo_label.setAlignment(Qt.AlignCenter)
        photo_layout.addWidget(photo_label)
        
        # Add photo preview
        photo_preview = QLabel()
        photo_preview.setFixedSize(160, 160)
        photo_preview.setStyleSheet("border: 2px dashed #BDBDBD; background-color: #f5f5f5;")
        photo_preview.setAlignment(Qt.AlignCenter)
        photo_preview.setText("No photo captured")
        photo_layout.addWidget(photo_preview)
        
        # Create a variable to store the captured photo
        student_photo = [None]  # Using a list to store a mutable reference
        
        # Capture photo button
        capture_button = QPushButton("📸 Capture Photo")
        capture_button.clicked.connect(lambda: self.capture_student_photo(photo_preview, student_photo))
        photo_layout.addWidget(capture_button)
        
        layout.addLayout(photo_layout)
        
        # Add buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        cancel_btn = QPushButton("❌ Cancel")
        
        save_btn.clicked.connect(lambda: self.save_student(
            dialog, student_id.text(), name.text(), class_combo.currentText(),
            email.text(), phone.text(), student_photo[0]
        ))
        cancel_btn.clicked.connect(dialog.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)
        
        dialog.exec_()
    
    def capture_student_photo(self, preview_label, photo_storage):
        """Capture a photo for a student directly in the student form"""
        # Create a temporary camera dialog
        camera_dialog = QDialog(self)
        camera_dialog.setWindowTitle("Capture Student Photo")
        camera_dialog.setModal(True)
        camera_dialog.resize(640, 520)
        
        # Create layout
        layout = QVBoxLayout(camera_dialog)
        
        # Camera feed label
        camera_label = QLabel()
        camera_label.setMinimumSize(640, 480)
        camera_label.setAlignment(Qt.AlignCenter)
        camera_label.setText("Camera feed will appear here")
        layout.addWidget(camera_label)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Start camera button
        start_btn = QPushButton("Start Camera")
        buttons_layout.addWidget(start_btn)
        
        # Capture button
        capture_btn = QPushButton("Capture")
        capture_btn.setEnabled(False)
        buttons_layout.addWidget(capture_btn)
        
        # Done button
        done_btn = QPushButton("Done")
        done_btn.setEnabled(False)
        buttons_layout.addWidget(done_btn)
        
        layout.addLayout(buttons_layout)
        
        # Create camera and timer
        camera = None
        timer = QTimer()
        current_frame = [None]  # Using a list to store a mutable reference
        
        # Update camera frame function
        def update_frame():
            ret, frame = camera.read()
            if ret:
                # Convert to RGB for display
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                
                # Convert to QImage and display
                image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                camera_label.setPixmap(QPixmap.fromImage(image))
                current_frame[0] = frame
        
        # Start camera function
        def start_camera():
            nonlocal camera
            camera = cv2.VideoCapture(0)
            if camera.isOpened():
                timer.start(30)  # Update every 30ms
                start_btn.setEnabled(False)
                capture_btn.setEnabled(True)
            else:
                QMessageBox.warning(camera_dialog, "Error", "Could not access the camera!")
        
        # Capture photo function
        def capture_photo():
            if current_frame[0] is not None:
                # Convert to RGB for face detection
                frame = current_frame[0]
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if not face_locations:
                    QMessageBox.warning(camera_dialog, "Error", "No face detected in the photo. Please try again.")
                    return
                
                # Store the captured photo
                photo_storage[0] = frame
                
                # Display in preview
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                preview_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                scaled_preview = preview_image.scaled(160, 160, Qt.KeepAspectRatio)
                preview_label.setPixmap(QPixmap.fromImage(scaled_preview))
                
                # Enable done button
                done_btn.setEnabled(True)
                
                QMessageBox.information(camera_dialog, "Success", "Photo captured successfully!")
        
        # Stop camera function
        def stop_camera():
            nonlocal camera
            if camera is not None:
                timer.stop()
                camera.release()
                camera = None
                camera_dialog.accept()
        
        # Connect signals
        timer.timeout.connect(update_frame)
        start_btn.clicked.connect(start_camera)
        capture_btn.clicked.connect(capture_photo)
        done_btn.clicked.connect(stop_camera)
        
        # Clean up on dialog close
        camera_dialog.finished.connect(lambda: stop_camera() if camera is not None else None)
        
        camera_dialog.exec_()
    
    def save_student(self, dialog, student_id, name, class_name, email, phone, photo=None):
        """Save student details to database"""
        # Validate inputs
        if not student_id or not name or not class_name:
            QMessageBox.warning(dialog, "Error", "Student ID, Name and Class are required!")
            return
        
        # Save photo if captured
        photo_path = None
        if photo is not None:
            # Create a filename based on student ID
            photo_path = os.path.join("student_photos", f"{student_id}.jpg")
            
            # Save the photo
            cv2.imwrite(photo_path, photo)
        
        # Add student to database
        success = self.db.add_student(student_id, name, class_name, email, phone, photo_path)
        
        if success:
            QMessageBox.information(dialog, "Success", "Student added successfully!")
            
            # Reload known faces to include the new student
            self.load_known_faces()
            
            dialog.accept()
            
            # Refresh the students table
            self.refresh_students_table()
        else:
            QMessageBox.warning(dialog, "Error", "Failed to add student. ID may already exist!")
            
            # Delete the saved photo if student wasn't added
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)

    def filter_students(self, text):
        """Filter students table based on search text"""
        for row in range(self.students_table.rowCount()):
            match = False
            for col in range(self.students_table.columnCount() - 1):  # Exclude actions column
                item = self.students_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.students_table.setRowHidden(row, not match)

    def view_student(self, student):
        """View student details"""
        msg = f"""
        Student Details:
        
        ID: {student[0]}
        Name: {student[1]}
        Class: {student[2]}
        Email: {student[3] or 'N/A'}
        Phone: {student[4] or 'N/A'}
        Registration Date: {student[6]}
        """
        QMessageBox.information(self, "Student Details", msg)

    def edit_student(self, student):
        """Edit student details"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Student")
        dialog.setModal(True)
        dialog.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dialog)
        form_layout = QGridLayout()
        
        # Create input fields with student data
        student_id = QLineEdit(student[0])
        student_id.setReadOnly(True)  # ID cannot be changed
        student_id.setStyleSheet("background-color: #f0f0f0;")
        
        name = QLineEdit(student[1])
        
        # Replace class_name LineEdit with ComboBox
        class_combo = QComboBox()
        class_combo.setEditable(True)  # Allow adding new classes
        
        # Add existing classes from database
        existing_classes = self.get_all_classes()
        if existing_classes:
            class_combo.addItems(existing_classes)
        else:
            # Add some default classes if none exist
            default_classes = ["Class 1", "Class 2", "Class 3", "Class 4"]
            class_combo.addItems(default_classes)
        
        # Set current class
        current_class = student[2]
        index = class_combo.findText(current_class)
        if index >= 0:
            class_combo.setCurrentIndex(index)
        else:
            class_combo.setCurrentText(current_class)
        
        email = QLineEdit(student[3] if student[3] else "")
        phone = QLineEdit(student[4] if student[4] else "")
        
        # Add fields to form
        form_layout.addWidget(QLabel("Student ID:"), 0, 0)
        form_layout.addWidget(student_id, 0, 1)
        form_layout.addWidget(QLabel("Name:"), 1, 0)
        form_layout.addWidget(name, 1, 1)
        form_layout.addWidget(QLabel("Class:"), 2, 0)
        form_layout.addWidget(class_combo, 2, 1)
        form_layout.addWidget(QLabel("Email:"), 3, 0)
        form_layout.addWidget(email, 3, 1)
        form_layout.addWidget(QLabel("Phone:"), 4, 0)
        form_layout.addWidget(phone, 4, 1)
        
        layout.addLayout(form_layout)
        
        # Add photo section
        photo_layout = QVBoxLayout()
        photo_label = QLabel("Student Photo")
        photo_label.setAlignment(Qt.AlignCenter)
        photo_layout.addWidget(photo_label)
        
        # Add photo preview
        photo_preview = QLabel()
        photo_preview.setFixedSize(160, 160)
        photo_preview.setStyleSheet("border: 2px dashed #BDBDBD; background-color: #f5f5f5;")
        photo_preview.setAlignment(Qt.AlignCenter)
        
        # Display existing photo if available
        photo_path = student[5]
        student_photo = [None]  # Using a list to store a mutable reference
        
        if photo_path and os.path.exists(photo_path):
            pixmap = QPixmap(photo_path)
            scaled_pixmap = pixmap.scaled(160, 160, Qt.KeepAspectRatio)
            photo_preview.setPixmap(scaled_pixmap)
            
            # Load the existing photo
            student_photo[0] = cv2.imread(photo_path)
        else:
            photo_preview.setText("No photo available")
        
        photo_layout.addWidget(photo_preview)
        
        # Capture photo button
        capture_button = QPushButton("📸 Capture New Photo")
        capture_button.clicked.connect(lambda: self.capture_student_photo(photo_preview, student_photo))
        photo_layout.addWidget(capture_button)
        
        layout.addLayout(photo_layout)
        
        # Add buttons
        button_box = QHBoxLayout()
        update_btn = QPushButton("💾 Update")
        cancel_btn = QPushButton("❌ Cancel")
        
        update_btn.clicked.connect(lambda: self.update_student(
            dialog, student_id.text(), name.text(), class_combo.currentText(),
            email.text(), phone.text(), student_photo[0]
        ))
        cancel_btn.clicked.connect(dialog.reject)
        
        button_box.addWidget(update_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)
        
        dialog.exec_()
    
    def update_student(self, dialog, student_id, name, class_name, email, phone, photo=None):
        """Update student details in database"""
        if not all([name, class_name]):
            QMessageBox.warning(self, "Error", "Please fill in all required fields!")
            return
        
        try:
            if self.db.update_student(student_id, name, class_name, email, phone, photo):
                QMessageBox.information(self, "Success", "Student updated successfully!")
                self.refresh_students_table()
                dialog.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to update student.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update student: {str(e)}")

    def delete_student(self, student):
        """Delete student from database"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete student {student[1]}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete photo if it exists
            if student[5] and os.path.exists(student[5]):
                try:
                    os.remove(student[5])
                except Exception as e:
                    print(f"Failed to delete student photo: {e}")
            
            # Delete from database
            if self.db.delete_student(student[0]):
                self.refresh_students_table()
                QMessageBox.information(self, "Success", "Student deleted successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete student!")

    def create_attendance_page(self):
        """Create the attendance management page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add header
        header_layout = QHBoxLayout()
        title = QLabel("Attendance Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left panel - Camera and controls
        camera_panel = QGroupBox("Camera Feed")
        camera_panel.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        camera_layout = QVBoxLayout(camera_panel)
        
        # Camera feed
        self.attendance_camera_label = QLabel()
        self.attendance_camera_label.setMinimumSize(640, 480)
        self.attendance_camera_label.setAlignment(Qt.AlignCenter)
        self.attendance_camera_label.setStyleSheet("""
            border: 2px dashed #BDBDBD;
            background-color: #f5f5f5;
            border-radius: 4px;
        """)
        self.attendance_camera_label.setText("Camera feed will appear here")
        camera_layout.addWidget(self.attendance_camera_label)
        
        # Camera controls
        controls_layout = QHBoxLayout()
        
        self.start_camera_button = QPushButton("🎥 Start Camera")
        self.start_camera_button.clicked.connect(self.start_camera)
        controls_layout.addWidget(self.start_camera_button)
        
        self.stop_camera_button = QPushButton("⏹️ Stop Camera")
        self.stop_camera_button.clicked.connect(self.stop_camera)
        self.stop_camera_button.setEnabled(False)
        controls_layout.addWidget(self.stop_camera_button)
        
        self.capture_photo_button = QPushButton("📸 Capture Photo")
        self.capture_photo_button.clicked.connect(self.capture_photo)
        self.capture_photo_button.setEnabled(False)
        controls_layout.addWidget(self.capture_photo_button)
        
        camera_layout.addLayout(controls_layout)
        
        # Right panel - Location and preview
        info_panel = QGroupBox("Attendance Information")
        info_panel.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        info_layout = QVBoxLayout(info_panel)
        
        # Location information
        location_group = QGroupBox("Location Verification")
        location_layout = QVBoxLayout(location_group)
        
        self.location_status_label = QLabel("Location: Not verified")
        self.location_status_label.setStyleSheet("color: #F44336;")
        location_layout.addWidget(self.location_status_label)
        
        self.get_location_button = QPushButton("📍 Get Current Location")
        self.get_location_button.clicked.connect(self.verify_location)
        location_layout.addWidget(self.get_location_button)
        
        self.location_distance_label = QLabel("Distance from school: N/A")
        location_layout.addWidget(self.location_distance_label)
        
        info_layout.addWidget(location_group)
        
        # Preview captured photo
        preview_group = QGroupBox("Captured Photo")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(320, 240)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            border: 2px dashed #BDBDBD;
            background-color: #f5f5f5;
            border-radius: 4px;
        """)
        self.preview_label.setText("Captured photo will appear here")
        preview_layout.addWidget(self.preview_label)
        
        # Student recognition result
        self.recognition_result_label = QLabel("Recognition result: N/A")
        preview_layout.addWidget(self.recognition_result_label)
        
        info_layout.addWidget(preview_group)
        
        # Mark attendance button
        self.mark_attendance_button = QPushButton("✅ Mark Attendance")
        self.mark_attendance_button.setEnabled(False)
        self.mark_attendance_button.clicked.connect(self.process_attendance)
        self.mark_attendance_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        info_layout.addWidget(self.mark_attendance_button)
        
        # Add panels to content layout
        content_layout.addWidget(camera_panel, 2)
        content_layout.addWidget(info_panel, 1)
        
        layout.addLayout(content_layout)
        self.stacked_widget.addWidget(page)

    def verify_location(self):
        """Verify the user's current location - must be at school premises"""
        try:
            # Show location checking dialog
            checking_dialog = QMessageBox()
            checking_dialog.setWindowTitle("Location Verification")
            checking_dialog.setText("📍 Checking your current location...")
            checking_dialog.setStandardButtons(QMessageBox.NoButton)
            checking_dialog.show()
            
            # Process events to show the dialog
            QApplication.processEvents()
            
            # Try to get real location first, fallback to demo mode
            current_location = self.get_real_location()
            
            # Close the checking dialog
            checking_dialog.close()
            
            if current_location is None:
                # Fallback to demo mode if real location unavailable
                self.demo_location_verification()
            else:
                # Process real location
                self.process_real_location(current_location)
                
        except Exception as e:
            self.location_distance_label.setText("Distance: Error")
            self.location_status_label.setText("Location: ❌ Verification failed")
            self.location_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.location_verified = False
            self.mark_attendance_button.setEnabled(False)
            
            QMessageBox.critical(self, "Location Error", 
                f"❌ Location verification failed!\n\nError: {str(e)}\n\n⚠️ Please try again or contact administrator.")
    
    def get_real_location(self):
        """Try to get real GPS location from the device"""
        try:
            # METHOD 1: Try Windows Location Services (Windows 10+)
            if sys.platform == "win32":
                location = self.get_windows_location()
                if location:
                    return location
            
            # METHOD 2: Try using geocoder library for IP-based location
            try:
                import geocoder
                g = geocoder.ip('me')
                if g.ok:
                    print(f"IP-based location: {g.latlng}")
                    return tuple(g.latlng)
            except ImportError:
                print("Geocoder library not available")
            
            # METHOD 3: Could add web-based geolocation for browser deployment
            # This would use JavaScript Geolocation API in a web context
            
            return None  # No real location available, use demo mode
            
        except Exception as e:
            print(f"Error getting real location: {e}")
            return None
    
    def get_windows_location(self):
        """Get location using Windows Location Services"""
        try:
            import subprocess
            import json
            
            # Use Windows PowerShell to get location (requires location services enabled)
            powershell_script = """
            try {
                Add-Type -AssemblyName System.Device
                $GeoWatcher = New-Object System.Device.Location.GeoCoordinateWatcher
                $GeoWatcher.Start()
                Start-Sleep -Seconds 3
                $Coord = $GeoWatcher.Position.Location
                if ($Coord.IsUnknown) {
                    Write-Output "UNKNOWN"
                } else {
                    Write-Output "$($Coord.Latitude),$($Coord.Longitude)"
                }
                $GeoWatcher.Stop()
            } catch {
                Write-Output "ERROR"
            }
            """
            
            result = subprocess.run(["powershell", "-Command", powershell_script], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip() not in ["UNKNOWN", "ERROR", ""]:
                coords = result.stdout.strip().split(',')
                if len(coords) == 2:
                    lat, lon = float(coords[0]), float(coords[1])
                    print(f"Windows location: {lat}, {lon}")
                    return (lat, lon)
            
        except Exception as e:
            print(f"Windows location failed: {e}")
        
        return None
    
    def process_real_location(self, current_location):
        """Process a real GPS location"""
        try:
            # Calculate distance from school
            distance = geodesic(self.school_location, current_location).kilometers
            
            self.current_location = current_location
            
            # Check if within allowed radius
            if distance <= self.allowed_radius:
                # Student is at school
                self.location_distance_label.setText(f"Distance from school: {distance*1000:.0f} m")
                self.location_status_label.setText("Location: ✅ Verified - You are at school")
                self.location_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                self.location_verified = True
                
                # Enable attendance marking if photo is captured
                if self.captured_photo is not None:
                    self.mark_attendance_button.setEnabled(True)
                
                QMessageBox.information(self, "Location Verified", 
                    f"✅ Location confirmed!\n\n📍 You are at the school premises\n📏 Distance: {distance*1000:.0f} meters from main building\n📱 Real GPS location detected\n\n✅ You can now mark your attendance.")
            
            else:
                # Student is too far from school
                self.location_distance_label.setText(f"Distance from school: {distance:.2f} km")
                self.location_status_label.setText("Location: ❌ Too far from school")
                self.location_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
                self.location_verified = False
                self.mark_attendance_button.setEnabled(False)
                
                QMessageBox.warning(self, "Location Verification Failed", 
                    f"❌ Location verification failed!\n\n📍 You are not at the school premises\n📏 Distance: {distance:.2f} km from school\n📐 Maximum allowed: {self.allowed_radius*1000:.0f} m\n📱 Real GPS location detected\n\n⚠️ You must be physically present at school to mark attendance.")
        
        except Exception as e:
            print(f"Error processing real location: {e}")
            self.demo_location_verification()  # Fallback to demo
    
    def demo_location_verification(self):
        """Fallback demo mode when real GPS is unavailable"""
        import random
        import time
        
        # Add a small delay for realism
        time.sleep(1)
        
        # Simulate different location scenarios for demonstration
        scenario = random.choice(["at_school", "too_far", "gps_error"])
        
        if scenario == "at_school":
            # Student is at school - within allowed radius
            lat_offset = random.uniform(-0.0005, 0.0005)  # ~50m variation
            lon_offset = random.uniform(-0.0005, 0.0005)  # ~50m variation
            
            current_lat = self.school_location[0] + lat_offset
            current_lon = self.school_location[1] + lon_offset
            
            current_location = (current_lat, current_lon)
            distance = geodesic(self.school_location, current_location).kilometers
            
            self.current_location = current_location
            self.location_distance_label.setText(f"Distance from school: {distance*1000:.0f} m")
            self.location_status_label.setText("Location: ✅ Verified - You are at school")
            self.location_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.location_verified = True
            
            if self.captured_photo is not None:
                self.mark_attendance_button.setEnabled(True)
            
            QMessageBox.information(self, "Location Verified (Demo Mode)", 
                f"✅ Location confirmed!\n\n📍 You are at the school premises\n📏 Distance: {distance*1000:.0f} meters from main building\n🔬 Demo mode - simulated location\n\n✅ You can now mark your attendance.")
        
        elif scenario == "too_far":
            # Student is too far from school
            lat_offset = random.uniform(-0.01, 0.01)  # ~1km variation
            lon_offset = random.uniform(-0.01, 0.01)  # ~1km variation
            
            # Ensure it's outside the allowed radius
            while True:
                current_lat = self.school_location[0] + lat_offset
                current_lon = self.school_location[1] + lon_offset
                current_location = (current_lat, current_lon)
                distance = geodesic(self.school_location, current_location).kilometers
                
                if distance > self.allowed_radius:
                    break
                
                lat_offset = random.uniform(-0.02, 0.02)
                lon_offset = random.uniform(-0.02, 0.02)
            
            self.current_location = current_location
            self.location_distance_label.setText(f"Distance from school: {distance:.2f} km")
            self.location_status_label.setText("Location: ❌ Too far from school")
            self.location_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.location_verified = False
            self.mark_attendance_button.setEnabled(False)
            
            QMessageBox.warning(self, "Location Verification Failed (Demo Mode)", 
                f"❌ Location verification failed!\n\n📍 You are not at the school premises\n📏 Distance: {distance:.2f} km from school\n📐 Maximum allowed: {self.allowed_radius*1000:.0f} m\n🔬 Demo mode - simulated location\n\n⚠️ You must be physically present at school to mark attendance.")
        
        else:  # gps_error
            # Simulate GPS/location service error
            self.location_distance_label.setText("Distance: Unable to determine")
            self.location_status_label.setText("Location: ❌ Location service unavailable")
            self.location_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.location_verified = False
            self.mark_attendance_button.setEnabled(False)
            
            QMessageBox.warning(self, "Location Service Error (Demo Mode)", 
                "❌ Unable to verify your location!\n\n📡 Location service is unavailable\n📱 Please check your GPS/location settings\n🔬 Demo mode - simulated scenario\n\n⚠️ Location verification is required for attendance marking.")

    def process_attendance(self):
        """Process attendance marking"""
        try:
            # Get the recognized student ID from the recognition result label
            recognition_text = self.recognition_result_label.text()
            
            # Extract student name and ID using regex
            match = re.search(r"Recognized: (.*) \((.*)\)", recognition_text)
            if not match:
                QMessageBox.warning(self, "Error", "Could not extract student information from recognition result!")
                return
            
            student_name = match.group(1)
            student_id = match.group(2)
            
            # Get current date and time
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Set status to "Present"
            status = "Present"
            
            # Get location data if available
            latitude = None
            longitude = None
            location_verified = False
            
            if self.location_verified:
                latitude = self.current_location[0]
                longitude = self.current_location[1]
                location_verified = True
            
            # Mark attendance in database
            success = self.db.mark_attendance(student_id, status, latitude, longitude, location_verified)
            
            if success:
                QMessageBox.information(self, "Success", f"Attendance marked for {student_name}!")
                
                # Reset UI
                self.captured_photo = None
                self.preview_label.clear()
                self.preview_label.setText("Captured photo will appear here")
                self.recognition_result_label.setText("Recognition result will appear here")
                self.location_result_label.setText("Location: Not verified")
                self.location_verified = False
                self.mark_attendance_button.setEnabled(False)
            else:
                QMessageBox.warning(self, "Error", "Failed to mark attendance!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def capture_photo(self):
        """Capture a photo from the camera feed"""
        if self.camera is None or not self.camera.isOpened():
            QMessageBox.warning(self, "Error", "Camera is not active!")
            return
        
        # Capture frame
        ret, frame = self.camera.read()
        if not ret:
            QMessageBox.warning(self, "Error", "Failed to capture photo!")
            return
        
        # Store the captured photo
        self.captured_photo = frame
        
        # Convert to RGB for display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Display preview
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        preview_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_preview = preview_image.scaled(320, 240, Qt.KeepAspectRatio)
        self.preview_label.setPixmap(QPixmap.fromImage(scaled_preview))
        
        try:
            # Detect faces for immediate feedback
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if not face_locations:
                QMessageBox.warning(self, "Warning", "No face detected in the photo. Please try again.")
                return
            
            # Set default recognition
            student_name = "Rakshit"
            student_id = "S12345"
            
            # Try to recognize the face immediately
            try:
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                if face_encodings and len(face_encodings) > 0:
                    face_encoding = face_encodings[0]
                    
                    # Compare with known faces
                    if self.known_face_encodings and len(self.known_face_encodings) > 0:
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        
                        # Find the best match
                        best_match_index = np.argmin(face_distances)
                        best_match_distance = face_distances[best_match_index]
                        
                        if best_match_distance < 0.6:  # Good match threshold
                            student_id = self.known_face_ids[best_match_index]
                            student_name = self.known_face_names[best_match_index]
                            
                            # Show confidence
                            confidence = round((1 - best_match_distance) * 100)
                            print(f"Recognized as {student_name} with {confidence}% confidence")
                        else:
                            print(f"No good match found. Best distance: {best_match_distance}")
                    else:
                        print("No known faces to compare with")
            except Exception as e:
                print(f"Error during face recognition: {str(e)}")
            
            # Update recognition result
            self.recognition_result_label.setText(f"Recognized: {student_name} ({student_id})")
            
            # Automatically verify location after capturing photo
            self.verify_location()
            
            # Enable the mark attendance button
            if hasattr(self, 'location_verified') and self.location_verified:
                self.mark_attendance_button.setEnabled(True)
            
            QMessageBox.information(self, "Success", "Photo captured successfully! Location verification in progress...")
        except Exception as e:
            print(f"Error during capture: {str(e)}")
            QMessageBox.warning(self, "Warning", "Photo captured but there was an issue with processing.")

    def start_camera(self):
        """Start the camera feed"""
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                QMessageBox.warning(self, "Error", "Could not access the camera!")
                self.camera = None
                return
            
            self.timer.start(30)  # Update every 30ms
            self.start_camera_button.setEnabled(False)
            self.stop_camera_button.setEnabled(True)
            self.capture_photo_button.setEnabled(True)

    def stop_camera(self):
        """Stop the camera feed"""
        if self.camera is not None:
            self.timer.stop()
            self.camera.release()
            self.camera = None
            self.attendance_camera_label.clear()
            self.attendance_camera_label.setText("Camera feed will appear here")
            self.start_camera_button.setEnabled(True)
            self.stop_camera_button.setEnabled(False)
            self.capture_photo_button.setEnabled(False)

    def create_reports_page(self):
        """Create the reports page"""
        reports_page = QWidget()
        layout = QVBoxLayout(reports_page)
        
        # Add header
        header_layout = QHBoxLayout()
        header = QLabel("📊 Attendance Reports")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Add tabs for daily and monthly reports
        tabs = QTabWidget()
        daily_tab = QWidget()
        monthly_tab = QWidget()
        
        tabs.addTab(daily_tab, "Daily Report")
        tabs.addTab(monthly_tab, "Monthly Report")
        
        # Create daily report tab
        daily_layout = QVBoxLayout(daily_tab)
        
        # Add filter controls
        filter_layout = QHBoxLayout()
        
        # Date picker
        date_label = QLabel("Date:")
        self.report_date_picker = QDateEdit()
        self.report_date_picker.setCalendarPopup(True)
        self.report_date_picker.setDate(QDate.currentDate())
        self.report_date_picker.dateChanged.connect(self.update_attendance_report)
        
        # Class filter
        class_label = QLabel("Class:")
        self.report_class_combo = QComboBox()
        self.report_class_combo.addItem("All Classes")
        
        # Add existing classes
        classes = self.get_all_classes()
        if classes:
            self.report_class_combo.addItems(classes)
        
        self.report_class_combo.currentTextChanged.connect(self.update_attendance_report)
        
        # Export button
        export_btn = QPushButton("📥 Export Report")
        export_btn.clicked.connect(self.export_attendance_report)
        
        filter_layout.addWidget(date_label)
        filter_layout.addWidget(self.report_date_picker)
        filter_layout.addWidget(class_label)
        filter_layout.addWidget(self.report_class_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(export_btn)
        
        daily_layout.addLayout(filter_layout)
        
        # Add attendance table
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(5)
        self.attendance_table.setHorizontalHeaderLabels(["ID", "Name", "Class", "Date", "Status"])
        self.attendance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.attendance_table.setAlternatingRowColors(True)
        self.attendance_table.setStyleSheet("alternate-background-color: #f5f5f5;")
        
        daily_layout.addWidget(self.attendance_table)
        
        # Add daily chart
        self.daily_figure = plt.figure(figsize=(10, 4))
        self.daily_canvas = FigureCanvas(self.daily_figure)
        daily_layout.addWidget(self.daily_canvas)
        
        # Create monthly report tab
        monthly_layout = QVBoxLayout(monthly_tab)
        
        # Add month/year selector
        month_year_layout = QHBoxLayout()
        
        month_label = QLabel("Month:")
        self.month_combo = QComboBox()
        for i in range(1, 13):
            self.month_combo.addItem(QDate(2000, i, 1).toString("MMMM"), i)
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
        
        year_label = QLabel("Year:")
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(QDate.currentDate().year())
        
        update_btn = QPushButton("🔄 Update")
        update_btn.clicked.connect(self.update_monthly_report)
        
        month_year_layout.addWidget(month_label)
        month_year_layout.addWidget(self.month_combo)
        month_year_layout.addWidget(year_label)
        month_year_layout.addWidget(self.year_spin)
        month_year_layout.addStretch()
        month_year_layout.addWidget(update_btn)
        
        monthly_layout.addLayout(month_year_layout)
        
        # Add monthly chart
        self.monthly_figure = plt.figure(figsize=(10, 4))
        self.monthly_canvas = FigureCanvas(self.monthly_figure)
        monthly_layout.addWidget(self.monthly_canvas)
        
        layout.addWidget(tabs)
        
        # Add the page to stacked widget
        self.stacked_widget.addWidget(reports_page)
        
        # Initialize reports with empty data to avoid errors
        try:
            # Apply modern chart styling
            plt.style.use('default')
            chart_colors = ModernUIStyles.get_chart_colors()
            
            # Create initial empty charts
            self.daily_figure.clear()
            self.daily_figure.patch.set_facecolor(chart_colors['background'])
            ax1 = self.daily_figure.add_subplot(111)
            ax1.set_facecolor(chart_colors['background'])
            
            bars = ax1.bar(['Present', 'Absent'], [0, 0], 
                          color=[chart_colors['present'], chart_colors['absent']],
                          edgecolor='white', linewidth=2, alpha=0.9)
            
            # Add modern styling
            ax1.set_title('Attendance for Today', fontsize=16, fontweight='bold', 
                         color=chart_colors['text'], pad=20)
            ax1.set_ylabel('Number of Students', fontsize=12, color=chart_colors['text'])
            ax1.tick_params(colors=chart_colors['text'], labelsize=10)
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_color(chart_colors['grid'])
            ax1.spines['bottom'].set_color(chart_colors['grid'])
            ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            
            # Add rounded corners effect
            for bar in bars:
                bar.set_capstyle('round')
            
            self.daily_canvas.draw()
            
            self.monthly_figure.clear()
            self.monthly_figure.patch.set_facecolor(chart_colors['background'])
            ax2 = self.monthly_figure.add_subplot(111)
            ax2.set_facecolor(chart_colors['background'])
            ax2.set_title('Monthly Attendance Overview', fontsize=16, fontweight='bold',
                         color=chart_colors['text'], pad=20)
            ax2.set_xlabel('Day of Month', fontsize=12, color=chart_colors['text'])
            ax2.set_ylabel('Number of Students', fontsize=12, color=chart_colors['text'])
            ax2.tick_params(colors=chart_colors['text'], labelsize=10)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color(chart_colors['grid'])
            ax2.spines['bottom'].set_color(chart_colors['grid'])
            ax2.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            
            self.monthly_canvas.draw()
            
            # Call update after a short delay to ensure UI is fully initialized
            QTimer.singleShot(500, self.update_attendance_report)
        except Exception as e:
            print(f"Error initializing reports: {e}")
        
        return reports_page
    
    def update_monthly_report(self):
        """Update the monthly attendance report"""
        selected_month = self.month_combo.currentIndex() + 1
        selected_year = self.year_spin.value()
        
        # Create a date string for the first day of the selected month
        selected_date = f"{selected_year}-{selected_month:02d}-01"
        self.update_monthly_chart(selected_date, "All Classes", True)
    
    def update_daily_chart(self, selected_date, selected_class="All Classes", has_location_columns=True):
        """Update daily attendance chart"""
        try:
            # Connect to database
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Get total students for the selected class
            if selected_class and selected_class != "All Classes":
                cursor.execute("SELECT COUNT(*) FROM students WHERE class = ?", (selected_class,))
            else:
                cursor.execute("SELECT COUNT(*) FROM students")
            
            total_students = cursor.fetchone()[0] or 0
            
            # Get present students for the selected date
            present_students = []
            for student_id in all_students:
                cursor.execute("""
                    SELECT status FROM attendance 
                    WHERE student_id = ? AND date = ?
                """, (student_id, selected_date))
                
                result = cursor.fetchone()
                if result and result[0] and result[0].lower() in ['present', 'p', '1']:
                    present_students.append(student_id)
            
            present_count = len(present_students)
            absent_count = total_students - present_count
            
            # Get location verification count if applicable
            location_verified_count = 0
            if has_location_columns:
                for student_id in present_students:
                    cursor.execute("""
                        SELECT location_verified FROM attendance 
                        WHERE student_id = ? AND date = ?
                    """, (student_id, selected_date))
                    
                    result = cursor.fetchone()
                    if result and result[0]:
                        location_verified_count += 1
            
            # Create figure and axis
            self.daily_figure.clear()
            ax = self.daily_figure.add_subplot(111)
            
            # Create bar chart
            labels = ['Present', 'Absent']
            counts = [present_count, absent_count]
            colors = ['#4CAF50', '#F44336']  # Green for present, red for absent
            
            print(f"Chart data - Present: {present_count}, Absent: {absent_count}, Total: {total_students}")
            
            bars = ax.bar(labels, counts, color=colors)
            
            # Add count labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom')
            
            # Add title and labels
            ax.set_title(f'Attendance for {selected_date}')
            ax.set_ylabel('Number of Students')
            
            # Add location verification info if available
            if has_location_columns and present_count > 0:
                location_text = f'Location Verified: {location_verified_count}/{present_count}'
                ax.text(0.5, -0.1, location_text, ha='center', transform=ax.transAxes)
            
            # Refresh canvas
            self.daily_canvas.draw()
            
            conn.close()
        except Exception as e:
            print(f"Error updating daily chart: {e}")
            import traceback
            traceback.print_exc()
    
    def update_monthly_chart(self, selected_date, selected_class="All Classes", has_location_columns=True):
        """Update monthly attendance chart with modern styling"""
        try:
            # Parse selected date
            date = datetime.strptime(selected_date, "%Y-%m-%d")
            
            # Calculate start and end of month
            start_of_month = date.replace(day=1).strftime("%Y-%m-%d")
            
            # Calculate end of month
            if date.month == 12:
                end_of_month = date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_of_month = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
            
            end_of_month = end_of_month.strftime("%Y-%m-%d")
            
            # Connect to database
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Construct query based on available columns
            if has_location_columns:
                query = """
                SELECT a.date, COUNT(*) as present_count,
                       SUM(CASE WHEN a.location_verified = 1 THEN 1 ELSE 0 END) as location_verified
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date BETWEEN ? AND ? AND a.status = 'Present'
                """
            else:
                query = """
                SELECT a.date, COUNT(*) as present_count
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date BETWEEN ? AND ? AND a.status = 'Present'
                """
            
            # Add class filter if selected
            if selected_class and selected_class != "All Classes":
                query += " AND s.class = ?"
                query += " GROUP BY a.date ORDER BY a.date"
                cursor.execute(query, (start_of_month, end_of_month, selected_class))
            else:
                query += " GROUP BY a.date ORDER BY a.date"
                cursor.execute(query, (start_of_month, end_of_month))
            
            results = cursor.fetchall()
            
            # Get total students for the selected class
            if selected_class and selected_class != "All Classes":
                cursor.execute("SELECT COUNT(*) FROM students WHERE class = ?", (selected_class,))
            else:
                cursor.execute("SELECT COUNT(*) FROM students")
            
            total_students = cursor.fetchone()[0]
            
            # Process results
            dates = []
            present_counts = []
            absent_counts = []
            
            # Create a dictionary to store results by date
            attendance_by_date = {}
            
            for row in results:
                attendance_date = row[0]
                present_count = row[1]
                attendance_by_date[attendance_date] = present_count
            
            # Generate all dates in the month
            current_date = datetime.strptime(start_of_month, "%Y-%m-%d")
            end_date = datetime.strptime(end_of_month, "%Y-%m-%d")
            
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                dates.append(date_str)
                
                # Get present count for this date (0 if no data)
                present_count = attendance_by_date.get(date_str, 0)
                present_counts.append(present_count)
                
                # Calculate absent count
                absent_count = total_students - present_count
                absent_counts.append(absent_count)
                
                # Move to next day
                current_date += timedelta(days=1)
            
            # Get modern chart colors
            chart_colors = ModernUIStyles.get_chart_colors()
            
            # Create figure with modern styling
            self.monthly_figure.clear()
            self.monthly_figure.patch.set_facecolor(chart_colors['background'])
            ax = self.monthly_figure.add_subplot(111)
            ax.set_facecolor(chart_colors['background'])
            
            # Create modern stacked bar chart
            x = range(len(dates))
            width = 0.75  # Slightly narrower bars for better appearance
            
            # Create bars with modern styling
            p1 = ax.bar(x, present_counts, width, 
                       color=chart_colors['present'], alpha=0.9, 
                       label='Present', edgecolor='white', linewidth=1.5)
            p2 = ax.bar(x, absent_counts, width, bottom=present_counts,
                       color=chart_colors['absent'], alpha=0.9, 
                       label='Absent', edgecolor='white', linewidth=1.5)
            
            # Add value labels on stacked bars for better readability
            for i, (present, absent) in enumerate(zip(present_counts, absent_counts)):
                if present > 0:  # Only show label if there's a value
                    ax.text(i, present/2, str(present), ha='center', va='center',
                           fontweight='600', fontsize=9, color='white')
                if absent > 0:
                    ax.text(i, present + absent/2, str(absent), ha='center', va='center',
                           fontweight='600', fontsize=9, color='white')
            
            # Format x-axis with modern styling
            date_labels = [datetime.strptime(d, "%Y-%m-%d").strftime("%d") for d in dates]
            
            # Show every nth label to avoid crowding
            step = max(1, len(dates) // 15)  # Show about 15 labels max
            ax.set_xticks(x[::step])
            ax.set_xticklabels(date_labels[::step], rotation=45)
            
            # Modern title and labels styling
            month_name = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%B %Y")
            ax.set_title(f'Monthly Attendance Overview - {month_name}', 
                        fontsize=18, fontweight='bold', 
                        color=chart_colors['text'], pad=25)
            
            ax.set_xlabel('Day of Month', fontsize=14, fontweight='600', 
                         color=chart_colors['text'], labelpad=15)
            ax.set_ylabel('Number of Students', fontsize=14, fontweight='600', 
                         color=chart_colors['text'], labelpad=15)
            
            # Modern axis styling
            ax.tick_params(colors=chart_colors['text'], labelsize=11, 
                          which='both', direction='out', length=6, width=1)
            
            # Remove top and right spines for cleaner look
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(chart_colors['grid'])
            ax.spines['bottom'].set_color(chart_colors['grid'])
            ax.spines['left'].set_linewidth(1)
            ax.spines['bottom'].set_linewidth(1)
            
            # Add subtle grid
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.8, color=chart_colors['grid'])
            ax.set_axisbelow(True)  # Grid behind bars
            
            # Modern legend styling
            legend = ax.legend(loc='upper right', frameon=True, fancybox=True, 
                              shadow=False, framealpha=0.95, fontsize=12)
            legend.get_frame().set_facecolor('#f8f9fa')
            legend.get_frame().set_edgecolor('#dee2e6')
            legend.get_frame().set_linewidth(1)
            
            # Add summary stats
            total_present = sum(present_counts)
            total_absent = sum(absent_counts)
            total_days = len([d for d in present_counts if d > 0 or absent_counts[present_counts.index(d)] > 0])
            
            if total_days > 0:
                avg_attendance = (total_present / (total_present + total_absent)) * 100 if (total_present + total_absent) > 0 else 0
                stats_text = f'Days with records: {total_days} | Avg. Attendance: {avg_attendance:.1f}%'
                ax.text(0.02, 0.98, stats_text, ha='left', va='top',
                       transform=ax.transAxes, fontsize=11, 
                       fontweight='600', color=chart_colors['text'],
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
            
            # Adjust layout for better spacing
            self.monthly_figure.tight_layout()
            
            # Refresh canvas
            self.monthly_canvas.draw()
            
            conn.close()
        except Exception as e:
            print(f"Error updating monthly chart: {e}")
    
    def filter_attendance_table(self):
        """Filter the attendance table based on the selected class"""
        selected_date = self.report_date_picker.date().toString("yyyy-MM-dd")
        self.update_attendance_table(selected_date)
    
    def export_attendance_report(self):
        """Export the attendance report to Excel"""
        try:
            selected_date = self.report_date_picker.date().toString("yyyy-MM-dd")
            selected_class = self.report_class_combo.currentText()
            
            # Ask for save location
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save Attendance Report", 
                f"Attendance_Report_{selected_date}_{selected_class.replace(' ', '_')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_name:
                return
            
            # Open file for writing
            with open(file_name, 'w', newline='') as file:
                import csv
                writer = csv.writer(file)
                
                # Write header
                writer.writerow(["Student ID", "Name", "Time", "Status"])
                
                # Write data
                for row in range(self.attendance_table.rowCount()):
                    row_data = []
                    for col in range(self.attendance_table.columnCount()):
                        item = self.attendance_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Success", f"Attendance report exported to {file_name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export report: {str(e)}")
    
    def update_attendance_report(self):
        """Update attendance report table and charts"""
        try:
            # Get selected date and class
            selected_date = self.report_date_picker.date().toString("yyyy-MM-dd")
            selected_class = self.report_class_combo.currentText()
            
            # Connect to database
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Get column names from attendance table to check if location columns exist
            cursor.execute("PRAGMA table_info(attendance)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            has_location_columns = ('latitude' in column_names and 
                                  'longitude' in column_names and 
                                  'location_verified' in column_names)
            
            # Construct query based on available columns
            if has_location_columns:
                query = """
                SELECT s.id, s.name, s.class, a.date, a.status, a.location_verified
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
                """
            else:
                query = """
                SELECT s.id, s.name, s.class, a.date, a.status
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
                """
            
            # Add class filter if selected
            if selected_class and selected_class != "All Classes":
                query += " WHERE s.class = ?"
                cursor.execute(query, (selected_date, selected_class))
            else:
                cursor.execute(query, (selected_date,))
            
            attendance_data = cursor.fetchall()
            
            # Clear table
            self.attendance_table.setRowCount(0)
            
            # Set up table headers based on available columns
            if has_location_columns:
                self.attendance_table.setColumnCount(6)
                self.attendance_table.setHorizontalHeaderLabels(["ID", "Name", "Class", "Date", "Status", "Location Verified"])
            else:
                self.attendance_table.setColumnCount(5)
                self.attendance_table.setHorizontalHeaderLabels(["ID", "Name", "Class", "Date", "Status"])
            
            # Populate table
            for row_idx, student in enumerate(attendance_data):
                self.attendance_table.insertRow(row_idx)
                
                # Add student data
                for col_idx, value in enumerate(student):
                    # Skip null values
                    if value is None:
                        if col_idx == 4:  # Status column
                            value = "Absent"
                        else:
                            value = ""
                    
                    # Format boolean values for location_verified
                    if col_idx == 5 and value is not None:  # Location verified column
                        value = "✓" if value else "✗"
                    
                    # Format status
                    if col_idx == 4:  # Status column
                        if value == "Present":
                            color = QColor(200, 255, 200)  # Light green
                        else:
                            color = QColor(255, 200, 200)  # Light red
                        
                        item = QTableWidgetItem(str(value))
                        item.setBackground(color)
                    else:
                        item = QTableWidgetItem(str(value))
                    
                    self.attendance_table.setItem(row_idx, col_idx, item)
            
            # Resize columns to content
            self.attendance_table.resizeColumnsToContents()
            
            # Update charts
            self.update_daily_chart(selected_date, selected_class, has_location_columns)
            self.update_monthly_chart(selected_date, selected_class, has_location_columns)
            
            conn.close()
        except Exception as e:
            print(f"Error updating attendance table: {e}")
    
    
    def update_daily_chart(self, selected_date, selected_class="All Classes", has_location_columns=True):
        """Update daily attendance chart with modern styling"""
        try:
            # Connect to database
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Get total students for the selected class
            if selected_class and selected_class != "All Classes":
                cursor.execute("SELECT COUNT(*) FROM students WHERE class = ?", (selected_class,))
            else:
                cursor.execute("SELECT COUNT(*) FROM students")
            
            total_students = cursor.fetchone()[0] or 0
            
            # Get present students for the selected date
            present_students = []
            all_students = []
            if selected_class and selected_class != "All Classes":
                cursor.execute("SELECT id FROM students WHERE class = ?", (selected_class,))
            else:
                cursor.execute("SELECT id FROM students")
            
            all_students = [row[0] for row in cursor.fetchall()]
            
            for student_id in all_students:
                cursor.execute("""
                    SELECT status FROM attendance 
                    WHERE student_id = ? AND date = ?
                """, (student_id, selected_date))
                
                result = cursor.fetchone()
                if result and result[0] and result[0].lower() in ['present', 'p', '1']:
                    present_students.append(student_id)
            
            present_count = len(present_students)
            absent_count = total_students - present_count
            
            # Get location verification count if applicable
            location_verified_count = 0
            if has_location_columns:
                for student_id in present_students:
                    cursor.execute("""
                        SELECT location_verified FROM attendance 
                        WHERE student_id = ? AND date = ?
                    """, (student_id, selected_date))
                    
                    result = cursor.fetchone()
                    if result and result[0]:
                        location_verified_count += 1
            
            # Get modern chart colors
            chart_colors = ModernUIStyles.get_chart_colors()
            
            # Create figure with modern styling
            self.daily_figure.clear()
            self.daily_figure.patch.set_facecolor(chart_colors['background'])
            ax = self.daily_figure.add_subplot(111)
            ax.set_facecolor(chart_colors['background'])
            
            # Create modern bar chart
            labels = ['Present', 'Absent']
            counts = [present_count, absent_count]
            colors = [chart_colors['present'], chart_colors['absent']]
            
            # Create bars with modern styling
            bars = ax.bar(labels, counts, color=colors, alpha=0.85, 
                         edgecolor='white', linewidth=2.5, 
                         width=0.6)  # Make bars slightly narrower
            
            # Add gradient-like effect by adding a subtle shadow
            for bar in bars:
                bar.set_capstyle('round')  # Rounded bar tops
            
            # Add value labels on top of bars with modern styling
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                if height > 0:  # Only show label if there's a value
                    ax.text(bar.get_x() + bar.get_width()/2., height + max(total_students * 0.02, 0.5),
                           f'{int(height)}', ha='center', va='bottom',
                           fontsize=14, fontweight='bold', color=chart_colors['text'])
            
            # Modern title styling
            title_text = f'Daily Attendance - {selected_date}'
            ax.set_title(title_text, fontsize=18, fontweight='bold', 
                        color=chart_colors['text'], pad=25)
            
            # Modern axis styling
            ax.set_ylabel('Number of Students', fontsize=14, fontweight='600', 
                         color=chart_colors['text'], labelpad=15)
            ax.tick_params(colors=chart_colors['text'], labelsize=12, 
                          which='both', direction='out', length=6, width=1)
            
            # Remove top and right spines for cleaner look
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(chart_colors['grid'])
            ax.spines['bottom'].set_color(chart_colors['grid'])
            ax.spines['left'].set_linewidth(1)
            ax.spines['bottom'].set_linewidth(1)
            
            # Add subtle grid
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.8, color=chart_colors['grid'])
            ax.set_axisbelow(True)  # Grid behind bars
            
            # Add percentage labels
            if total_students > 0:
                present_percent = (present_count / total_students) * 100
                absent_percent = (absent_count / total_students) * 100
                
                # Add percentage text below bars
                for i, (bar, percent) in enumerate(zip(bars, [present_percent, absent_percent])):
                    ax.text(bar.get_x() + bar.get_width()/2., -max(total_students * 0.08, 1),
                           f'{percent:.1f}%', ha='center', va='top',
                           fontsize=11, fontweight='500', color=chart_colors['text'])
            
            # Add location verification info if available
            if has_location_columns and present_count > 0:
                location_text = f'Location Verified: {location_verified_count}/{present_count} students'
                ax.text(0.98, 0.02, location_text, ha='right', va='bottom',
                       transform=ax.transAxes, fontsize=10, 
                       style='italic', color=chart_colors['text'], alpha=0.8)
            
            # Add summary stats in corner
            stats_text = f'Total: {total_students} students'
            ax.text(0.02, 0.98, stats_text, ha='left', va='top',
                   transform=ax.transAxes, fontsize=10, 
                   fontweight='600', color=chart_colors['text'])
            
            # Adjust layout for better spacing
            try:
                self.daily_figure.tight_layout()
            except Exception as e:
                print(f"Warning: Could not apply tight_layout: {e}")
                # Continue without tight_layout if it fails
            
            # Refresh canvas
            self.daily_canvas.draw()
            
            conn.close()
        except Exception as e:
            print(f"Error updating daily chart: {e}")
            import traceback
            traceback.print_exc()
    
    def update_monthly_chart(self, selected_date, selected_class="All Classes", has_location_columns=True):
        """Update monthly attendance chart"""
        try:
            # Parse selected date
            date = datetime.strptime(selected_date, "%Y-%m-%d")
            
            # Calculate start and end of month
            start_of_month = date.replace(day=1).strftime("%Y-%m-%d")
            
            # Calculate end of month
            if date.month == 12:
                end_of_month = date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_of_month = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
            
            end_of_month = end_of_month.strftime("%Y-%m-%d")
            
            # Connect to database
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Construct query based on available columns
            if has_location_columns:
                query = """
                SELECT a.date, COUNT(*) as present_count,
                       SUM(CASE WHEN a.location_verified = 1 THEN 1 ELSE 0 END) as location_verified
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date BETWEEN ? AND ? AND a.status = 'Present'
                """
            else:
                query = """
                SELECT a.date, COUNT(*) as present_count
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date BETWEEN ? AND ? AND a.status = 'Present'
                """
            
            # Add class filter if selected
            if selected_class and selected_class != "All Classes":
                query += " AND s.class = ?"
                query += " GROUP BY a.date ORDER BY a.date"
                cursor.execute(query, (start_of_month, end_of_month, selected_class))
            else:
                query += " GROUP BY a.date ORDER BY a.date"
                cursor.execute(query, (start_of_month, end_of_month))
            
            results = cursor.fetchall()
            
            # Get total students for the selected class
            if selected_class and selected_class != "All Classes":
                cursor.execute("SELECT COUNT(*) FROM students WHERE class = ?", (selected_class,))
            else:
                cursor.execute("SELECT COUNT(*) FROM students")
            
            total_students = cursor.fetchone()[0]
            
            # Process results
            dates = []
            present_counts = []
            absent_counts = []
            
            # Create a dictionary to store results by date
            attendance_by_date = {}
            
            for row in results:
                attendance_date = row[0]
                present_count = row[1]
                attendance_by_date[attendance_date] = present_count
            
            # Generate all dates in the month
            current_date = datetime.strptime(start_of_month, "%Y-%m-%d")
            end_date = datetime.strptime(end_of_month, "%Y-%m-%d")
            
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                dates.append(date_str)
                
                # Get present count for this date (0 if no data)
                present_count = attendance_by_date.get(date_str, 0)
                present_counts.append(present_count)
                
                # Calculate absent count
                absent_count = total_students - present_count
                absent_counts.append(absent_count)
                
                # Move to next day
                current_date += timedelta(days=1)
            
            # Create figure and axis
            self.monthly_figure.clear()
            ax = self.monthly_figure.add_subplot(111)
            
            # Create stacked bar chart
            x = range(len(dates))
            width = 0.8
            
            p1 = ax.bar(x, present_counts, width, color='#4CAF50', label='Present')
            p2 = ax.bar(x, absent_counts, width, bottom=present_counts, color='#F44336', label='Absent')
            
            # Format x-axis with dates
            ax.set_xticks(x)
            ax.set_xticklabels([datetime.strptime(d, "%Y-%m-%d").strftime("%d") for d in dates], rotation=45)
            
            # Add title and labels
            month_name = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%B %Y")
            ax.set_title(f'Monthly Attendance - {month_name}')
            ax.set_xlabel('Day of Month')
            ax.set_ylabel('Number of Students')
            
            # Add legend
            ax.legend()
            
            # Adjust layout
            self.monthly_figure.tight_layout()
            
            # Refresh canvas
            self.monthly_canvas.draw()
            
            conn.close()
        except Exception as e:
            print(f"Error updating monthly chart: {e}")
    
    def filter_attendance_table(self):
        """Filter the attendance table based on the selected class"""
        selected_date = self.report_date_picker.date().toString("yyyy-MM-dd")
        self.update_attendance_table(selected_date)
    
    def export_attendance_report(self):
        """Export the attendance report to Excel"""
        try:
            selected_date = self.report_date_picker.date().toString("yyyy-MM-dd")
            selected_class = self.report_class_combo.currentText()
            
            # Ask for save location
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save Attendance Report", 
                f"Attendance_Report_{selected_date}_{selected_class.replace(' ', '_')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_name:
                return
            
            # Open file for writing
            with open(file_name, 'w', newline='') as file:
                import csv
                writer = csv.writer(file)
                
                # Write header
                writer.writerow(["Student ID", "Name", "Time", "Status"])
                
                # Write data
                for row in range(self.attendance_table.rowCount()):
                    row_data = []
                    for col in range(self.attendance_table.columnCount()):
                        item = self.attendance_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Success", f"Attendance report exported to {file_name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export report: {str(e)}")
    
    def update_attendance_table(self, date=None):
        """Update the attendance table with data from the database"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Clear the table
            self.attendance_table.setRowCount(0)
            
            # Get the selected class
            selected_class = self.report_class_combo.currentText()
            
            # Get all students
            students = self.db.get_all_students()
            
            # Filter by class if needed
            if selected_class != "All Classes":
                students = [s for s in students if s[2] == selected_class]
            
            # Add each student to the table
            for row, student in enumerate(students):
                self.attendance_table.insertRow(row)
                
                # Student ID
                id_item = QTableWidgetItem(student[0])
                self.attendance_table.setItem(row, 0, id_item)
                
                # Name
                name_item = QTableWidgetItem(student[1])
                self.attendance_table.setItem(row, 1, name_item)
                
                # Time and Status
                if student[6]:  # If attendance record exists
                    time_item = QTableWidgetItem(student[6] if student[6] else "")
                    status_item = QTableWidgetItem(student[7] if student[7] else "absent")
                    
                    # Color code the status
                    if student[7] == "present":
                        status_item.setBackground(QColor("#E8F5E9"))  # Light green
                    else:
                        status_item.setBackground(QColor("#FFEBEE"))  # Light red
                else:
                    time_item = QTableWidgetItem("")
                    status_item = QTableWidgetItem("absent")
                    status_item.setBackground(QColor("#FFEBEE"))  # Light red
                
                self.attendance_table.setItem(row, 2, time_item)
                self.attendance_table.setItem(row, 3, status_item)
            
            # Resize columns to content
            self.attendance_table.resizeColumnsToContents()
        except Exception as e:
            print(f"Error updating attendance table: {str(e)}")

    def get_all_classes(self):
        """Get all unique classes from the database"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT class FROM students ORDER BY class")
            classes = [row[0] for row in cursor.fetchall()]
            conn.close()
            return classes
        except Exception as e:
            print(f"Error retrieving classes: {e}")
            return []
    
    def create_chatbot_page(self):
        """Create the AI Assistant chatbot page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add header
        header_layout = QHBoxLayout()
        header = QLabel("🤖 AI Attendance Assistant")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(header)
        
        # User selector
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Login as:"))
        self.user_role_combo = QComboBox()
        self.user_role_combo.addItems(["Student", "Teacher"])
        self.user_role_combo.currentTextChanged.connect(self.change_chatbot_user)
        user_layout.addWidget(self.user_role_combo)
        
        # Student ID input (for students)
        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("Enter your Student ID (e.g., S12345)")
        self.student_id_input.setText("S12345")  # Default value
        self.student_id_input.textChanged.connect(self.update_chatbot_user)
        user_layout.addWidget(QLabel("Student ID:"))
        user_layout.addWidget(self.student_id_input)
        
        user_layout.addStretch()
        header_layout.addLayout(user_layout)
        layout.addLayout(header_layout)
        
        # Add separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #E0E0E0; margin: 10px 0px;")
        layout.addWidget(line)
        
        # Main chat area
        chat_layout = QHBoxLayout()
        
        # Chat history area
        chat_group = QGroupBox("Chat with AI Assistant")
        chat_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        chat_group_layout = QVBoxLayout(chat_group)
        
        # Chat display area
        self.chat_display = QScrollArea()
        self.chat_display.setMinimumHeight(400)
        self.chat_display.setStyleSheet("""
            QScrollArea {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
        """)
        
        # Chat content widget
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setAlignment(Qt.AlignTop)
        
        # Add welcome message
        self.add_message("AI Assistant", "Hello! I'm your attendance assistant. How can I help you today? Try asking:\n• 'Did I attend yesterday?'\n• 'My attendance percentage'\n• 'Help' for more options", is_bot=True)
        
        self.chat_display.setWidget(self.chat_content)
        self.chat_display.setWidgetResizable(True)
        chat_group_layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your question here...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #BDBDBD;
                border-radius: 20px;
                background-color: white;
                font-size: 14px;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.chat_input)
        
        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        chat_group_layout.addLayout(input_layout)
        chat_layout.addWidget(chat_group, 2)
        
        # Quick actions panel
        actions_group = QGroupBox("Quick Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        actions_layout = QVBoxLayout(actions_group)
        
        # Quick question buttons
        quick_questions = [
            ("📊 My Attendance %", "What's my attendance percentage?"),
            ("📅 Yesterday's Status", "Did I attend yesterday?"),
            ("📈 Monthly Summary", "How many days was I absent this month?"),
            ("👥 Check Student", "Tell me Rakshit attendance"),
            ("❓ Help", "Help"),
            ("📋 Daily Summary", "Show daily attendance summary")
        ]
        
        for button_text, query in quick_questions:
            btn = QPushButton(button_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 8px;
                    text-align: left;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border-color: #2196F3;
                }
            """)
            btn.clicked.connect(lambda checked, q=query: self.send_quick_question(q))
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        chat_layout.addWidget(actions_group, 1)
        
        layout.addLayout(chat_layout)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(page)
    
    def change_chatbot_user(self):
        """Handle user role change in chatbot"""
        role = self.user_role_combo.currentText().lower()
        if role == "student":
            self.student_id_input.setVisible(True)
            student_id = self.student_id_input.text() or "S12345"
            self.chatbot.set_user(student_id, "student")
        else:
            self.student_id_input.setVisible(False)
            self.chatbot.set_user("teacher", "teacher")
        
        # Clear chat and add appropriate welcome message
        self.clear_chat()
        welcome_msg = self.chatbot.generate_response("hello")
        self.add_message("AI Assistant", welcome_msg, is_bot=True)
    
    def update_chatbot_user(self):
        """Update chatbot user when student ID changes"""
        if self.user_role_combo.currentText() == "Student":
            student_id = self.student_id_input.text() or "S12345"
            self.chatbot.set_user(student_id, "student")
    
    def clear_chat(self):
        """Clear the chat display"""
        # Remove all child widgets from chat layout
        while self.chat_layout.count():
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def add_message(self, sender, message, is_bot=False):
        """Add a message to the chat display"""
        message_widget = QWidget()
        message_layout = QHBoxLayout(message_widget)
        message_layout.setContentsMargins(10, 5, 10, 5)
        
        # Create message bubble
        bubble = QLabel()
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        if is_bot:
            # Bot message styling
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #E3F2FD;
                    border: 1px solid #2196F3;
                    border-radius: 15px;
                    padding: 10px;
                    margin: 5px;
                    color: #1565C0;
                }
            """)
            bubble.setText(f"🤖 {sender}:\n{message}")
            message_layout.addWidget(bubble)
            message_layout.addStretch()
        else:
            # User message styling
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #C8E6C9;
                    border: 1px solid #4CAF50;
                    border-radius: 15px;
                    padding: 10px;
                    margin: 5px;
                    color: #2E7D32;
                }
            """)
            bubble.setText(f"👤 You:\n{message}")
            message_layout.addStretch()
            message_layout.addWidget(bubble)
        
        self.chat_layout.addWidget(message_widget)
        
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()))
    
    def send_message(self):
        """Send user message to chatbot"""
        user_message = self.chat_input.text().strip()
        if not user_message:
            return
        
        # Add user message to chat
        self.add_message("You", user_message, is_bot=False)
        
        # Clear input
        self.chat_input.clear()
        
        # Get bot response
        try:
            bot_response = self.chatbot.generate_response(user_message)
            self.add_message("AI Assistant", bot_response, is_bot=True)
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}\nPlease try again."
            self.add_message("AI Assistant", error_msg, is_bot=True)
    
    def send_quick_question(self, question):
        """Send a predefined quick question"""
        self.chat_input.setText(question)
        self.send_message()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 
