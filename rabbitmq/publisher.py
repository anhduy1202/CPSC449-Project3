import pika

class Publisher:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange='notification_service', exchange_type='fanout')

    def publish(self, message):
        self.channel.basic_publish(
            exchange='notification_service', 
            routing_key='', 
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent
            )
        )

    def __del__(self):
        self.connection.close()

if __name__ == '__main__':
    publisher = Publisher()
    publisher.publish('{"student_id": "0001", "class_id": "0001", "email": "user1@example.com", "webhook_url": "https://example1.com/"}')
