import pika

class EmailSubscriber:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange='notification_service', exchange_type='fanout')

        result = self.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        self.channel.queue_bind(exchange='notification_service', queue=queue_name)

        self.channel.basic_consume(queue=queue_name, on_message_callback=self.send_email, auto_ack=True)


    def start_consuming(self):
        try:
            print('consumer started...')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print('consumer stopped...')
            exit(0)

  
    def send_email(self, ch, method, properties, email):
        print(f'sending email to {email}...')

    
if __name__ == '__main__':
    subscriber = EmailSubscriber()
    subscriber.start_consuming()
