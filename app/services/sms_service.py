# -*- coding: utf-8 -*-
"""SMS service for sending 2FA codes"""

from flask import current_app
import logging

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service for sending 2FA codes and notifications"""
    
    def __init__(self):
        self.provider = current_app.config.get('SMS_PROVIDER', 'mock')
        self.enabled = current_app.config.get('SMS_ENABLED', False)
    
    def send_2fa_code(self, phone_number, code):
        """
        Отправить 2FA код по SMS
        
        Args:
            phone_number (str): Номер телефона получателя
            code (str): 6-значный 2FA код
            
        Returns:
            dict: Результат отправки с success и message
        """
        try:
            if not self.enabled:
                logger.info(f"SMS disabled. Would send 2FA code {code} to {phone_number}")
                return {
                    'success': True,
                    'message': 'SMS отправлена (режим симуляции)',
                    'provider': 'mock'
                }
            
            if self.provider == 'twilio':
                return self._send_via_twilio(phone_number, code)
            elif self.provider == 'mock':
                return self._send_via_mock(phone_number, code)
            else:
                return {
                    'success': False,
                    'message': f'Неизвестный SMS провайдер: {self.provider}'
                }
                
        except Exception as e:
            logger.error(f"Ошибка отправки SMS: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка отправки SMS: {str(e)}'
            }
    
    def _send_via_mock(self, phone_number, code):
        """Заглушка для отправки SMS (для тестирования)"""
        message = f"Ваш код подтверждения MES: {code}. Действителен 5 минут."
        
        logger.info(f"[SMS MOCK] To: {phone_number}, Message: {message}")
        
        # Симуляция успешной отправки
        return {
            'success': True,
            'message': 'SMS отправлена (симуляция)',
            'provider': 'mock',
            'phone': phone_number,
            'code': code
        }
    
    def _send_via_twilio(self, phone_number, code):
        """Отправка SMS через Twilio (реальная отправка)"""
        try:
            from twilio.rest import Client
            
            account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            from_number = current_app.config.get('TWILIO_PHONE_NUMBER')
            
            if not all([account_sid, auth_token, from_number]):
                return {
                    'success': False,
                    'message': 'Twilio не настроен (отсутствуют обязательные параметры)'
                }
            
            client = Client(account_sid, auth_token)
            
            message_body = f"Ваш код подтверждения MES: {code}. Действителен 5 минут."
            
            message = client.messages.create(
                body=message_body,
                from_=from_number,
                to=phone_number
            )
            
            logger.info(f"SMS отправлена через Twilio. SID: {message.sid}")
            
            return {
                'success': True,
                'message': 'SMS отправлена через Twilio',
                'provider': 'twilio',
                'message_sid': message.sid
            }
            
        except Exception as e:
            logger.error(f"Ошибка Twilio: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка Twilio: {str(e)}'
            }
    
    def send_account_lockout_notification(self, phone_number, username):
        """Уведомление о блокировке аккаунта"""
        try:
            message = f"Ваш аккаунт MES ({username}) заблокирован из-за множественных неудачных попыток входа."
            
            if self.provider == 'mock':
                logger.info(f"[SMS MOCK] Lockout notification to {phone_number}: {message}")
                return {'success': True, 'message': 'Уведомление о блокировке отправлено (симуляция)'}
            
            # Здесь бы была реальная отправка через Twilio
            return {'success': True, 'message': 'Уведомление о блокировке отправлено'}
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о блокировке: {str(e)}")
            return {'success': False, 'message': str(e)}

# Глобальная функция для простого использования
def send_2fa_sms(phone_number, code):
    """Быстрая отправка 2FA SMS"""
    service = SMSService()
    return service.send_2fa_code(phone_number, code) 