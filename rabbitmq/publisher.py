import pika

class Publisher:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange='notification_service', exchange_type='fanout')

    def publish(self, message):
        self.channel.basic_publish(exchange='notification_service', routing_key='', body=message)

    def __del__(self):
        self.connection.close()
