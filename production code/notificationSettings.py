from typing import Dict, List
from notifications import NotificationManager, NotificationCategory, NotificationChannel
import mysql.connector

class NotificationSettings:
    def __init__(self, userID: str, dbConfig: dict):
        self.userID = userID
        if dbConfig is None:
            dbConfig = {
                'host': "localhost",
                'user': "root",
                'password': "Melt1129",
                'database': "banking_db"
            }
        self.dbConfig = dbConfig
        self.notification_manager = NotificationManager(userID, dbConfig)

    def get_db_connection(self):
        try:
            return mysql.connector.connect(**self.dbConfig)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise
    
    def display_settings(self):
        print(f"\n=== Notification Settings for User {self.userID} ===")
        preferences = self.notification_manager.get_all_preferences()
        
        for category, preference in preferences.items():
            categoryName = category.value.replace('_', ' ').title()
            enabledStatus = "ENABLED" if self.notification_manager.is_category_enabled(category) else "DISABLED"
            immutableFlag = " (Always On)" if preference.immutable else ""
            
            print(f"\n{categoryName}{immutableFlag}: {enabledStatus}")
            
            for channel, is_enabled in preference.channels.items():
                channelName = channel.value.upper()
                status = "✓" if is_enabled else "✗"
                print(f"  - {channelName}: {status}")
    
    def toggle_channel(self, categoryName: str, channelName: str, enabled: bool = None) -> bool:
        try:
            category = NotificationCategory(categoryName)
            channel = NotificationChannel(channelName)
        except ValueError:
            print(f"Invalid category or channel name")
            return False
        
        if enabled is None:
            currentPref = self.notification_manager.get_category_preferences(category)
            if currentPref:
                enabled = not currentPref.channels.get(channel, False)
        
        success = self.notification_manager.update_channel_preference(category, channel, enabled)
        
        if success:
            action = "enabled" if enabled else "disabled"
            print(f"{channelName.upper()} notifications {action} for {categoryName.replace('_', ' ')}")
        else:
            print(f"Failed to update {categoryName}. Security alerts must have at least one channel enabled.")
        
        return success
    
    def update_category_settings(self, categoryName: str, 
                               push: bool = None, email: bool = None, sms: bool = None) -> bool:
        try:
            category = NotificationCategory(categoryName)
        except ValueError:
            print(f"Invalid category name: {categoryName}")
            return False
        
        currentPrefs = self.notification_manager.get_category_preferences(category)
        if not currentPrefs:
            return False
        
        newChannels = currentPrefs.channels.copy()
        
        if push is not None:
            newChannels[NotificationChannel.PUSH] = push
        if email is not None:
            newChannels[NotificationChannel.EMAIL] = email
        if sms is not None:
            newChannels[NotificationChannel.SMS] = sms
        
        success = self.notification_manager.update_category_channels(category, newChannels)
        
        if success:
            print(f"Updated {categoryName.replace('_', ' ')} notification settings")
        else:
            print(f"Failed to update {categoryName}. Security alerts must have at least one channel enabled.")
        
        return success
    
    def enable_all_channels(self, categoryName: str) -> bool:
        try:
            category = NotificationCategory(categoryName)
        except ValueError:
            return False
        
        channels = {
            NotificationChannel.PUSH: True,
            NotificationChannel.EMAIL: True,
            NotificationChannel.SMS: True
        }
        
        return self.notification_manager.update_category_channels(category, channels)
    
    def disable_all_channels(self, categoryName: str) -> bool:
        try:
            category = NotificationCategory(categoryName)
        except ValueError:
            return False
        
        if category == NotificationCategory.SECURITY_ALERTS:
            print("Cannot disable all channels for security alerts")
            return False
        
        channels = {
            NotificationChannel.PUSH: False,
            NotificationChannel.EMAIL: False,
            NotificationChannel.SMS: False
        }
        
        return self.notification_manager.update_category_channels(category, channels)
    
    def send_test_notification(self, categoryName: str, message: str = "Test notification") -> bool:
        try:
            category = NotificationCategory(categoryName)
        except ValueError:
            return False
        
        return self.notification_manager.send_notification(
            category, 
            message, 
            title="Test Notification"
        )
    
    def get_settings_summary(self) -> Dict:
        try:
            connection = self.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT category, channel, enabled, immutable FROM bankNotificationSettings WHERE userID = %s",
                (self.userID,)
            )
            settings = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            summary = {}
            for setting in settings:
                category = setting['category']
                if category not in summary:
                    summary[category] = {
                        'enabled': False,
                        'channels': {},
                        'immutable': bool(setting['immutable'])
                    }
                
                summary[category]['channels'][setting['channel']] = bool(setting['enabled'])
            
            for category, data in summary.items():
                data['enabled'] = any(data['channels'].values())
            
            return summary
            
        except Exception as e:
            print(f"Error getting notification settings summary: {e}")
            return {}
    
    def reset_all_settings(self) -> bool:
        return self.notification_manager.reset_to_defaults()
    
    def get_notifications(self, limit: int = 50, unreadOnly: bool = False) -> List[dict]:
        return self.notification_manager.get_user_notifications(limit, unreadOnly)
    
    def mark_as_read(self, notificationID: int) -> bool:
        return self.notification_manager.mark_notification_as_read(notificationID)
    
    def mark_all_as_read(self) -> bool:
        return self.notification_manager.mark_all_notifications_as_read()
    
    def update_settings_from_api(self, category_updates: Dict[str, Dict[str, bool]]) -> bool:
        """Update notification settings from API data"""
        try:
            connection = self.get_db_connection()
            cursor = connection.cursor()
            
            for category_name, channels in category_updates.items():
                for channel_name, enabled in channels.items():
                    # Update or insert setting
                    cursor.execute("""
                        INSERT INTO bankNotificationSettings (userID, category, channel, enabled) 
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE enabled = %s
                    """, (self.userID, category_name, channel_name, enabled, enabled))
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
            
        except Exception as e:
            print(f"Error updating notification settings: {e}")
            if 'connection' in locals():
                connection.rollback()
            return False