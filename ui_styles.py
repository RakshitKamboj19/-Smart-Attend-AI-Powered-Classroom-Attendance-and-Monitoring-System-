"""
Modern UI Design System for Student Attendance System
Professional color scheme, typography, and component styles
"""

class ModernUIStyles:
    """Modern UI design system with cohesive styling"""
    
    # Color Palette - Enhanced Professional Colors with Better Contrast
    COLORS = {
        # Primary Colors - Enhanced for better visibility
        'primary': '#2563EB',           # Blue - Main brand color (better contrast)
        'primary_light': '#3B82F6',     # Light blue
        'primary_dark': '#1D4ED8',      # Dark blue
        'primary_bg': '#EFF6FF',        # Very light blue background
        'primary_hover': '#1E40AF',     # Primary hover state
        
        # Secondary Colors - Enhanced green tones
        'secondary': '#059669',         # Emerald green (darker for better contrast)
        'secondary_light': '#10B981',   # Light emerald
        'secondary_dark': '#047857',    # Dark emerald
        'secondary_bg': '#ECFDF5',      # Very light emerald background
        'secondary_hover': '#065F46',   # Secondary hover state
        
        # Accent Colors - Enhanced amber/orange
        'accent': '#DC2626',            # Red accent for important actions
        'accent_light': '#EF4444',      # Light red
        'accent_dark': '#B91C1C',       # Dark red
        'accent_bg': '#FEF2F2',         # Very light red background
        'accent_hover': '#991B1B',      # Accent hover state
        
        # Status Colors - High contrast versions
        'success': '#059669',           # Green for success (darker)
        'warning': '#D97706',           # Orange for warning (darker)
        'error': '#DC2626',             # Red for error (darker)
        'info': '#2563EB',              # Blue for info (darker)
        
        # Neutral Colors - Enhanced contrast scale
        'white': '#FFFFFF',
        'black': '#000000',
        'gray_50': '#F8FAFC',           # Lightest gray
        'gray_100': '#F1F5F9',          # Very light gray
        'gray_200': '#E2E8F0',          # Light gray
        'gray_300': '#CBD5E1',          # Medium light gray
        'gray_400': '#94A3B8',          # Medium gray
        'gray_500': '#64748B',          # Dark medium gray
        'gray_600': '#475569',          # Dark gray
        'gray_700': '#334155',          # Very dark gray
        'gray_800': '#1E293B',          # Almost black
        'gray_900': '#0F172A',          # Darkest
        
        # Enhanced gradients for better visual appeal
        'gradient_primary': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563EB, stop:1 #1D4ED8)',
        'gradient_secondary': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #059669, stop:1 #047857)',
        'gradient_accent': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #DC2626, stop:1 #B91C1C)',
        'gradient_dark': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #0F172A)',
        'gradient_light': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #F8FAFC)',
    }
    
    # Enhanced Typography System for Better Readability
    FONTS = {
        'primary': 'Inter, Segoe UI, system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
        'heading': 'Inter, Segoe UI, system-ui, sans-serif',
        'mono': 'JetBrains Mono, Consolas, Monaco, "Courier New", monospace',
        
        # Enhanced font sizes (in px) - Larger for better readability
        'xs': '11px',      # Slightly smaller for captions
        'sm': '13px',      # Small text, labels
        'base': '15px',    # Base body text - increased from 16px
        'md': '16px',      # Medium text
        'lg': '18px',      # Large text
        'xl': '20px',      # Extra large
        '2xl': '24px',     # Headings
        '3xl': '28px',     # Large headings
        '4xl': '32px',     # Major headings
        '5xl': '40px',     # Hero text
        '6xl': '48px',     # Display text
        
        # Font weights
        'light': '300',
        'normal': '400',
        'medium': '500',
        'semibold': '600',
        'bold': '700',
        'extrabold': '800',
    }
    
    # Spacing System (in px)
    SPACING = {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        '2xl': '48px',
        '3xl': '64px',
    }
    
    # Border Radius
    RADIUS = {
        'sm': '6px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '24px',
        'full': '9999px',
    }
    
    # Shadows
    SHADOWS = {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    }

    @classmethod
    def get_main_window_style(cls):
        """Get main window stylesheet"""
        return f"""
            QMainWindow {{
                background: {cls.COLORS['gray_50']};
                color: {cls.COLORS['gray_900']};
                font-family: {cls.FONTS['primary']};
                font-size: {cls.FONTS['base']};
            }}
        """

    @classmethod
    def get_sidebar_style(cls):
        """Get sidebar stylesheet"""
        return f"""
            QWidget#sidebar {{
                background: {cls.COLORS['white']};
                border-right: 1px solid {cls.COLORS['gray_200']};
                min-width: 280px;
                max-width: 280px;
            }}
            
            /* Logo Section */
            QWidget#logo_section {{
                background: {cls.COLORS['gradient_primary']};
                border-radius: {cls.RADIUS['lg']};
                margin: {cls.SPACING['md']};
                padding: {cls.SPACING['lg']};
            }}
            
            /* Navigation Buttons */
            QPushButton#nav_button {{
                background: transparent;
                color: {cls.COLORS['gray_700']};
                text-align: left;
                padding: {cls.SPACING['md']} {cls.SPACING['lg']};
                border: none;
                border-radius: {cls.RADIUS['md']};
                font-size: {cls.FONTS['sm']};
                font-weight: 500;
                margin: 2px {cls.SPACING['md']};
                min-height: 48px;
            }}
            
            QPushButton#nav_button:hover {{
                background: {cls.COLORS['gray_100']};
                color: {cls.COLORS['primary']};
            }}
            
            QPushButton#nav_button:pressed,
            QPushButton#nav_button:checked {{
                background: {cls.COLORS['primary_bg']};
                color: {cls.COLORS['primary']};
                border-left: 4px solid {cls.COLORS['primary']};
            }}
            
            /* User Section */
            QWidget#user_section {{
                background: {cls.COLORS['gray_50']};
                border-radius: {cls.RADIUS['lg']};
                margin: {cls.SPACING['md']};
                padding: {cls.SPACING['md']};
                border: 1px solid {cls.COLORS['gray_200']};
            }}
        """

    @classmethod
    def get_card_style(cls):
        """Get modern card stylesheet"""
        return f"""
            QGroupBox {{
                background: {cls.COLORS['white']};
                border: 1px solid {cls.COLORS['gray_200']};
                border-radius: {cls.RADIUS['lg']};
                padding: {cls.SPACING['lg']};
                margin: {cls.SPACING['md']};
                color: {cls.COLORS['gray_900']};
                font-weight: 600;
                font-size: {cls.FONTS['lg']};
            }}
            
            QGroupBox::title {{
                color: {cls.COLORS['gray_800']};
                font-size: {cls.FONTS['lg']};
                font-weight: 700;
                padding: {cls.SPACING['xs']} {cls.SPACING['sm']};
                background: {cls.COLORS['white']};
                border-radius: {cls.RADIUS['sm']};
                margin-top: -10px;
                margin-left: {cls.SPACING['md']};
            }}
        """

    @classmethod
    def get_button_style(cls, variant='primary'):
        """Get modern button stylesheet"""
        if variant == 'primary':
            bg = cls.COLORS['primary']
            bg_hover = cls.COLORS['primary_dark']
            color = cls.COLORS['white']
        elif variant == 'secondary':
            bg = cls.COLORS['secondary']
            bg_hover = cls.COLORS['secondary_dark']
            color = cls.COLORS['white']
        elif variant == 'outline':
            bg = 'transparent'
            bg_hover = cls.COLORS['gray_50']
            color = cls.COLORS['primary']
        else:  # ghost
            bg = 'transparent'
            bg_hover = cls.COLORS['gray_100']
            color = cls.COLORS['gray_700']
        
        return f"""
            QPushButton {{
                background: {bg};
                color: {color};
                border: {'1px solid ' + cls.COLORS['primary'] if variant == 'outline' else 'none'};
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['sm']} {cls.SPACING['lg']};
                font-size: {cls.FONTS['sm']};
                font-weight: 600;
                font-family: {cls.FONTS['primary']};
                min-height: 40px;
            }}
            
            QPushButton:hover {
                background: {bg_hover};
            }
            
            QPushButton:pressed {
                background: {bg_hover};
            }
            
            QPushButton:disabled {{
                background: {cls.COLORS['gray_200']};
                color: {cls.COLORS['gray_400']};
                border: none;
            }}
        """

    @classmethod
    def get_input_style(cls):
        """Get modern input field stylesheet"""
        return f"""
            QLineEdit, QSpinBox, QDateEdit, QComboBox {{
                background: {cls.COLORS['white']};
                border: 1px solid {cls.COLORS['gray_300']};
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['sm']} {cls.SPACING['md']};
                color: {cls.COLORS['gray_900']};
                font-size: {cls.FONTS['sm']};
                font-family: {cls.FONTS['primary']};
                min-height: 40px;
                selection-background-color: {cls.COLORS['primary_light']};
            }}
            
            QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QComboBox:focus {{
                border: 2px solid {cls.COLORS['primary']};
                background: {cls.COLORS['white']};
                outline: none;
            }}
            
            QLineEdit:hover, QSpinBox:hover, QDateEdit:hover, QComboBox:hover {{
                border-color: {cls.COLORS['primary_light']};
            }}
            
            QLineEdit::placeholder {{
                color: {cls.COLORS['gray_400']};
                font-style: italic;
            }}
            
            QComboBox::drop-down {{
                border: none;
                padding-right: {cls.SPACING['sm']};
            }}
            
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }}
        """

    @classmethod
    def get_table_style(cls):
        """Get modern table stylesheet"""
        return f"""
            QTableWidget {{
                background: {cls.COLORS['white']};
                border: 1px solid {cls.COLORS['gray_200']};
                border-radius: {cls.RADIUS['lg']};
                gridline-color: {cls.COLORS['gray_200']};
                color: {cls.COLORS['gray_900']};
                font-size: {cls.FONTS['sm']};
                font-family: {cls.FONTS['primary']};
                selection-background-color: {cls.COLORS['primary_bg']};
            }}
            
            QTableWidget::item {{
                padding: {cls.SPACING['md']} {cls.SPACING['sm']};
                border-bottom: 1px solid {cls.COLORS['gray_100']};
            }}
            
            QTableWidget::item:selected {{
                background: {cls.COLORS['primary_bg']};
                color: {cls.COLORS['primary_dark']};
            }}
            
            QTableWidget::item:hover {{
                background: {cls.COLORS['gray_50']};
            }}
            
            QHeaderView::section {{
                background: {cls.COLORS['gray_100']};
                color: {cls.COLORS['gray_800']};
                padding: {cls.SPACING['md']} {cls.SPACING['sm']};
                border: none;
                border-bottom: 2px solid {cls.COLORS['primary']};
                font-weight: 600;
                font-size: {cls.FONTS['sm']};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            QHeaderView::section:first {{
                border-top-left-radius: {cls.RADIUS['lg']};
            }}
            
            QHeaderView::section:last {{
                border-top-right-radius: {cls.RADIUS['lg']};
            }}
        """

    @classmethod
    def get_tab_style(cls):
        """Get modern tab widget stylesheet"""
        return f"""
            QTabWidget::pane {{
                background: {cls.COLORS['white']};
                border: 1px solid {cls.COLORS['gray_200']};
                border-radius: {cls.RADIUS['lg']};
                margin-top: -1px;
            }}
            
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            
            QTabBar::tab {{
                background: {cls.COLORS['gray_100']};
                color: {cls.COLORS['gray_600']};
                padding: {cls.SPACING['sm']} {cls.SPACING['lg']};
                margin-right: 2px;
                border-top-left-radius: {cls.RADIUS['md']};
                border-top-right-radius: {cls.RADIUS['md']};
                font-weight: 500;
                font-size: {cls.FONTS['sm']};
                min-width: 120px;
            }}
            
            QTabBar::tab:selected {{
                background: {cls.COLORS['white']};
                color: {cls.COLORS['primary']};
                border-bottom: 2px solid {cls.COLORS['primary']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background: {cls.COLORS['gray_200']};
                color: {cls.COLORS['gray_700']};
            }}
        """

    @classmethod
    def get_scrollbar_style(cls):
        """Get modern scrollbar stylesheet"""
        return f"""
            QScrollBar:vertical {{
                background: {cls.COLORS['gray_100']};
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: {cls.COLORS['gray_400']};
                border-radius: 6px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {cls.COLORS['gray_500']};
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background: {cls.COLORS['gray_100']};
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {cls.COLORS['gray_400']};
                border-radius: 6px;
                min-width: 30px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: {cls.COLORS['gray_500']};
            }}
        """

    @classmethod
    def get_chart_colors(cls):
        """Get modern color scheme for charts"""
        return {
            'present': cls.COLORS['secondary'],
            'absent': cls.COLORS['error'],
            'verified': cls.COLORS['primary'],
            'background': cls.COLORS['white'],
            'text': cls.COLORS['gray_800'],
            'grid': cls.COLORS['gray_200'],
        }

    @classmethod
    def get_status_colors(cls):
        """Get status indicator colors"""
        return {
            'success': cls.COLORS['success'],
            'warning': cls.COLORS['warning'],
            'error': cls.COLORS['error'],
            'info': cls.COLORS['info'],
        }

    @classmethod
    def get_complete_stylesheet(cls):
        """Get complete application stylesheet"""
        return f"""
            /* Main Application Styles */
            {cls.get_main_window_style()}
            {cls.get_sidebar_style()}
            {cls.get_card_style()}
            {cls.get_input_style()}
            {cls.get_table_style()}
            {cls.get_tab_style()}
            {cls.get_scrollbar_style()}
            
            /* Labels */
            QLabel {{
                color: {cls.COLORS['gray_800']};
                font-family: {cls.FONTS['primary']};
                font-size: {cls.FONTS['sm']};
            }}
            
            QLabel#title {{
                font-size: {cls.FONTS['2xl']};
                font-weight: 700;
                color: {cls.COLORS['gray_900']};
                margin-bottom: {cls.SPACING['lg']};
            }}
            
            QLabel#subtitle {{
                font-size: {cls.FONTS['lg']};
                font-weight: 600;
                color: {cls.COLORS['gray_700']};
                margin-bottom: {cls.SPACING['md']};
            }}
            
            /* Status Labels */
            QLabel#status_success {{
                background: {cls.COLORS['secondary_bg']};
                color: {cls.COLORS['secondary_dark']};
                border: 1px solid {cls.COLORS['secondary_light']};
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['xs']} {cls.SPACING['sm']};
                font-weight: 600;
            }}
            
            QLabel#status_error {{
                background: rgba(239, 68, 68, 0.1);
                color: {cls.COLORS['error']};
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['xs']} {cls.SPACING['sm']};
                font-weight: 600;
            }}
            
            QLabel#status_warning {{
                background: rgba(245, 158, 11, 0.1);
                color: {cls.COLORS['warning']};
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['xs']} {cls.SPACING['sm']};
                font-weight: 600;
            }}
            
            /* Progress Bar */
            QProgressBar {{
                background: {cls.COLORS['gray_200']};
                border: none;
                border-radius: {cls.RADIUS['sm']};
                text-align: center;
                height: 8px;
            }}
            
            QProgressBar::chunk {{
                background: {cls.COLORS['gradient_primary']};
                border-radius: {cls.RADIUS['sm']};
            }}
            
            /* Checkbox */
            QCheckBox {{
                color: {cls.COLORS['gray_700']};
                font-size: {cls.FONTS['sm']};
                font-family: {cls.FONTS['primary']};
                spacing: {cls.SPACING['sm']};
            }}
            
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: {cls.RADIUS['sm']};
                border: 2px solid {cls.COLORS['gray_300']};
                background: {cls.COLORS['white']};
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {cls.COLORS['primary']};
            }}
            
            QCheckBox::indicator:checked {{
                background: {cls.COLORS['primary']};
                border-color: {cls.COLORS['primary']};
                image: url(checkmark.png);
            }}
            
            /* Radio Button */
            QRadioButton {{
                color: {cls.COLORS['gray_700']};
                font-size: {cls.FONTS['sm']};
                font-family: {cls.FONTS['primary']};
                spacing: {cls.SPACING['sm']};
            }}
            
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {cls.COLORS['gray_300']};
                background: {cls.COLORS['white']};
            }}
            
            QRadioButton::indicator:hover {{
                border-color: {cls.COLORS['primary']};
            }}
            
            QRadioButton::indicator:checked {{
                background: {cls.COLORS['primary']};
                border-color: {cls.COLORS['primary']};
            }}
            
            /* Separator Lines */
            QFrame[frameShape="4"] {{
                color: {cls.COLORS['gray_200']};
                background-color: {cls.COLORS['gray_200']};
                height: 1px;
                border: none;
                margin: {cls.SPACING['md']} 0;
            }}
            
            /* Tooltips */
            QToolTip {{
                background: {cls.COLORS['gray_800']};
                color: {cls.COLORS['white']};
                border: none;
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['sm']} {cls.SPACING['md']};
                font-size: {cls.FONTS['xs']};
                font-family: {cls.FONTS['primary']};
            }}
        """
