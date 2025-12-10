import unittest
from unittest.mock import Mock, patch, MagicMock
from notifications import NotificationManager, NotificationCategory, NotificationChannel
from User import User
from notificationSettings import NotificationSettings

class TestNotificationManager(unittest.TestCase):
    
    def setUp(self):
        self.user_id = "test_user_123"
        self.db_config = {
            'host': 'localhost',
            'user': 'test',
            'password': 'test',
            'database': 'test_db'
        }
    
    @patch('notifications.mysql.connector.connect')
    def test_load_preferences_with_no_db_data(self, mock_connect):
        """Test loading preferences when no user data exists in database"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        manager = NotificationManager(self.user_id, self.db_config)
        
        # Verify default preferences are loaded
        self.assertIn(NotificationCategory.SECURITY_ALERTS, manager.preferences)
        self.assertIn(NotificationCategory.TRANSACTION_ALERTS, manager.preferences)
        self.assertIn(NotificationCategory.MARKETING, manager.preferences)
        self.assertIn(NotificationCategory.STATEMENTS, manager.preferences)
        
        # Verify security alerts are immutable and always enabled
        security_prefs = manager.preferences[NotificationCategory.SECURITY_ALERTS]
        self.assertTrue(security_prefs.immutable)
        self.assertTrue(all(security_prefs.channels.values()))  # All channels enabled
    
    @patch('notifications.mysql.connector.connect')
    def test_update_channel_preference_success(self, mock_connect):
        """Test updating a single channel preference"""
        # Mock database
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        manager = NotificationManager(self.user_id, self.db_config)
        
        # Disable email for marketing
        success = manager.update_channel_preference(
            NotificationCategory.MARKETING,
            NotificationChannel.EMAIL,
            False
        )
        
        self.assertTrue(success)
        self.assertFalse(
            manager.preferences[NotificationCategory.MARKETING]
            .channels[NotificationChannel.EMAIL]
        )
    
    def test_update_security_alerts_immutable(self):
        """Test that security alerts cannot be fully disabled"""
        manager = NotificationManager(self.user_id, None)  # Use default prefs
        
        # Try to disable all channels one by one
        security_prefs = manager.preferences[NotificationCategory.SECURITY_ALERTS]
        
        # Disable PUSH and EMAIL
        manager.update_channel_preference(
            NotificationCategory.SECURITY_ALERTS,
            NotificationChannel.PUSH,
            False
        )
        manager.update_channel_preference(
            NotificationCategory.SECURITY_ALERTS,
            NotificationChannel.EMAIL,
            False
        )
        
        # Try to disable the last channel (SMS) - should fail
        success = manager.update_channel_preference(
            NotificationCategory.SECURITY_ALERTS,
            NotificationChannel.SMS,
            False
        )
        
        self.assertFalse(success)
        self.assertTrue(
            manager.preferences[NotificationCategory.SECURITY_ALERTS]
            .channels[NotificationChannel.SMS]
        )
    
    def test_update_category_channels(self):
        """Test updating all channels for a category at once"""
        manager = NotificationManager(self.user_id, None)
        
        # Update transaction alerts to only use SMS
        new_channels = {
            NotificationChannel.PUSH: False,
            NotificationChannel.EMAIL: False,
            NotificationChannel.SMS: True
        }
        
        success = manager.update_category_channels(
            NotificationCategory.TRANSACTION_ALERTS,
            new_channels
        )
        
        self.assertTrue(success)
        self.assertEqual(
            manager.preferences[NotificationCategory.TRANSACTION_ALERTS].channels,
            new_channels
        )
    
    def test_update_category_channels_security_all_disabled_fails(self):
        """Test that disabling all channels for security alerts fails"""
        manager = NotificationManager(self.user_id, None)
        
        # Try to disable all channels for security alerts
        all_disabled = {
            NotificationChannel.PUSH: False,
            NotificationChannel.EMAIL: False,
            NotificationChannel.SMS: False
        }
        
        success = manager.update_category_channels(
            NotificationCategory.SECURITY_ALERTS,
            all_disabled
        )
        
        self.assertFalse(success)
        # Verify original preferences unchanged
        self.assertTrue(all(
            manager.preferences[NotificationCategory.SECURITY_ALERTS]
            .channels.values()
        ))
    
    def test_is_category_enabled(self):
        """Test checking if a category has any enabled channels"""
        manager = NotificationManager(self.user_id, None)
        
        # Marketing has only EMAIL enabled by default
        self.assertTrue(manager.is_category_enabled(NotificationCategory.MARKETING))
        
        # Disable all marketing channels
        manager.update_category_channels(
            NotificationCategory.MARKETING,
            {ch: False for ch in NotificationChannel}
        )
        
        self.assertFalse(manager.is_category_enabled(NotificationCategory.MARKETING))
    
    def test_get_enabled_channels(self):
        """Test getting list of enabled channels for a category"""
        manager = NotificationManager(self.user_id, None)
        
        # Transaction alerts default: PUSH=True, EMAIL=True, SMS=False
        enabled_channels = manager.get_enabled_channels(
            NotificationCategory.TRANSACTION_ALERTS
        )
        
        self.assertIn(NotificationChannel.PUSH, enabled_channels)
        self.assertIn(NotificationChannel.EMAIL, enabled_channels)
        self.assertNotIn(NotificationChannel.SMS, enabled_channels)
        self.assertEqual(len(enabled_channels), 2)
    
    @patch('notifications.mysql.connector.connect')
    def test_send_notification_only_to_enabled_channels(self, mock_connect):
        """Test that notifications are only sent to enabled channels"""
        # Mock database
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        manager = NotificationManager(self.user_id, self.db_config)
        
        # Disable PUSH for statements
        manager.update_channel_preference(
            NotificationCategory.STATEMENTS,
            NotificationChannel.PUSH,
            False
        )
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            success = manager.send_notification(
                NotificationCategory.STATEMENTS,
                "Your statement is ready",
                "Monthly Statement"
            )
            
            self.assertTrue(success)
            
            # Verify only EMAIL and SMS notifications were printed (SMS is disabled by default)
            # Should only see EMAIL notification
            push_calls = [call for call in mock_print.call_args_list 
                         if 'PUSH' in str(call)]
            email_calls = [call for call in mock_print.call_args_list 
                          if 'EMAIL' in str(call)]
            
            self.assertEqual(len(push_calls), 0)  # PUSH disabled
            self.assertEqual(len(email_calls), 1)  # EMAIL enabled
    
    def test_reset_to_defaults(self):
        """Test resetting all preferences to defaults"""
        manager = NotificationManager(self.user_id, None)
        
        # Modify some preferences
        manager.update_channel_preference(
            NotificationCategory.MARKETING,
            NotificationChannel.PUSH,
            True
        )
        manager.update_channel_preference(
            NotificationCategory.TRANSACTION_ALERTS,
            NotificationChannel.SMS,
            True
        )
        
        # Reset to defaults
        with patch.object(manager, 'save_preferences', return_value=True):
            success = manager.reset_to_defaults()
            self.assertTrue(success)
        
        # Verify back to defaults
        self.assertFalse(
            manager.preferences[NotificationCategory.MARKETING]
            .channels[NotificationChannel.PUSH]
        )
        self.assertFalse(
            manager.preferences[NotificationCategory.TRANSACTION_ALERTS]
            .channels[NotificationChannel.SMS]
        )
    
    def test_get_preferences_summary(self):
        """Test getting a summary of all preferences"""
        manager = NotificationManager(self.user_id, None)
        
        summary = manager.get_preferences_summary()
        
        # Verify structure
        self.assertIn('security_alerts', summary)
        self.assertIn('transaction_alerts', summary)
        self.assertIn('marketing', summary)
        self.assertIn('statements', summary)
        
        # Verify security alerts are immutable
        self.assertTrue(summary['security_alerts']['immutable'])
        self.assertTrue(summary['security_alerts']['enabled'])
        
        # Verify all channels are present
        self.assertIn('push', summary['security_alerts']['channels'])
        self.assertIn('email', summary['security_alerts']['channels'])
        self.assertIn('sms', summary['security_alerts']['channels'])

class TestNotificationSettings(unittest.TestCase):
    
    def setUp(self):
        self.user_id = "test_user_123"
        self.db_config = {
            'host': 'localhost',
            'user': 'test',
            'password': 'test',
            'database': 'test_db'
        }
    
    @patch('notificationSettings.mysql.connector.connect')
    def test_toggle_channel_success(self, mock_connect):
        """Test toggling a channel on/off"""
        settings = NotificationSettings(self.user_id, self.db_config)
        
        # Mock the notification manager
        mock_manager = Mock()
        mock_manager.update_channel_preference.return_value = True
        mock_manager.get_category_preferences.return_value = Mock(
            channels={NotificationChannel.EMAIL: False}
        )
        settings.notification_manager = mock_manager
        
        success = settings.toggle_channel('marketing', 'email')
        
        self.assertTrue(success)
        mock_manager.update_channel_preference.assert_called_once()
    
    def test_toggle_channel_invalid_category(self):
        """Test toggling channel with invalid category name"""
        settings = NotificationSettings(self.user_id, self.db_config)
        
        success = settings.toggle_channel('invalid_category', 'email')
        
        self.assertFalse(success)
    
    def test_update_category_settings(self):
        """Test updating multiple channels for a category"""
        settings = NotificationSettings(self.user_id, self.db_config)
        
        # Mock the notification manager
        mock_manager = Mock()
        mock_manager.update_category_channels.return_value = True
        mock_manager.get_category_preferences.return_value = Mock(
            channels={
                NotificationChannel.PUSH: False,
                NotificationChannel.EMAIL: False,
                NotificationChannel.SMS: False
            }
        )
        settings.notification_manager = mock_manager
        
        success = settings.update_category_settings(
            'transaction_alerts',
            push=True,
            email=False,
            sms=True
        )
        
        self.assertTrue(success)
        mock_manager.update_category_channels.assert_called_once()
    
    def test_disable_all_channels_security_fails(self):
        """Test that disabling all channels for security alerts fails"""
        settings = NotificationSettings(self.user_id, self.db_config)
        
        success = settings.disable_all_channels('security_alerts')
        
        self.assertFalse(success)
    
    def test_enable_all_channels(self):
        """Test enabling all channels for a category"""
        settings = NotificationSettings(self.user_id, self.db_config)
        
        # Mock the notification manager
        mock_manager = Mock()
        mock_manager.update_category_channels.return_value = True
        settings.notification_manager = mock_manager
        
        success = settings.enable_all_channels('marketing')
        
        self.assertTrue(success)
        mock_manager.update_category_channels.assert_called_once()
    
    def test_send_test_notification(self):
        """Test sending a test notification"""
        settings = NotificationSettings(self.user_id, self.db_config)
        
        # Mock the notification manager
        mock_manager = Mock()
        mock_manager.send_notification.return_value = True
        settings.notification_manager = mock_manager
        
        success = settings.send_test_notification('security_alerts', 'Test message')
        
        self.assertTrue(success)
        mock_manager.send_notification.assert_called_once_with(
            NotificationCategory.SECURITY_ALERTS,
            'Test message',
            'Test Notification'
        )

class TestUserNotificationIntegration(unittest.TestCase):
    
    def setUp(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'test',
            'password': 'test',
            'database': 'test_db'
        }
    
    def test_user_initialization_with_notification_settings(self):
        """Test that User object initializes with NotificationSettings"""
        user = User(
            email="test@example.com",
            passwordHash="hash",
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated="2024-01-01",
            dbConfig=self.db_config
        )
        
        self.assertIsNotNone(user.notificationSettings)
        self.assertIsInstance(user.notificationSettings, NotificationSettings)
    
    def test_update_notification_preferences_via_user(self):
        """Test updating notification preferences through User class"""
        user = User(
            email="test@example.com",
            passwordHash="hash",
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated="2024-01-01",
            dbConfig=self.db_config
        )
        
        # Mock the notification settings
        mock_settings = Mock()
        mock_settings.update_category_settings.return_value = True
        user.notificationSettings = mock_settings
        
        success, message = user.update_notification_preferences(
            'marketing',
            {'push': True, 'email': False, 'sms': True}
        )
        
        self.assertTrue(success)
        mock_settings.update_category_settings.assert_called_once_with(
            'marketing',
            push=True,
            email=False,
            sms=True
        )
    
    def test_get_notification_summary(self):
        """Test getting notification summary from User"""
        user = User(
            email="test@example.com",
            passwordHash="hash",
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated="2024-01-01",
            dbConfig=self.db_config
        )
        
        # Mock the notification settings
        mock_settings = Mock()
        mock_settings.get_settings_summary.return_value = {
            'security_alerts': {'enabled': True, 'channels': {'push': True}}
        }
        user.notificationSettings = mock_settings
        
        summary = user.get_notification_summary()
        
        self.assertIn('security_alerts', summary)
        mock_settings.get_settings_summary.assert_called_once()

class TestNotificationEdgeCases(unittest.TestCase):
    
    def test_empty_database_configuration(self):
        """Test behavior when database configuration is None"""
        manager = NotificationManager("test_user", None)
        
        # Should initialize with default preferences
        self.assertIn(NotificationCategory.SECURITY_ALERTS, manager.preferences)
        
        # Attempt to save should handle gracefully
        success = manager.save_preferences()
        # Depending on implementation, this might return False or handle differently
        # We're mainly checking it doesn't crash
    
    def test_invalid_category_enum_values(self):
        """Test handling of invalid category values"""
        manager = NotificationManager("test_user", None)
        
        # This should not crash
        pref = manager.get_category_preferences("invalid_category")
        self.assertIsNone(pref)
        
        enabled = manager.is_category_enabled("invalid_category")
        self.assertFalse(enabled)
    
    def test_concurrent_preference_updates(self):
        """Test scenario with rapid, consecutive preference updates"""
        manager = NotificationManager("test_user", None)
        
        # Rapid toggling of a preference
        for _ in range(5):
            manager.update_channel_preference(
                NotificationCategory.TRANSACTION_ALERTS,
                NotificationChannel.SMS,
                True
            )
            manager.update_channel_preference(
                NotificationCategory.TRANSACTION_ALERTS,
                NotificationChannel.SMS,
                False
            )
        
        # Final state should be False
        self.assertFalse(
            manager.preferences[NotificationCategory.TRANSACTION_ALERTS]
            .channels[NotificationChannel.SMS]
        )
    
    def test_partial_channel_updates(self):
        """Test updating only some channels in a category"""
        manager = NotificationManager("test_user", None)
        
        # Update only SMS, leave others as default
        new_channels = {
            NotificationChannel.SMS: True  # Only specify SMS
        }
        
        # This method requires all channels
        # So we need to use update_channel_preference instead
        success = manager.update_channel_preference(
            NotificationCategory.TRANSACTION_ALERTS,
            NotificationChannel.SMS,
            True
        )
        
        self.assertTrue(success)
        self.assertTrue(
            manager.preferences[NotificationCategory.TRANSACTION_ALERTS]
            .channels[NotificationChannel.SMS]
        )
        # Other channels should remain at defaults
        self.assertTrue(
            manager.preferences[NotificationCategory.TRANSACTION_ALERTS]
            .channels[NotificationChannel.PUSH]
        )
    
    def test_notification_with_empty_message(self):
        """Test sending notification with empty or None message"""
        manager = NotificationManager("test_user", None)
        
        # Should handle gracefully
        success = manager.send_notification(
            NotificationCategory.SECURITY_ALERTS,
            ""  # Empty message
        )
    
    def test_get_notifications_with_various_filters(self):
        """Test retrieving notifications with different filter combinations"""
        manager = NotificationManager("test_user", None)
        
        # Test with different limit values
        notifications = manager.get_user_notifications(limit=0)
        notifications = manager.get_user_notifications(limit=1000)
        
        # Test unread only flag
        notifications = manager.get_user_notifications(unreadOnly=True)
        
        # These should not crash
        self.assertIsInstance(notifications, list)

class TestAcceptanceCriteria(unittest.TestCase):
    """Tests specifically for the acceptance criteria"""
    
    def test_security_alerts_always_on(self):
        """AC: Security alerts remain always on and cannot be disabled"""
        manager = NotificationManager("test_user", None)
        
        # Verify default state
        security_prefs = manager.preferences[NotificationCategory.SECURITY_ALERTS]
        self.assertTrue(security_prefs.immutable)
        self.assertTrue(all(security_prefs.channels.values()))
        
        # Try to disable category
        success = manager.update_category_channels(
            NotificationCategory.SECURITY_ALERTS,
            {ch: False for ch in NotificationChannel}
        )
        self.assertFalse(success)
        
        # Verify still enabled
        self.assertTrue(manager.is_category_enabled(NotificationCategory.SECURITY_ALERTS))
    
    def test_channel_preferences_per_category(self):
        """AC: System saves channel preferences (push, email, SMS) per category"""
        manager = NotificationManager("test_user", None)
        
        # Set different preferences for each category
        test_cases = [
            (NotificationCategory.TRANSACTION_ALERTS, 
             {NotificationChannel.PUSH: True, 
              NotificationChannel.EMAIL: False, 
              NotificationChannel.SMS: True}),
            (NotificationCategory.MARKETING,
             {NotificationChannel.PUSH: False,
              NotificationChannel.EMAIL: True,
              NotificationChannel.SMS: False}),
            (NotificationCategory.STATEMENTS,
             {NotificationChannel.PUSH: False,
              NotificationChannel.EMAIL: False,
              NotificationChannel.SMS: True})
        ]
        
        for category, channels in test_cases:
            success = manager.update_category_channels(category, channels)
            self.assertTrue(success)
            
            # Verify saved correctly
            saved_prefs = manager.get_category_preferences(category)
            self.assertEqual(saved_prefs.channels, channels)
    
    def test_toggle_categories_independently(self):
        """AC: When I toggle categories, system saves preferences independently"""
        manager = NotificationManager("test_user", None)
        
        # Toggle marketing without affecting transaction alerts
        original_transaction_prefs = manager.preferences[
            NotificationCategory.TRANSACTION_ALERTS
        ].channels.copy()
        
        # Disable marketing entirely
        manager.update_category_channels(
            NotificationCategory.MARKETING,
            {ch: False for ch in NotificationChannel}
        )
        
        # Transaction alerts should remain unchanged
        current_transaction_prefs = manager.preferences[
            NotificationCategory.TRANSACTION_ALERTS
        ].channels
        
        self.assertEqual(original_transaction_prefs, current_transaction_prefs)
        
        # Marketing should be disabled
        self.assertFalse(manager.is_category_enabled(NotificationCategory.MARKETING))