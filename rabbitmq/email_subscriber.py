import pika
import json
import smtplib
from email.mime.text import MIMEText
import sys

FROM = 'titan.online@fullerton.edu'
class EmailSubscriber:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange='notification_service', exchange_type='fanout')

        result = self.channel.queue_declare(queue='email', durable=True)
        queue_name = result.method.queue

        self.channel.queue_bind(exchange='notification_service', queue=queue_name)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=queue_name, on_message_callback=self.send_email)


    def start_consuming(self):
        try:
            print('consumer started...')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print('consumer stopped...')
            exit(0)

  
    def send_email(self, ch, method, properties, message):
        try:
            decoded = json.loads(message)

            if not decoded['email']: return

            server = smtplib.SMTP('localhost', port=8025)

            body = f'Dear student, \nYour status for course {decoded["class_id"]} has been updated to "enrolled"'
            email = MIMEText(body)
            email['Subject'] = 'Enrollment Status Update'
            email['From'] =  FROM
            email['To'] = decoded['email']

            print('sending email to ', decoded['email'])
            server.sendmail(FROM, [decoded['email']], email.as_string())

            ch.basic_ack(delivery_tag=method.delivery_tag)
            server.quit()
        except Exception as e:
            print(f'error while sending mail: {e}')

if __name__ == '__main__':
    subscriber = EmailSubscriber()
    subscriber.start_consuming()
