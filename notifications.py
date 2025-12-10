from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
import mysql.connector
from datetime import datetime

class NotificationChannel(Enum):
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"

class NotificationCategory(Enum):
    SECURITY_ALERTS = "security_alerts"
    TRANSACTION_ALERTS = "transaction_alerts"
    MARKETING = "marketing"
    STATEMENTS = "statements"

@dataclass
class NotificationPreferences:
    category: NotificationCategory
    channels: Dict[NotificationChannel, bool]
    immutable: bool = False

class NotificationManager:
    def __init__(self, userID: str, dbConfig: dict):
        self.userID = userID
        self.dbConfig = dbConfig
        self.preferences = self.load_preferences()

    def get_db_connection(self):
        try:
            if self.dbConfig is None:
                raise ValueError("Database configuration is None")
            return mysql.connector.connect(**self.dbConfig)
        except Exception as e:
            print(f"Error creating database connection: {e}")
            raise
    
    def load_preferences(self):
        try:
            if self.dbConfig is None:
                print("Database configuration is None, using default preferences")
                return self.initialize_default_preferences()
            
            connection = self.get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute("""
            SELECT category, channel, enabled, immutable FROM bankNotificationSettings WHERE userID = %s""", (self.userID,))
            dbPreferences = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            if dbPreferences:
                return self.preferences_from_db(dbPreferences)
            else:
                defaultPrefs = self.initialize_default_preferences()
                self.save_preferences_to_db(defaultPrefs)
                return defaultPrefs
        except Exception as e:
            print(f"Error loading notification preferences: {str(e)}")
            return self.initialize_default_preferences()
        
    def preferences_from_db(self, dbRows: List[dict]) -> Dict[NotificationCategory, NotificationPreferences]:
        preferences = {}

        categoryData = {}
        for row in dbRows:
            category = NotificationCategory(row['category'])
            if category not in categoryData:
                categoryData[category] = {
                    'channels': {},
                    'immutable': bool(row['immutable'])
                }
            channel = NotificationChannel(row['channel'])
            categoryData[category]['channels'][channel] = bool(row['enabled'])

        for category, data in categoryData.items():
            preferences[category] = NotificationPreferences(
                category=category,
                channels=data['channels'],
                immutable=data['immutable']
            )
        return preferences
    
    def save_preferences_to_db(self, preferences: Dict[NotificationCategory, NotificationPreferences]):
        try:
            connection = self.get_db_connection()
            cursor = connection.cursor()

            cursor.execute("DELETE FROM bankNotificationSettings WHERE userID = %s", (self.userID,))

            for preference in preferences.values():
                for channel, enabled, in preference.channels.items():
                    cursor.execute("INSERT INTO bankNotificationSettings (userID, category, channel, enabled, immutable) VALUES (%s, %s, %s, %s, %s)",
                                   (self.userID, preference.category.value, channel.value, enabled, preference.immutable))
            
            connection.commit()
            cursor.close()
            connection.close()

        except Exception as e:
            print(f"Error saving preferences to database: {e}")
            if 'connection' in locals():
                connection.rollback()

    def initialize_default_preferences(self) -> Dict[NotificationCategory, NotificationPreferences]:
        return {
            NotificationCategory.SECURITY_ALERTS: NotificationPreferences(
                category=NotificationCategory.SECURITY_ALERTS,
                channels={
                    NotificationChannel.PUSH: True,
                    NotificationChannel.EMAIL: True,
                    NotificationChannel.SMS: True
                },
                immutable=True
            ),
            NotificationCategory.TRANSACTION_ALERTS: NotificationPreferences(
                category=NotificationCategory.TRANSACTION_ALERTS,
                channels={
                    NotificationChannel.PUSH: True,
                    NotificationChannel.EMAIL: True,
                    NotificationChannel.SMS: False
                }
            ),
            NotificationCategory.MARKETING: NotificationPreferences(
                category=NotificationCategory.MARKETING,
                channels={
                    NotificationChannel.PUSH: False,
                    NotificationChannel.EMAIL: True,
                    NotificationChannel.SMS: False
                }
            ),
            NotificationCategory.STATEMENTS: NotificationPreferences(
                category=NotificationCategory.STATEMENTS,
                channels={
                    NotificationChannel.PUSH: False,
                    NotificationChannel.EMAIL: True,
                    NotificationChannel.SMS: False
                }
            )
        }
    
    def update_channel_preference(self, category: NotificationCategory, channel: NotificationChannel, enabled: bool) -> bool:
        if category not in self.preferences:
            return False
        
        preference = self.preferences[category]
        
        if preference.immutable:
            currentEnabledChannels = [ch for ch, enabled in preference.channels.items() if enabled]
            if len(currentEnabledChannels) == 1 and currentEnabledChannels[0] == channel and not enabled:
                return False
        
        preference.channels[channel] = enabled
        return self.save_preferences()
    
    def update_category_channels(self, category: NotificationCategory, channels: Dict[NotificationChannel, bool]) -> bool:
        if category not in self.preferences:
            return False
        
        preference = self.preferences[category]
        
        if preference.immutable:
            if not any(channels.values()):
                return False
        
        preference.channels = channels.copy()
        return self.save_preferences()
    
    def get_category_preferences(self, category: NotificationCategory) -> Optional[NotificationPreferences]:
        return self.preferences.get(category)
    
    def get_all_preferences(self) -> Dict[NotificationCategory, NotificationPreferences]:
        return self.preferences.copy()
    
    def is_category_enabled(self, category: NotificationCategory) -> bool:
        if category not in self.preferences:
            return False
        return any(self.preferences[category].channels.values())
    
    def get_enabled_channels(self, category: NotificationCategory) -> List[NotificationChannel]:
        if category not in self.preferences:
            return []
        return [channel for channel, enabled in self.preferences[category].channels.items() if enabled]
    
    #Future Implementation: save to database
    def save_preferences(self) -> bool:
        try:
            self.save_preferences_to_db(self.preferences)
            print(f"Notification prefereneces saved for user {self.userID}")
            return True
        except Exception as e:
            print(f"Error saving notification preferences: {str(e)}")
            return False

    def send_notification(self, category: NotificationCategory, message: str, 
                        title: Optional[str] = None) -> bool:
        if not self.is_category_enabled(category):
            print(f"Category {category.value} is disabled, notification not sent: {message}")
            return False
        
        enabledChannels = self.get_enabled_channels(category)
        if not enabledChannels:
            return False
        
        success = True
        for channel in enabledChannels:
            if not self.store_notifications_in_db(category, channel, message, title):
                success = False
            self.send_via_channel(channel, category, message, title)
        return success
        
    def store_notifications_in_db(self, category: NotificationCategory, channel: NotificationChannel, message: str, title: Optional[str] = None) -> bool:
        try:
            connection = self.get_db_connection()
            cursor = connection.cursor()

            cursor.execute("INSERT INTO bankNotifications (userID, category, channel, title, message) VALUES (%s, %s, %s, %s, %s)", (self.userID, category.value, channel.value, title, message))
    
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error storing notification in database: {e}")
            if 'connection' in locals():
                connection.rollback()
            return False
        
    def get_user_notifications(self, limit: int = 50, unreadOnly: bool = False) -> List[dict]:
        try:
            connection = self.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = "SELECT * FROM bankNotifications WHERE userID = %s"
            params = [self.userID]
            
            if unreadOnly:
                query += " AND is_read = 0"
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            notifications = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            for notification in notifications:
                if notification['created_at']:
                    notification['created_at'] = notification['created_at'].isoformat()
            
            return notifications
            
        except Exception as e:
            print(f"Error fetching notifications from database: {e}")
            return []
    
    def mark_notification_as_read(self, notificationID: int) -> bool:
        try:
            connection = self.get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute(
                "UPDATE bankNotifications SET is_read = 1 WHERE idbankNotifications = %s AND userID = %s",
                (notificationID, self.userID)
            )
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
            
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            if 'connection' in locals():
                connection.rollback()
            return False
    
    def mark_all_notifications_as_read(self) -> bool:
        try:
            connection = self.get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute(
                "UPDATE bankNotifications SET is_read = 1 WHERE userID = %s",
                (self.userID,)
            )
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
            
        except Exception as e:
            print(f"Error marking all notifications as read: {e}")
            if 'connection' in locals():
                connection.rollback()
            return False
    
    def send_via_channel(self, channel: NotificationChannel, category: NotificationCategory,
                         message: str, title: Optional[str] = None):
        channelName = channel.value.upper()
        categoryName = category.value.replace('_', ' ').title()
        
        if title:
            print(f"[{channelName}] {categoryName}: {title} - {message}")
        else:
            print(f"[{channelName}] {categoryName}: {message}")
    
    def reset_to_defaults(self) -> bool:
        self.preferences = self.initialize_default_preferences()
        return self.save_preferences()
        
    def get_preferences_summary(self) -> Dict:
        summary = {}
        for category, preference in self.preferences.items():
            summary[category.value] = {
                'enabled': self.is_category_enabled(category),
                'channels': {
                    channel.value: enabled 
                    for channel, enabled in preference.channels.items()
                },
                'immutable': preference.immutable
            }
        return summary